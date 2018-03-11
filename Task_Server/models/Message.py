from common.dbclient import db
from models import Resource
from common.logger import logger
import numpy as np
import pandas as pd
import operator
import pytz, datetime


logr = logger('pcbc-mturk.models.Message', verbose=False)

class Message(Resource.Resource):

    def __init__(self, experiment_id, text, message_id, shortname, task_id, updated={}, collection="", write_enabled=True):
        if collection != "":
            self.C = db[collection]

        self.experiment_id = experiment_id
        self.text = text
        self.message_id = message_id
        self.shortname = shortname
        self.task_id = str(task_id)
        self.spec = {
            'experiment_id': self.experiment_id,
            'text': self.text,
            'message_id': self.message_id,
            'shortname': self.shortname,
            'task_id': self.task_id,
        }

        self.logr = logr
        self.doc = self.GET()
        if write_enabled:
            if not self.doc:
                # print 'Adding new message to DB'
                self._id = self.PUT(updated)

    @classmethod
    def _GetSetDict(cls, C, key, value):
        recs = C.find({key: str(value), 'message_id': {'$exists':True}})
        return recs

    @classmethod
    def GetSet(cls, C, key, value):
        print 'Getting Messages Set for %s'%C
        rated_recs = []
        recs = cls._GetSetDict(C, key, value)
        for rec in recs:
            m = cls.FromDict(rec)
            rated_recs.append(m)
        return rated_recs

    @classmethod
    def FromDict(cls, rec):
        return cls(rec.get('experiment_id'), rec.get('text'), rec.get('message_id'), rec.get('shortname'), rec.get('task_id'), write_enabled=False)

    def GET(self):
        self.doc = self.C.find_one(self.spec)
        return self.doc

    def PUT(self, updated={}):
        di = {}
        di.update(self.spec)
        di.update(updated)
        di['created_at'] = datetime.datetime.now(pytz.utc)
        doc = self.C.insert(di)
        if not doc:
            self.logr.debug(
                "Error putting the message.", class_name=type(self).__name__, data=res)
            return None
        return doc

    def SAVE(self, collection):
        db[collection].insert(self.doc)

    def DELETE(self, collection):
        db[collection].remove(self.doc)        

    def __call__(self):
        return self.GET()


class GeneratedMessage(Message):
    C = db.messages


class FixedMessage(Message):
    C = db.message_votes

    def PUT(self, updated={}):
        d = {
            'fixed_messages': [{'assignment_id':'Original'},{'assignment_id':'None'}],
            'workers': []
        }
        d.update(updated)
        Message.PUT(self, d)

    def AddFixedMessage(self, assignment_id, worker_id, text, hit_id, use_sandbox):
        res = self.C.find_and_modify(self.spec,
                 {'$addToSet': {'fixed_messages': {'assignment_id': assignment_id,
                                          'worker_id': worker_id,
                                          'text': text,
                                          'hitId': hit_id,
                                          'votes': 0,
                                          'use_sandbox': use_sandbox},
                                'workers': worker_id
                                }
                  },
                 upsert=True, new=True)
        self.logr.debug("Fixed message inserted successfully. AssignmentId: %s" %
                       assignment_id, class_name=type(self).__name__, data=res)


    def VoteBest(self, assignment_id, worker_id, voted_message_text, hit_id, use_sandbox):
        collection = db.select_best_votes
        res = {
            'assignment_id': assignment_id, 
            'hit_id':hit_id, 
            'worker_id': worker_id, 
            'voted_message_text': voted_message_text
        }
        to_insert = {}
        to_insert.update(self.spec)
        to_insert.update(res)

        collection.insert(to_insert)

        # q = self.spec
        # q.update({"fixed_messages.assignment_id":orig_assignment_id})
        # res = self.C.find_and_modify(q,
        #                      {
        #                      '$inc': {'fixed_messages.$.votes': 1},
        #                      '$addToSet': {'select_best_votes': {'assignment_id': assignment_id,
        #                           'worker_id': worker_id,
        #                           'orig_assignment_id': orig_assignment_id,
        #                           'hitId': hit_id,
        #                           'use_sandbox': use_sandbox
        #                           },
        #                           'select_best_workers': worker_id
        #                         }
                                
        #                 },
        #                              upsert=True, new=True)
        self.logr.debug("Vote on fixed message increased successfully. AssignmentId: %s" %
                       assignment_id, class_name=type(self).__name__, data=res)



    def aggregate(self):
        """ Selects the highest voted message by the turkers on the select_best grammar task. """
        rm = self.doc
        if 'fixed_messages' in rm:
            fixed_messages = [x for x in rm['fixed_messages']]
        
            # find message with highest no of votess
            best_message = max(fixed_messages, key=lambda x: x['votes'])

            if best_message['assignment_id'] == 'None':
                print 'Couldnt Fix. Setting rating to 0.'
                r['mean'] = 0

            rm['orig_message'] = rm['text']
            rm['best_message'] = best_message
            rm['text'] = best_message['text']
            rm['n'] = len(fixed_messages)
            rm['comments'] = ','.join([x.get('comment', '') for x in fixed_messages])
            return True 
        else:
            return False

    # @staticmethod
    # def GetSet(C, task_id):
    #     rated_recs = []
    #     recs = [x for x in C.find({'task_id': str(task_id)})]
    #     print '--- found %s messages'%len(recs)
    #     for rec in recs:
    #         m = FixedMessage.FromDict(rec)
    #         rated_recs.append(m)
    #     return rated_recs


