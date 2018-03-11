from common.dbclient import db, findl
from bson import ObjectId
from common import helpers
from random import shuffle, randint
import pandas as pd
from models.Experiment import Experiment
from models.Message import Message, RatedMessage, GeneratedMessage, FixedMessage



def get_task_vars():
    rand_no = randint(1, 1000)
    wid = u'test_worker_%s' % rand_no
    aid = u'test_ass_%s' % rand_no
    return wid, aid, use_sandbox


def get_experiment(experiment_id, init_conf={'experiment_name': 'quality'}):
    return Experiment(use_sandbox, name='unit_test', experiment_id=experiment_id, init_task_config=init_conf)

def create_task(task, task_type, init_conf, messages):
    experiment = get_experiment(exp.exp_id, init_conf)
    tr = experiment.create_task(
        task, init_conf[task_type], {'messages': messages})
    return tr, experiment

def start_task(task, task_type, init_conf, messages):
    tr, experiment = create_task(task, task_type, init_conf, messages)
    tr.start_task()
    print 'TASK STARTED-> %s | %s'%(tr.task_type, tr.task_id)
    return tr, experiment

def create_generate_task(persona="Charles"):
    task_type = 'generate_quality'
    task = TASKS[task_type]
    init_conf = {
        'generate_quality': {
            'experiment_name':'quality',
            'task_type' : 'generate_quality',
            'task_path' : 'generate_quality.html',
            'max_assignments' : 10,
            'per_message_incentive': 0.16,
            'title' : 'Help a Person to walk more in his daily routine by generating messages.',
            'shortname': persona
            },
        }
    experiment = get_experiment(exp.exp_id, init_conf)
    tr = experiment.create_task(
            task, init_conf[task_type], [{'shortname':persona}])
    tr.start_task()
    return tr, experiment

def create_generate_task_lay(persona="Charles"):
    task_type = 'generate_quality'
    task = TASKS[task_type]
    init_conf = {
        'generate_quality': {
            'experiment_name':'quality',
            'task_type' : 'generate_quality',
            'task_path' : 'generate_quality_lay.html',
            'max_assignments' : 10,
            'per_message_incentive': 0.16,
            'title' : 'Help a Person to walk more in his daily routine by generating messages.',
            'shortname': persona
            },
        }
    experiment = get_experiment(exp.exp_id, init_conf)
    tr = experiment.create_task(
            task, init_conf[task_type], [{'shortname':persona}])
    tr.start_task()
    return tr, experiment

def simulate_generate_task():
    task_type = 'generate_quality'

    def operation(aid, wid, hitId, req, task_type):
        for i in range(1,4):
            m = {'text': 'test message that is greated than 30 chars. %s %s'%(aid, i), 
                'id':'testmessage_%s_%s'%(aid, i),'shortname':req['shortname']}
            obs = GeneratedMessage(str(req['experiment_id']), m['text'], m['id'], m[
                                'shortname'], req['task_id'])
    simulate_last_task(operation)


def create_rating_task(experiment_ids):
    from project1.controllers.RateMessages import RateMessages

    taskd = findl(db.tasks, {'experiment_id':ObjectId(experiment_ids[0])})
    shortname = taskd['shortname']

    task = RateMessages
    task_type = 'rating_quality'
    init_conf = {task_type: {'use_sandbox': use_sandbox,
                             'experiment_name': 'quality',
                             'task_type': task_type,
                             'shortname': shortname,
                             'per_message_incentive': 0.02,
                             'title': 'Help a Person to walk more in his daily routine by rating messages that will be sent to him.',
                             }}

    messages = [x for x in db.messages.find(
        {'experiment_id': {'$in': [str(x) for x in experiment_ids]}})]

    # shuffle the order of messages
    shuffle(messages)
    print 'total messages = %s' % len(messages)

    # start voting task on this experiment id, shuffle messages for the voting
    # task, make sure it works by testing it
    return start_task(task, task_type, init_conf, messages)


def create_rating_task_with_messages(shortname, messages):
    from project1.controllers.RateMessages import RateMessages

    task = RateMessages
    task_type = 'rating_quality'
    init_conf = {task_type: {'use_sandbox': use_sandbox,
                             'experiment_name': 'quality',
                             'task_type': task_type,
                             'shortname': shortname,
                             'per_message_incentive': 0.02,
                             'title': 'Help a Person to walk more in his daily routine by rating messages that will be sent to him.',
                             }}


    # shuffle the order of messages
    shuffle(messages)
    print 'total messages = %s' % len(messages)

    # start voting task on this experiment id, shuffle messages for the voting
    # task, make sure it works by testing it
    return start_task(task, task_type, init_conf, messages)

