from project1.controllers.CleanGenerateTask import CleanGenerateTask
from models.Message import FixedMessage
from common.dbclient import db
from models.Task import Task

class CleanSelectBestTask(CleanGenerateTask):

    default_task_config = {
            'task_type' : 'clean_select_best_task',
            'per_message_incentive': 0.05,
            'title' : 'Help someone to walk more in his daily routine by rating messages that will be sent to him.',
            'hit_options':{
                'message_count_per_hit': 1, 
                'no_of_turkers_per_message' : 10
                },
            }

    def prepare_input(self):
        CleanGenerateTask.prepare_input(self)
        for m in self.messages:
            if m not in self.already_fixed_messages:
                m['select_best_workers'] = []


    def aggregate_message_votes(self):
        collection = db.select_best_votes
        fix_votes = [x for x in collection.find({'task_id': str(self.task_id)})]

        # remove previous aggregation done for this experiment_id
        db[self.aggc].remove({'task_id': str(self.task_id)})

        self.experiment.logr.plog("Total votes found: %s" % len(
            fix_votes), class_name=self.task_type)
        self.experiment.logr.debug(
            "Task Config: %s" % self.task_config, class_name=self.task_type)

        self.experiment.logr.plog(
            "Aggregation complete.", class_name=self.task_type)

        return fix_votes