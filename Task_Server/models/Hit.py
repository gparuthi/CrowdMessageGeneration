from mongoengine import *
from common.dbclient import db
import datetime
from operator import attrgetter
import collections
import random
import pytz

def getMinSet(arr, key):
    values = [x[key] for x in arr]
    minVal  = min(values)
    all_mins_by_key = [v for i, v in enumerate(arr) if v[key] == minVal]
    return all_mins_by_key


class HitInstance(Document):
    date_modified = DateTimeField(default=datetime.datetime.now(pytz.utc))
    date_created = DateTimeField(default=datetime.datetime.now(pytz.utc))
    hit_id = StringField(required=True)
    loadedBy = IntField(min_value=0, max_value=100, default=0)
    submittedBy = IntField(min_value=0, max_value=100, default=0)
    loadedAndSubmitted = IntField(min_value=0, max_value=100, default=0)
    loadedByWorkers = DictField(default={})
    ignoredByWorkers = DictField(default={})
    submittedByWorkers = DictField(default={})
    
    def isLoaded(self, worker_id="default"):
        self.loadedBy += 1
        self.loadedAndSubmitted += 1
        self.loadedByWorkers[worker_id] = datetime.datetime.now(pytz.utc)
        self.save()
        
    def isUnLoaded(self, worker_id="default"):
        self.loadedBy -= 1
        self.loadedAndSubmitted -= 1
        self.updateAsIgnoredByWorker(worker_id)
        self.save()
    
    def isSubmitted(self, worker_id="default"):
        self.submittedBy += 1
        self.loadedAndSubmitted += 1
        self.submittedByWorkers[worker_id] = datetime.datetime.now(pytz.utc)
        del self.loadedByWorkers[worker_id]
        self.loadedBy -= 1
        self.save()

    def updateAsIgnoredByWorker(self, worker_id):
        if worker_id in self.loadedByWorkers:
            self.ignoredByWorkers[worker_id] = self.loadedByWorkers[worker_id]
            del self.loadedByWorkers[worker_id]

    def check_for_times(self):
        for worker_id in self.loadedByWorkers:
            loadtimeunaware = self.loadedByWorkers[worker_id]
            loadtime = pytz.utc.localize(loadtimeunaware)
            timedelta = datetime.datetime.now(pytz.utc) - loadtime
            seconds = timedelta.total_seconds() #+ 110 # There seems to be clock difference bw server and computer
            print self.hit_id, worker_id, seconds
            if seconds > 5*60 or seconds < -5*60:
                self.updateAsIgnoredByWorker(worker_id)
                print 'ignored by worker %s'%worker_id

        self.loadedBy = len(self.loadedByWorkers)
        self.loadedAndSubmitted = self.loadedBy+self.submittedBy
        self.save()

    # @property
    # def submittedBy(self):
    #     return len(self.submittedByWorkers)
    

    @classmethod
    def get_with_least_submits(cls, hitids):
    	hit_instances = HitInstance.objects(hit_id__in = hitids, submittedBy__lt = 5, loadedBy__lt = 6)

        s1 = getMinSet(hit_instances, 'submittedBy')
        s2 = getMinSet(s1, 'loadedBy')

        if len(s2) == 0:
            chosen_id = random.choice(hitids)
        else:
        	chosen_id = random.choice(s2).hit_id

    	return chosen_id