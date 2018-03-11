from random import shuffle, choice
from common.dbclient import db, client
from common.logger import logger
from dateutil import parser
from datetime import datetime

logr = logger(fname='pcbc-mturk-helpers', insertDate=False)

def pull_random_messages(requirements):
    task_id = requirements['task_id']
    worker_id = requirements['workerId']
    # 1 is the verification_message
    message_count_per_hit = requirements['message_count_per_hit'] - 1
    no_of_raters_per_message = requirements['no_of_raters_per_message']
    if client:
        potential_messages = [x for x in db.message_votes.find(
            {'task_id': task_id, 'workers': {'$nin': [worker_id]}})]
        incomplete_messages = [
            m for m in potential_messages if len(m['votes']) < no_of_raters_per_message]
        # randomly choose message (n=message_count_per_hit)
        shuffle(incomplete_messages)
        chosen_messages = incomplete_messages[:message_count_per_hit]
        # If there only few messages in the chosen_messages, choose few from
        # finished ones that the worker hasn't seen.
        if len(chosen_messages) < message_count_per_hit:
            finished_messages = [
                m for m in potential_messages if len(m['votes']) == no_of_raters_per_message]
            shuffle(finished_messages)
            additional_messages = finished_messages[
                :(message_count_per_hit - len(chosen_messages))]
            chosen_messages.extend(additional_messages)
        return chosen_messages
    else:
        logr.plog("Couldn't connect to MongoDB. Please check the connection.",
                  class_name='pull_random_messages', data=requirements)


def get_verification_message():
    vd = {'Charles': ["Don't fix over target which stands very high nowadays.  If BOSS regularly fixes you a target you must be prepared for that from last month. ",
                      "Whatever you do, don't listen to the person above me.",
                      "Routine Medical checkup may help you. Business tension must be freed from your mind. Take Light food with clear water. in morning.",
                      "Watch some channels of your favorite and also let your wife watch her favorite also too. Because sharing gives more energy.",
                      "When watching television don't act real with it for keep in mind that you are only viewing it and not enact in them.",
                      "When you comment any of the programme mind your left or right viewer's thought and see it wont affect them.",
                      "Hello there, you appear to be a handsome, happy individual.  As mentioned in your description, you work and appear to be a successful person as well.",
                      ]}
    message = {
        'text': choice(vd['Charles']).encode('utf-8'),
        '_id': 'verification_question',
        'shortname': 'verification'
    }
    return message

def get_time(timeob):
    if type(timeob) == datetime:
        return timeob.replace(tzinfo=None)
    if type(timeob) == str or type(timeob) == unicode:
        return parser.parse(timeob).replace(tzinfo=None)

    raise Exception