class RatedMessage(Message):
    C = db.message_votes

    @classmethod
    def _GetSetDict(cls, C, key, value):
        recs = C.find({key: str(value), 'message_id': {'$exists':True}, '$where': '(this.votes.length > 0)'})
        return recs

    def AddRating(self, assignment_id, worker_id, rating, hit_id, use_sandbox, message_needs_fixing=0):
        res = self.C.find_and_modify(self.spec,
                                     {'$addToSet': {'votes': {'assignment_id': assignment_id,
                                                              'worker_id': worker_id,
                                                              'rating': rating,
                                                              'hitId': hit_id,
                                                              'needs_fixing': message_needs_fixing,
                                                              'use_sandbox': use_sandbox},
                                                    'workers': worker_id
                                                    },
                                      '$inc': {'sum': rating}
                                      },
                                     upsert=True, new=True)
        self.logr.debug("Voted message inserted successfully. AssignmentId: %s" %
                       assignment_id, class_name=type(self).__name__, data=res)


    def PUT(self, updated={}):
        d = {
            'votes': [],
            'workers': []
        }
        d.update(updated)
        Message.PUT(self, d)

    def aggregate(self):
        doc = self.doc
        if 'votes' in doc:
            votes = [x for x in doc['votes'] if x['worker_id']!='NoWorkerId']
        else:
            self.logr.debug(
                'No votes key found in this message\'s doc ')
            return False
        if len(votes) == 0:
            self.logr.debug(
                'No votes found for this message for the current task ')
            return False
        self.logr.debug('Found rated message %s' % self.message_id)
        votes_for_fixing = sum([x.get('needs_fixing', 0) for x in votes]) 
        print 'n=%s | fix_votes=%s | "%s"'%(len(votes), votes_for_fixing,doc['text'])
        if votes_for_fixing >= 3:
            doc['needs_fixing'] = True
        else:
            doc['needs_fixing'] = False
        doc['votes_for_fixing'] = votes_for_fixing
        doc['mean'], doc['std'], doc['median'] = RatedMessage.get_scores(votes)
        doc['zmean'], doc['zmedian'], doc['zstd'] = RatedMessage.get_zscores(self.task_id, votes)
        doc['n'] = len(votes)
        doc['comments'] = ','.join([x.get('comment', '') for x in doc['votes']])
        return True

    def check_convergence(self, min_rating, max_std, min_good_rating):
        r = self.doc
        r['is_bad'] = False
        self.logr.debug("n: %s should be >=%s - STD: %s should be <%s" %
                       (r['n'], min_rating, r['std'], max_std), class_name=type(self).__name__)
        if r['n'] >= min_rating and r['std'] <= max_std:
            self.logr.debug("Found converged message: %s with avg_rating:%s > %s" % (r['text'], r['mean'], min_good_rating),
                           class_name=type(self).__name__)
            r['HasConverged'] = True
            # check final rating
            if r['mean'] < min_good_rating:
                r['is_bad'] = True
                self.logr.debug(
                    'Unfortunately, the messages doesnt cross the given threshold')

    @staticmethod
    def get_scores(votes_info, key='rating'):
        votes = [x[key] for x in votes_info]
        return np.mean(votes), np.std(votes), np.median(votes)

    @staticmethod
    def get_zscores(task_id, votes):
        zscores = []
        for v in votes:
            worker_id = v.get('worker_id')
            rating = v['rating']
            wscores = RatedMessage.get_worker_scores(task_id, worker_id)
            zscore = (int(rating) - wscores.mean()) / wscores.std(ddof=0)
            zscores.append(zscore)
            # print worker_id, 'rating: %s' % v['rating'], 'zscore: %s' % zscore
        return np.mean(zscores), np.std(zscores), np.median(zscores)

    @staticmethod
    def get_worker_scores(task_id, worker_id):
        zscore = 0
        # find all responses of worker for rating tasks (for this task_type)
        res = [x for x in db.responses.find(
            {'task_id': str(task_id), 'workerId': worker_id})]
        all_ratings = []
        for r in res:
            worker_id = r['workerId']
            for i in range(1, 15):
                k = u'message%s_id' % i
                if k in r:
                    mid = r[k]
                    if mid != u'verification_question':
                        rating = r[u'message%s_rating_Likely' % i]
                        all_ratings.append(rating)
        # all_ratings = [x['rating'] for x in db.worker_ratings.find({'worker_id':worker_id})]
        # retrive all message ratings and calculate mean, std
        ratingss = pd.Series(all_ratings).astype(int)
        # calculate the
        return ratingss


