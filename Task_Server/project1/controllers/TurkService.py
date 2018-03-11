from flask import Markup
from common.logger import logger
from random import shuffle
from jinja2 import Environment, PackageLoader
import common.turk_utils as turk_utils
import models.Response as Response
from models.Message import RatedMessage, GeneratedMessage, FixedMessage
from common.dbclient import db
from common import helpers
import ipdb
import json

MIN_RATING_TASK_TIME = 10  # seconds

env = Environment(loader=PackageLoader('ken', 'templates/experts_bakeoff')) 
env.filters['escapejs'] = lambda v: Markup(json.dumps(v))
# templates/3x2 for varying roles_goals, tips experiment
# templates/experts_bakeoff for varying different personas

logr = logger(fname='pcbc-mturk-%s'%__name__)

personas = {
    'Charles':{
        'photo_url': 'https://intecolab.com:5000/public/Personas/charles.jpg',
        'roles_goals': [
            "He is 48 years old",
            "He is married with two kids",
            "Being a good father and a husband is really important to him",
            "He would like to feel more confident about his appearance",
        ]
        },
    'John':{
        'photo_url': 'https://intecolab.com:5000/public/Personas/john.jpg',
        'roles_goals': [
            "He is 54 years old",
            "He is divorced",
            "He wants to feel more in control of his life",
            "He wants to feel more energetic",
        ]
        },
    'Mary':{
        'photo_url': 'https://intecolab.com:5000/public/Personas/mary.jpg',
         'roles_goals': [
                "She is 52 years old",
                "She lives with her husband",
                "Being there for friends and family is important to her",
                "She wants to feel more in control of her life",
         ]

    },
    'Grace':{
        'photo_url': 'https://intecolab.com:5000/public/Personas/grace.jpg',
         'roles_goals': [
                "She is 65 years old",
                "She is retired and lives with her husband",
                "Staying independent is important for her",
                "Feeling strong is important to her",
         ]

    },
    'Jose':{
        'photo_url': 'https://intecolab.com:5000/public/Personas/jose.jpg',
         'roles_goals': [
               "He is a 29 years old computer programmer at a startup",
               "He lives with his partner",
               "He wants to feel more disciplined",
               "He really values being successful at work",

         ]

    },

}

def get_html(requirements, task_type, task_path):
    print 'hit requested: %s'%task_path
    if 'rating_quality' == task_type:
         shuffle(requirements['messages'])
    if task_type == 'ratingV2_quality':
        messages = Response.pull_random_messages(requirements)
        messages.append(Response.get_verification_message())
        if len(messages) == requirements['message_count_per_hit']:
            shuffle(messages)
            requirements['messages'] = messages
        else:
            task_type = "sorry_no_more_hits_available"
    template = env.get_template(task_path)
    
    html =  template.render(requirements=requirements, personas=personas)
    return html


def submit(session_data):

    task_data = session_data['data']

    task_type = task_data['task_type']
    r = TurkResponse(task_data)
    try:
        if task_type=='generate_quality':
            return r.submit_generate()
        elif task_type=='rating_quality' or task_type=='ratingV2_quality':
            return r.submit_rating()
        elif task_type=='clean_generate_task':
            return r.submit_clean_generate()
        elif task_type == 'clean_select_best_task':
            return r.submit_clean_select_best_task()
        elif task_type == 'eval_turk_rate_messages':
            return submit_turk_eval(session_data)
    except Exception as e:
        logr.plog("Couldnt push the response to DB. Exceptions: %s"%e, class_name='submit', data=data)
        raise
        return {'id':'FAILED!'}


def submit_turk_eval(session_data):
    db.turk_eval_votes.insert(session_data);

