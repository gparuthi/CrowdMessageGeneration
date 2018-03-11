import pandas as pd
from common.dbclient import db
from models.Message import RatedMessage, EvalRatedMessage
import math
from common import helpers
from models.Task import Task, AnyAggregateTask
import ipdb
import random

class RateMessages(AnyAggregateTask):
    # Input: 1 persona, 1 situation, n messages
    # Creates: 1 HIT for 1 Task
    # Output: Rated messages
    # Should precede: RateSet on completion

    default_task_config = {
        'task_type': 'rating_quality',
        'incentive': 0.1,
        'per_message_incentive': 0.022,
        'title': 'Help someone to walk more in his daily routine by rating messages that will be sent to him.',
        'shortname':'NA',
        'hit_options': {
            'message_count_per_hit': 13, # includes the verification question
            'is_verification_question': True,
            'task_sub_type': 'tone',
            'no_of_raters_per_message': 10
        },
    }

    MessageType = RatedMessage

    def prepare_input(self):
        self.inputc = 'ratemessages_input'
        self.votesc = 'message_votes'
        self.aggc = 'rated_messages'
        AnyAggregateTask.prepare_input(self)

    def initialize_hits(self):
        # messages = [x for x in
        # db.ratemessages_input.find({'experiment_id':str(self.experiment.exp_id),
        # 'HasConverged': False}).sort('_id',-1)] # orig.experiment might be
        # legacy, experiment_id should be at the root
        

        finalhits = []
        no_of_messages = len(self.messages)
        self.experiment.logr.debug("Number of messages to be rated: %s" % no_of_messages , class_name=type(self).__name__)
        no_of_raters_per_message = self.task_config[
            'hit_options']['no_of_raters_per_message']

        message_count_per_hit = self.task_config['hit_options']['message_count_per_hit']
        print 'Message count per hit = %s'%message_count_per_hit

        self.task_config['max_assignments'] = no_of_raters_per_message
        self.task_config['hit_options'][
            'max_hits_per_worker'] = no_of_raters_per_message

        if no_of_messages > 0:
            
            # idf['hitId'] = idf.orig.apply(lambda x: x['hitId'])
            actual_messages_per_hit = message_count_per_hit - 1

            rem = no_of_messages%actual_messages_per_hit
            if rem > 0:
                rem = actual_messages_per_hit - rem

            for i in range(rem):
                self.messages.append(random.choice(self.messages[:-rem]))

            idf = pd.DataFrame(self.messages).reset_index()
            idf['hit_no'] = idf['index'].apply(lambda x: x/actual_messages_per_hit)
            print idf.hit_no.value_counts()
            # hits are converted to json of the form
            for name, group in idf.groupby('hit_no'):
                d = {}
                d.update(self.task_config['hit_options'])

                # ipdb.set_trace()
                d.update({
                          'shortname': self.task_config.get('shortname'),
                          'messages': [{'_id': x['_id'],
                                        'text':x['text'].encode('utf-8'),
                                        'shortname':x['shortname']} for x in group.to_dict(orient='records')]})
                if self.task_config['hit_options']['is_verification_question']:
                    d['messages'].append(helpers.get_verification_message())
                d['message_count_per_hit'] = len(d['messages'])
                finalhits.append(d)
        self.final_hits = finalhits


    def _aggregate_message_votes(self, key, value):
        inputc = self.inputc
        votesc = self.votesc
        aggc = self.aggc

        # ipdb.set_trace()

        rated_messages = self.MessageType.GetSet(
            db[votesc], key, value)

        # remove previous aggregation done for this experiment_id
        db[self.aggc].remove({key: str(value)})



        self.experiment.logr.plog("Total messages found: %s" % len(
            rated_messages), class_name=type(self).__name__ )
        self.experiment.logr.debug(
            "Task Config: %s" % self.task_config, class_name=type(self).__name__)
        for rm in rated_messages:
            if rm.aggregate():
                if rm.check_convergence(self.task_config['MIN_RATINGS_TO_CONVERGE'], self.task_config['MAX_STD_TO_CONVERGE'], self.task_config['MIN_RATE_FOR_GOOD']):
                    # Update input c
                    db[inputc].update({'id': rm.message_id,
                                               'orig.experiment_id': rm.experiment_id},
                                              {'$set': {'HasConverged': True}})
                rm.SAVE(self.aggc)

        self.experiment.logr.debug(
            "Aggregation complete.", class_name=type(self).__name__)

    def aggregate_message_votes(self):
        self._aggregate_message_votes('task_id', self.task_id)

    def aggregate_message_votes_for_experiment(self):
        self._aggregate_message_votes('experiment_id', self.experiment_id)        

    def start_task(self):
        Task.start_task(self)
        # store messages in message_votes
        for m in self.messages:
            # this adds the message to the db
            m = self.MessageType(str(self.experiment.exp_id),
                             m['text'].encode('utf-8'),
                             str(m['_id']),
                             m['shortname'],
                             self.task_id, {'task_type':self.task_type})


