from mongoengine import *
from common.dbclient import db
import datetime
from operator import attrgetter

class HitInstance(Document):
    date_modified = DateTimeField(default=datetime.datetime.now)
    date_created = DateTimeField(default=datetime.datetime.now())
    hit_id = StringField(required=True)
    loadedBy = IntField(min_value=0, max_value=100, default=0)
    submittedBy = IntField(min_value=0, max_value=100, default=0)
    loadedAndSubmitted = IntField(min_value=0, max_value=100, default=0)
    loadedByWorkers = DictField(default={})
    submittedByWorkers = DictField(default={})
    
    def isLoaded(self, worker_id="default"):
        self.loadedBy += 1
        self.loadedAndSubmitted += 1
        self.loadedByWorkers[worker_id] = datetime.datetime.now()
        self.save()
        
    def isUnLoaded(self, worker_id="default"):
        self.loadedBy -= 1
        self.loadedAndSubmitted -= 1
        self.delWorker(worker_id)
        self.save()
    
    def isSubmitted(self, worker_id="default"):
        self.submittedBy += 1
        self.loadedAndSubmitted += 1
        self.submittedByWorkers[worker_id] = datetime.datetime.now()
        self.save()

    def delWorker(self, worker_id):
    	if worker_id in self.loadedByWorkers:
	        del self.loadedByWorkers[worker_id]

    def check_for_times(self):
    	for worker_id in self.loadedByWorkers:
    		loadtime = self.loadedByWorkers[worker_id]
    		timedelta = loadtime - datetime.datetime.now()
    		seconds = timedelta.total_seconds()
    		print worker_id, seconds
    		if seconds > 5*60:
    			self.delWorker(worker_id)
    			print 'updated worker %s'%worker_id

    	self.loadedBy = len(self.loadedByWorkers)
    	self.loadedAndSubmitted = self.loadedBy+self.submittedBy
    	self.save()

    @classmethod
    def get_with_least_submits(cls, hitids):
    	hit_instances = HitInstance.objects(hit_id__in = hitids)
    	min_num = min(hit_instances,key=attrgetter('submittedBy'))
    	return min_num