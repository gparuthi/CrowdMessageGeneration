import common.task_utils as task_utils
import common.turk_utils as turk_utils
import common.check_task_status
from common.dbclient import db

import collections

def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d

class Task(object):

    def __init__(self, experiment, task_config, update_task_config, input_hit_conf, task_id=None):
        # add task config params
        update(task_config, self.default_task_config)
        update(task_config, update_task_config)
        task_config['taskid'] = "%s_%s" % (
            experiment.name, task_config['task_type'])
        if task_config['use_sandbox']:
            task_config['title'] += '_%s' % "test4"  # random.randint(1,1000)

        self.input_hit_conf = input_hit_conf

        self.task_config = task_config
        self.task_type = task_config['task_type']
        self.task_id = task_id
        self.experiment = experiment
        self.experiment.logr.plog("Task created: %s, Experiment: %s" % (
            self.task_type, self.experiment.exp_id), class_name=type(self).__name__)
        # Prepare Input
        self.prepare_input()
        # self. = create_task.shuffle_hits(experiment.sits_df)

    def start_task(self):
        # Initialize HITS for TURK
        self.initialize_hits()
        # Create the HITS on TURK
        if len(self.final_hits) > 0 and self.task_id == None:
            taskd = task_utils.create_task(self.task_config, self.final_hits)
            self.task_doc = taskd
            self.task_id = taskd['_id']
            self.experiment.logr.plog("Task started: %s, Experiment: %s" % (
                self.task_doc['_id'], self.experiment.exp_id), class_name=type(self).__name__)
        else:
            self.experiment.logr.plog("No Input or task_id might already be started: %s" % (
                self.task_id), class_name=type(self).__name__)

    def get_taskd(self):
        self.task_doc = db.tasks.find_one({'_id': self.task_id})
        return self.task_doc

    def prepare_input(self):
        raise NotImplementedError("Should have implemented this")

    def initialize_hits(self):
        raise NotImplementedError("Should have implemented this")

    def after_end(self):
        self.experiment.logr.plog(
            "Task Ended: %s " % self.task_type, class_name=type(self).__name__)

    @property
    def experiment_id(self):
        return self.experiment.exp_id

class AnyAggregateTask(Task):
    def prepare_input(self):
        self.messages = self.input_hit_conf.get('messages', [])
        if len(self.messages) == 0:
            print "No messages found in input. Please provide messages to be rated."
        else:
            self.experiment.logr.plog("Found %s messages in input conf" % len(
                self.messages), class_name=type(self).__name__)
            for m in self.messages:
                m['experiment_id'] = str(self.experiment.exp_id)

        # Create Input Set
        for m in self.messages:
            m['HasConverged'] = False
            if '_id' in m:
                del m['_id']
            try:
                db[self.votesc].insert(m)
            except Exception as e:
                self.experiment.logr.plog("%s | Message already exists in rate_messsages input collection: %s" % (
                    e, m.get('id', 'NoID')), class_name=type(self).__name__)

    def initialize_hits(self):
        raise NotImplementedError("Should have implemented this")
    
    def aggregate_message_votes(self):
        raise NotImplementedError("Should have implemented this")

    def after_end(self):
        Task.after_end(self)
        self.experiment.logr.plog(
            "Initiating aggregation", class_name=type(self).__name__)
        self.aggregate_message_votes()