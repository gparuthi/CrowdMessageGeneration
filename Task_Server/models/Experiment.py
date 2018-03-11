from datetime import datetime
from common.logger import logger
from bson import json_util
import pytz
from common.dbclient import db

class Experiment(object):

    def __init__(self, use_sandbox, name='test', experiment_id=None, init_task_config={}):
        self.use_sandbox = use_sandbox
        self.name = name
        if experiment_id == None:
            self.exp_id = db.experiments.insert({'name': name, 'createTime': datetime.now(pytz.utc),
                                                 'use_sandbox': use_sandbox, 'tasks': [], 'init_task_config': init_task_config})
        else:
            self.exp_id = experiment_id
        self.init_task_config = init_task_config
        self.logr = logger(fname=type(self).__name__)
        self.logr.debug("Experiment created: %s, Sandbox = %s, init_task_config=%s" % (
            self.exp_id, self.use_sandbox, json_util.dumps(init_task_config)), class_name=type(self).__name__)
        # create tasks
        self.tasks = []
        # print params
        print self.get_task_conf()

    def create_task(self, task, update_task_config, input_hit_conf, task_id=None):
        tk = task(
            self, self.get_task_conf(), update_task_config, input_hit_conf, task_id)
        # task_config['task_uniqueid'] = '%s_%s'%(taskid,title)]
        self.tasks.append(tk)
        return tk

    def get_task_conf(self):
        fixed_task_config = {
            'message_count_per_hit': 3,
            'max_assignments': 5,
            'experiment_id': self.exp_id,
            'use_sandbox': self.use_sandbox,
            'createTime': datetime.now(pytz.utc),
            'port': 4999 if self.use_sandbox else 5000,
            'FINISHED': False,
            'MIN_RATINGS_TO_CONVERGE': 5,
            'MAX_STD_TO_CONVERGE': 2,
            'MIN_RATE_FOR_GOOD': 3.5,  # must be greater than this,
            'MAX_ASSIGNMENTS_BEFORE_KILL': 20,
            # for sets
            'MIN_SET_LENGTH': 5,
            'MAX_CONVERGENCE_TRIES': 10,
            'MIN_SCORE_FOR_RATE_SET': 3
        }
        fixed_task_config.update(self.init_task_config)
        return fixed_task_config