class TurkResponse(Response.Response):

    def submit_generate(self):
        res = []
        for i in range(1, int(self.data.get('message_count_per_hit', 3)) + 1):
            divid = 'message%i_text' % i
            if divid in self.data:
                message_text = self.data[divid]
                message_shortname = self.data['shortname']
                message_id = '%s_m%s' % (self.data['assignmentId'], i)
                m = GeneratedMessage(
                    self.experiment_id, message_text, message_id, message_shortname, self.task_id, updated={'orig': self.data})
        return res

    def submit_rating(self):
        data = self.data
        res = []
        logr.plog("Data: %s" % data,
                          class_name=type(self).__name__, data=self.data)
        if TurkHelpers.verify_submission(data):
            for i in range(1, int(self.data.get('message_count_per_hit', 3)) + 1):
                message_id = data['message%i_id' % i]
                logr.plog("Rating. MessageId: %s" % message_id,
                          class_name=type(self).__name__, data=self.data)
                if message_id != 'verification_question':
                    message_text = data['message%i_text' % i]
                    message_shortname = data['message%i_shortname' % i]
                    message_rating = float(
                        data['message%i_rating_Likely' % i])  # to aggregate
                    message_needs_fixing = int(
                        data.get('message%s_needs_fixing' % i, 0))
                    m = RatedMessage(
                        self.experiment_id, message_text, message_id, message_shortname, self.task_id)
                    res.append(m.AddRating(self.assignment_id, self.worker_id,
                                           message_rating, self.hit_id, self.use_sandbox, message_needs_fixing))
            return res

    def submit_turk_eval_rating(self):
        data = self.data
        res = []
        self.submit_rating()
        for i in range(1, int(self.data.get('eval_message_count_per_hit', 4)) + 1):
            message_id = data['messagee%i_id' % i]
            logr.plog("Rating. MessageId: %s" % message_id,
                      class_name=type(self).__name__, data=self.data)
            if message_id != 'verification_question':
                message_text = data['messagee%i_text' % i]
                message_shortname = data['messagee%i_shortname' % i]
                message_ratings = {}
                for scale in data['scales']:
                    message_rating = float(
                        data['messagee%i_rating_%s' % (i, scale)])  # to aggregate
                    message_ratings[scale] = message_rating
                m = RatedMessage(
                    self.experiment_id, message_text, message_id, message_shortname, self.task_id)
                res.append(m.AddEvalRating(self.assignment_id, self.worker_id,
                                       message_ratings, self.hit_id, self.use_sandbox, message_needs_fixing))
            return res

    def submit_clean_generate(self):
        data = self.data
        res = []
        message_id = data['message_id']
        logr.plog("CleanGenerate. MessageId: %s" % message_id,
                  class_name=type(self).__name__, data=self.data)
        message_text = data['message_text']
        message_shortname = data['message_shortname']
        new_message_text = data['new_message_text']  # to aggregate
        m = FixedMessage(
            self.experiment_id, message_text, message_id, message_shortname, self.task_id)
        res.append(m.AddFixedMessage(self.assignment_id, self.worker_id,
                               new_message_text, self.hit_id, self.use_sandbox))
        return res

    def submit_clean_select_best_task(self):
        data = self.data
        res = []
        message_id = data['message_id']
        logr.plog("CleanSelectBest. MessageId: %s" % message_id,
                  class_name=type(self).__name__, data=self.data)
        message_text = data['message_text']
        message_shortname = data['message_shortname']
        best_message_text = data['best_message_text']  # to aggregate
        m = FixedMessage(
            self.experiment_id, message_text, message_id, message_shortname, self.task_id, write_enabled=False)
        res.append(m.VoteBest(self.assignment_id, self.worker_id,
                               best_message_text, self.hit_id, self.use_sandbox))
        return res

class TurkHelpers():
    @classmethod
    def verify_submission(cls, data):
        if (helpers.get_time(data['endTime']) - helpers.get_time(data['startTime'])).seconds <= MIN_RATING_TASK_TIME:
            cls.add_to_bad_response(data, 'TaskDuration')
            logr.plog("Task duration was too short. AssignmentId: %s" % data[
                      'assignmentId'], class_name=type(cls).__name__, data=data)
            return False
        else:
            for i in range(1, int(data.get('message_count_per_hit', 3)) + 1):
                if data['message%i_id' % i] == 'verification_question':
                    ver_likely_rating = float(
                        data.get('message%i_rating_Likely' % i, 5))
                    if ver_likely_rating > 3.5:
                        cls.add_to_bad_response(data, 'FailedVerification')
                        logr.plog("Verification test failed. AssignmentId: %s" % data[
                                  'assignmentId'], class_name=type(cls).__name__, data=data)
                        return False
        return True

    @classmethod
    def add_to_bad_response(cls, data, reason=''):
        # verification question test failed
        data.update({'reason': reason})
        db.bad_votes.insert(data)
        # add assignment_count of the hit and task
        db.hits.find_and_modify({'hitId': data['hitId']},
                                {
            '$inc': {'additional_assignments': 1}
        },
            new=True)
        # add assignment
        res = turk_utils.extend_hit_assignments(data['hitId'], 1)
        logr.plog("HIT successfully extended: %s, result is: %s" % (
            data['hitId'], res), class_name='add_to_bad_response', data=data)
        # reject assignment
        # res = turk_utils.reject_assignment(data['assignmentId'])
        # logr.plog("Assignment successfully rejected: %s, result is: %s"%(data['hitId'],res), class_name='add_to_bad_response', data=data)
        return {'id': 'FAILED!', 'reason': 'Verification failed!'}
