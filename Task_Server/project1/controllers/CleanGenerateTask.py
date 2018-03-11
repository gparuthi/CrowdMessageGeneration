from common.dbclient import db
from models.Task import Task
from models.Message import FixedMessage
# import ipdb 

class CleanGenerateTask(Task):
    default_task_config = {
            'task_type' : 'clean_generate_task',
            'per_message_incentive': 0.05,
            'title' : 'Help someone to walk more in his daily routine by rating messages that will be sent to him.',
            'hit_options':{
                'message_count_per_hit': 1, 
                'no_of_turkers_per_message' : 5
                },
            }
        
    def prepare_input(self):
        self.inputc = 'ratemessages_input'
        self.votesc = 'message_votes'
        self.aggc = 'rated_messages'
        self.already_fixed_messages = []

        self.messages = self.input_hit_conf.get('messages', [])
        if len(self.messages) == 0:
            print "No messages found in input. Please provide messages to be rated."
        else:
            self.experiment.logr.plog("Found %s messages in input conf" % len(
                self.messages), class_name=type(self).__name__)
            for m in self.messages:
                m['experiment_id'] = str(self.experiment.exp_id)

            # ipdb.set_trace()

            # Create Input Set
            input_set = []
            for m in self.messages:
                if '_id' in m:
                    del m['_id']
                if 'votes' in m:
                    del m['votes']
                if 'task_id' in m:
                    del m['task_id']
                if 'task_type' in m:
                    del m['task_type']
                if 'workers' in m:
                    del m['workers']
                try:
                    if 'needs_fixing' in m:
                        if m['needs_fixing']==0:
                            self.already_fixed_messages.append(m)
                            continue
                    input_set.append(m)
                    db[self.inputc].insert(m)
                except Exception as e:
                    self.experiment.logr.plog("%s | Message already exists in rate_messsages input collection: %s" % (
                        e, m.get('id', 'NoID')), class_name=type(self).__name__)

            self.messages = input_set

    def initialize_hits(self):
        self.experiment.logr.plog("Number of messages to be fixed: %s" % len(
            self.messages), class_name=type(self).__name__)
        no_of_turkers_per_message = self.task_config[
            'hit_options']['no_of_turkers_per_message']

        self.task_config['max_assignments'] = no_of_turkers_per_message
        self.task_config['hit_options'][
            'max_hits_per_worker'] = no_of_turkers_per_message

        self.final_hits = self.messages # for hits with multiple messages -> [{'messages': self.messages}]

    
    def start_task(self):
        Task.start_task(self)

        # create docs in votesc collection
        def assign_task_id(m):
            m['task_id'] = str(self.task_id)
            m['task_type'] = str(self.task_type)
            db[self.votesc].insert(m)

        for m in self.messages:
            assign_task_id(m)
            
        for m in self.already_fixed_messages:
            assign_task_id(m)

    def aggregate_message_votes(self):
        rated_messages = FixedMessage.GetSet(
            db[self.votesc], 'task_id', self.task_id)

        # remove previous aggregation done for this experiment_id
        db[self.aggc].remove({'task_id': str(self.task_id)})

        self.experiment.logr.plog("Total messages found: %s" % len(
            rated_messages), class_name=self.task_type)
        
        for rm in rated_messages:
            rm.SAVE(self.aggc)

        self.experiment.logr.plog(
            "Aggregation complete.", class_name=self.task_type)