# def create_ratingV2_task(choose_last = False):
#     task_type = 'ratingV2_quality'

#     experiment_ids = ['54e50a28a54d7528a154a4cf', '54ede06aa54d753d2a8868c5']
#     init_conf = {task_type: {'use_sandbox': use_sandbox,
#                              'experiment_name': 'quality',
#                              'task_type': task_type,
#                              'per_message_incentive': 0.02,
#                              'hit_options': {
#                                  'max_hits_per_worker': 3,
#                                  # including the verification_question in
#                                  # message_count_per_hit
#                                  'message_count_per_hit': 7,
#                                  'is_verification_question': True,
#                                  'task_sub_type': 'quality',
#                                  'no_of_raters_per_message': 5,
#                              },
#                              'title': 'Help a Person to walk more in his daily routine by rating messages that will be sent to him.',
#                              }}

#     messages = [x for x in db.messages.find(
#         {'experiment_id': {'$in': [str(x) for x in experiment_ids]}})][:20]

#     # shuffle the order of messages
#     shuffle(messages)
#     print 'total messages = %s' % len(messages)

#     # start voting task on this experiment id, shuffle messages for the voting
#     # task, make sure it works by testing it

#     return start_task(task, task_type, init_conf, messages)


def simulate_last_rating_task():
    def operation(aid, wid, hitId, req, task_type):
        if task_type == 'ratingV2_quality':
            messages = helpers.pull_random_messages(req)
        else:
            messages = req['messages']
        obs = [RatedMessage(str(req['experiment_id']), m['text'], m['_id'], m[
                            'shortname'], req['task_id']) for m in messages if m['shortname'] != 'verification']
        print 'messages found = %s' % len(messages)
        for m in obs:
            needs_fixing = randint(0, 1)
            m.AddRating(
                aid, wid, 5, hitId, req['use_sandbox'], needs_fixing)
            m.GET()
            # print m.message_id, len(m.doc['votes']), aid, wid,
            # needs_fixing
    simulate_last_task(operation)



def simulate_last_task(operation):
    hits = findl(db.tasks)['hits']
    for hidx, h in enumerate(hits):
        print 'hit %s' % hidx
        hitId = h['hitId']
        req = db.hits.find_one({'hitId': hitId})['requirements']
        task_type = req['task_type']
        print 'TASK Simulating-> %s | %s'%(task_type, req['task_id'])
        for i in range(req['max_assignments']):
            wid, aid, use_sandbox = get_task_vars()
            print 'worker %s' % i
            req['workerId'] = wid
            req['assignmentId'] = aid
            operation(aid, wid, hitId, req, task_type)





def create_clean_generate_task(choose_last=True):
    task_type = 'clean_generate_task'
    task = TASKS[task_type]
    if choose_last:
        last_task = findl(db.tasks, {'task_type': 'rating_quality'})
        last_task_id = str(last_task['_id'])
        task_ids = [last_task_id]
        print 'last_task_id = %s'%last_task_id
    # else:
    #     task_ids = ['5528b3fea54d75860594d2ab']

    init_conf = {task_type: {'use_sandbox': use_sandbox,
                             'experiment_name': 'quality',
                             'task_type': task_type,
                             'per_message_incentive': 0.02,
                             'title': 'Help a Person to walk more in his daily routine by rating messages that will be sent to him.',
                             }}

    messages = [x for x in db.rated_messages.find(
        {'task_id': {'$in': [str(x) for x in task_ids]}})]
    # shuffle the order of messages
    shuffle(messages)
    n = len(messages) if choose_last else 5
    messages = messages[:n] 
    print 'need fixing values = %s' % [x['needs_fixing'] for x in messages]

    return start_task(task, task_type, init_conf, messages)


def create_clean_select_best_task():
    last_task = findl(db.tasks, {'task_type': 'clean_generate_task'})
    last_task_id = str(last_task['_id'])
    task_type = 'clean_select_best_task'
    task = TASKS[task_type]

    init_conf = {task_type: {'use_sandbox': use_sandbox,
                             'experiment_name': 'quality',
                             'task_type': task_type,
                             'per_message_incentive': 0.05,
                             'title': 'Help a Person to walk more in his daily routine by rating messages that will be sent to him.',
                             }}

    messages = [x for x in db.rated_messages.find(
        {'task_id': {'$in': [str(x) for x in [last_task_id]]}})]

    # shuffle the order of messages
    shuffle(messages)

    print 'fixed messages found = %s' % [len(x.get('fixed_messages',[])) for x in messages]
    # start voting task on this experiment id, shuffle messages for the voting
    # task, make sure it works by testing it
    return start_task(task, task_type, init_conf, messages)