class EvalExpertRateMessages(RateMessages):
    MessageType = EvalRatedMessage
    
    default_task_config = {
        'task_type': 'eval_expert_rate_messages',
        'per_message_incentive': 0.022,
        'title': 'Help someone to walk more in his daily routine by rating messages that will be sent to him.',
        'hit_options': {
            'message_count_per_hit': 16,
            'is_verification_question': False,
            'no_of_raters_per_message': 5,
            'task_sub_type': 'experts'
        },
    }

    def initialize_hits(self):
        finalhits = []
        df = pd.DataFrame(self.messages)

        hitgrps = df.groupby('batchid')

        for i in range(2):
            print 'i: ', i
            batch = hitgrps.get_group(i)
            d = {}    
            d.update(self.task_config['hit_options'])
            d.update({
                      'shortname': self.task_config.get('shortname'),
                      'messages': [{'_id': x['_id'],
                                    'text':x['text'].encode('utf-8'),
                                    'shortname':x['shortname']} for x in batch.to_dict(orient='records')]})
    
            d['message_count_per_hit'] = len(d['messages'])
            finalhits.append(d)
        self.final_hits = finalhits

class EvalTurkRateMessages(RateMessages):
    default_task_config = {
        'task_type': 'eval_turk_rate_messages',
        'per_message_incentive': 0.022,
        'title': 'Help someone to walk more in his daily routine by rating messages that will be sent to him.',
        'hit_options': {
            'message_count_per_hit': 13,
            'is_verification_question': True,
            'no_of_raters_per_message': 5,
            'task_sub_type': 'turk'
        },
    }

    def initialize_hits(self):
        finalhits = []
        df = pd.DataFrame(self.messages)

        hitgrps = df.groupby('batchid')

        no_of_batches = 4
        no_of_subbatches = 4

        for i in range(no_of_batches): 
            batch = hitgrps.get_group(i)
            subgroups = batch.groupby('subbatchid')
            # print for debugging purposes
            # print '**** Batch %d ****'%(i) 
            # for rec in batch.to_dict(outtype='records'):
            #     print rec['text']

            for j in range(no_of_subbatches):                
                subbatch = subgroups.get_group(j)
                d = {}    
                d.update(self.task_config['hit_options'])
                d.update({
                          'shortname': self.task_config.get('shortname'),
                          'messages': [{'_id': x['_id'],
                                        'text':x['text'].encode('utf-8'),
                                        'shortname':x['shortname']} for x in batch.to_dict(outtype='records')],
                            'eval_messages': [{'_id': x['_id'],
                                        'text':x['text'].encode('utf-8'),
                                        'shortname':x['shortname']} for x in subbatch.to_dict(outtype='records')]})
        
                d['message_count_per_hit'] = len(d['messages'])
                d['eval_message_count_per_hit'] = len(d['eval_messages'])
                finalhits.append(d)

                # print for debugging purposes
                # print '** SubBatch %d **'%(j)
                # for rec in subbatch.to_dict(outtype='records'):
                #     print rec['text']
                
        self.final_hits = finalhits

class RateMessagesV2(RateMessages):
    default_task_config = {
        'task_type': 'ratingV2_task',
        'incentive': 0.1,
        'per_message_incentive': 0.02,
        'title': 'Help someone to walk more in his daily routine by rating messages that will be sent to him.',
        'hit_options': {
            'max_hits_per_worker': 3,
            'message_count_per_hit': 7,
            # including the verification question
            'is_verification_question': True,
            'task_sub_type': 'quality',
            'no_of_raters_per_message': 5
        },

    }

    def initialize_hits(self):
        finalhits = []
        self.experiment.logr.debug("Number of messages to be rated: %s" % len(
            self.messages), class_name=type(self).__name__)
        max_hits_per_worker = self.task_config[
            'hit_options']['max_hits_per_worker']
        message_count_per_hit = self.task_config['hit_options']['message_count_per_hit']
        no_of_raters_per_message = self.task_config[
            'hit_options']['no_of_raters_per_message']

        no_of_messages = len(self.messages)

        total_no_of_ratings_needed = float(
            no_of_messages) * no_of_raters_per_message
        total_no_of_assignments = math.ceil(
            total_no_of_ratings_needed / (message_count_per_hit - 1))  # -1 for verification question
        max_assignments = int(
            math.ceil(total_no_of_assignments / max_hits_per_worker))

        print 'Setting max_assignments as %s' % max_assignments

        if len(self.messages) > 0:
            # Create HITS
            for i in range(max_hits_per_worker):
                d = self.task_config['hit_options']
                d['hit_no'] = i
                finalhits.append(d)

        self.task_config['max_assignments'] = max_assignments
        self.final_hits = finalhits