class EvalRatedMessage(RatedMessage):
    C = db.message_votes

    def AddEvalRating(self, assignment_id, worker_id, message_ratings, hit_id, use_sandbox, message_needs_fixing=0):
        res = self.C.find_and_modify(self.spec,
                                     {'$addToSet': {'eval_votes': {'assignment_id': assignment_id,
                                                              'worker_id': worker_id,
                                                              'ratings': message_ratings,
                                                              'hitId': hit_id,
                                                              'needs_fixing': message_needs_fixing,
                                                              'use_sandbox': use_sandbox},
                                                    'workers': worker_id
                                                    },
                                      '$inc': {'sum': rating}
                                      },
                                     upsert=True, new=True)
        self.logr.debug("Eval Rated message inserted successfully. AssignmentId: %s" %
                       assignment_id, class_name=type(self).__name__, data=res)

    def PUT(self, updated={}):
        d = {
            'votes': [],
            'eval_votes': [],
            'workers': []
        }
        d.update(updated)
        Message.PUT(self, d)

    def aggregate(self):
        r = self.doc
        if 'votes' in r:
            votes = [x for x in r['votes']]
        else:
            self.logr.debug(
                'No votes key found in this message\'s doc ')
            return False
        if len(votes) == 0:
            self.logr.debug(
                'No votes found for this message for the current task ')
            return False
        self.logr.debug('Found rated message %s' % self.message_id)
        r['mean'], r['std'], r['median'] = RatedMessage.get_scores(votes)
        r['zmean'], r['zmedian'], r['zstd'] = RatedMessage.get_zscores(self.task_id, votes)
        # TODO : Calculate the means of each scale below

        r['n'] = len(votes)
        r['comments'] = ','.join([x.get('comment', '') for x in r['votes']])
        return True