def simulate_last_clean_generate_task():
    def operation(aid, wid, hitId, req, task_type):
        obs = FixedMessage(str(req['experiment_id']), req['text'], req[
            'message_id'], req['shortname'], req['task_id'])

        obs.AddFixedMessage(
            aid, wid, 'fixed message %s %s' % (wid, aid), hitId, req['use_sandbox'])
        obs.GET()
    simulate_last_task(operation)

# def aggregate_last_clean_generate_task():


def simulate_last_clean_select_best_task():
    def operation(aid, wid, hitId, req, task_type):
        obs = FixedMessage(str(req['experiment_id']), req['text'], req[
                           'message_id'], req['shortname'], req['task_id'])
        fixed_messages = obs.GET()['fixed_messages']
        shuffle(fixed_messages)
        orig_aid = fixed_messages[0]['assignment_id']
        obs.VoteBest(aid, wid, orig_aid, hitId, req['use_sandbox'])
        obs.GET()
    simulate_last_task(operation)


def _aggregate_ratings(experiment_id):
    experiment_id = experiment_id
    

    new_experiment = Experiment(
        True, name='unit_test_agg_task', experiment_id=experiment_id, init_task_config={})
    t2 = new_experiment.create_task(task, {}, {'messages': []},
                                    task_id=ObjectId(task_id))
    t2.aggregate_message_votes()

    aggc = t2.aggc

    rated_messages = [
        x for x in db[aggc].find({'task_id': str(task_id)})]
    print 'found rated messages = %s for task_id %s'%(len(rated_messages),task_id)
    df = pd.DataFrame(rated_messages)
    if 'n' in df.columns:
        print 'found rated messages = ', len(rated_messages)
        print df.n.value_counts()
    return df

def aggregate_ratings():
    hit = findl(db.hits)
    req = hit['requirements']
    req['hitId'] = hit['hitId']

    task_type = hit['task_type']
    task = TASKS[task_type]

    experiment_id = req['experiment_id']
    task_id = req['task_id']

    new_experiment = Experiment(
        True, name='unit_test_agg_task', experiment_id=experiment_id, init_task_config={})
    t2 = new_experiment.create_task(task, {}, {'messages': []},
                                    task_id=ObjectId(task_id))
    t2.aggregate_message_votes()

    aggc = t2.aggc

    rated_messages = [
        x for x in db[aggc].find({'task_id': str(task_id)})]
    print 'found rated messages = %s for task_id %s'%(len(rated_messages),task_id)
    df = pd.DataFrame(rated_messages)
    if 'n' in df.columns:
        print 'found rated messages = ', len(rated_messages)
        print df.n.value_counts()
    return df



def create_eval_task(messages, persona='Charles',  task_type = 'eval_turk_rate_messages'):
    init_conf = {task_type: {'use_sandbox': use_sandbox,
                             'experiment_name': 'quality',
                             'shortname': persona
                             }}
    task = TASKS[task_type]
    # shuffle the order of messages
    shuffle(messages)
    print 'total messages = %s' % len(messages)

    # start voting task on this experiment id, shuffle messages for the voting
    # task, make sure it works by testing it
    return start_task(task, task_type, init_conf, messages)

from project1.controllers.RateMessages import RateMessages, RateMessagesV2
from project1.controllers.GenerateTask import GenerateTask
from project1.controllers.CleanSelectBestTask import CleanSelectBestTask
from project1.controllers.CleanGenerateTask import CleanGenerateTask
from project1.controllers.RateMessages import EvalExpertRateMessages, EvalTurkRateMessages

TASKS = {
    'generate_location': GenerateTask,
    'rating_location': RateMessages,
    'generate_quality': GenerateTask,
    'rating_quality': RateMessages,
    'generate_ubi': GenerateTask,
    'rating_ubi': RateMessages,
    'ratingV2_quality': RateMessagesV2,
    'clean_select_best_task' : CleanSelectBestTask,
    'clean_generate_task' : CleanGenerateTask,
    'eval_turk_rate_messages': EvalTurkRateMessages,
    'eval_expert_rate_messages' : EvalExpertRateMessages
    # 'is_human': IsHuman,
    # 'feedback_messages': FeedbackMessage
}

def get_new_experiment():
    return Experiment(use_sandbox, name='unit_test', init_task_config={})

use_sandbox = True
exp = get_new_experiment()

