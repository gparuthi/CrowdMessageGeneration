from project1.tests.unit_test import *
import pandas as pd
import ipdb

def get_messages_in_clipboard_as_csv(experiment_ids, clipboard=False, iscols= True, isdf = True):
    cols = [ u'comments','zmean','zmedian','zstd', 
                                             u'mean', u'median', u'text',
                                             u'n', u'shortname', u'std']
    rated_messages = [x for x in db.rated_messages.find({'experiment_id':{'$in':[str(x) for x in experiment_ids]}})]
    mdf = pd.DataFrame(rated_messages)
    if iscols:
        mdf= mdf[cols]
    if clipboard:
        mdf.to_clipboard()
    if isdf:
        return mdf
    else:
        return rated_messages

def start_task(task, task_type, init_conf, messages, ename):
    experiment = Experiment(
        use_sandbox, name=ename, init_task_config=init_conf)
    tr = experiment.create_task(
        task, init_conf[task_type], {'messages': messages})
    tr.start_task()
    print 'TASK STARTED-> %s | %s' % (tr.task_type, tr.task_id)
    return tr, experiment


def create_clean_generate_task(messages):
    task_type = 'clean_generate_task'
    task = TASKS[task_type]

    init_conf = {task_type: {'use_sandbox': use_sandbox,
                             'experiment_name': 'quality',
                             'task_type': task_type,
                             'per_message_incentive': 0.05,
                             'title': 'Help Charles to walk more in his daily routine by rating messages that will be sent to him.',
                             'hit_options': {
                                 'message_count_per_hit': 1,
                                 'no_of_turkers_per_message': 3
                             }
                             }}
    m_needs_fixing = [x['needs_fixing'] for x in messages]
    print '%s / %s need fixing values = %s' % (len(m_needs_fixing), len(messages), m_needs_fixing)

    return start_task(task, task_type, init_conf, messages, task_type)

def create_rating_task(messages, ename, task_sub_type="good"):
    from project1.controllers.RateMessages import RateMessages
    task = RateMessages
    task_type = 'rating_quality'
    
    init_conf = {task_type: {'use_sandbox': use_sandbox,
                             'experiment_name': 'quality',
                             'task_type': task_type,
                             'per_message_incentive': 0.022,
                             'hit_options': {
                                'task_sub_type': task_sub_type,
                            },
                             }}

    # shuffle the order of messages
    shuffle(messages)
    print 'total messages = %s' % len(messages)

    # start voting task on this experiment id, shuffle messages for the voting
    # task, make sure it works by testing it
    return start_task(task, task_type, init_conf, messages, ename)

def create_eval_task(messages, ename, task, task_type = 'eval_turk_rate_messages', task_sub_type="experts"):

    init_conf = {task_type: {'use_sandbox': use_sandbox,
                             'experiment_name': 'quality',
                             }}

    # shuffle the order of messages
    shuffle(messages)
    print 'total messages = %s' % len(messages)

    # start voting task on this experiment id, shuffle messages for the voting
    # task, make sure it works by testing it
    return start_task(task, task_type, init_conf, messages, ename)

from project1.controllers.RateMessages import EvalExpertRateMessages, EvalTurkRateMessages

use_sandbox = True
if __name__ == "__main__":
    # eval rating task
    messages = pd.read_json('/Users/gparuthi/Dropbox/UMICH/Projects/Timing/code/PCBC_MTURK_WebApp/ubicomp/eval/sim_messages.json').to_dict(orient='records')
    use_sandbox= True
    # tr, new_experiment = create_eval_task(messages, "evaluation_sim_experts",EvalExpertRateMessages)
    tr, new_experiment = create_eval_task(messages, "evaluation_sim_experts", task = EvalTurkRateMessages, task_type='eval_turk_rate_messages')
    # # rating task
    # use_sandbox= True
    # experiment_ids = [ObjectId('54e50a27a54d7528a154a4cc'), ObjectId('54ede067a54d753d2a8868c2')]
    # messages = [x for x in db.messages.find({'experiment_id':{'$in':[str(x) for x in experiment_ids]}})][:10]
    # for m in messages:
    #     if 'text' not in m:
    #         m['text'] = m['message']
    # tr, new_experiment = create_rating_task(messages, "kev_v5_ratingtest_motivational_messages", 'motivational')

    # clean task
    # rm_c = get_messages_in_clipboard_as_csv([ObjectId('5524ab3d281f59bae060ca28')], iscols=False, isdf=False)
    # create_clean_generate_task(rm_c)