import common.mturk as mturk
from datetime import datetime
import pytz
import math
from common.dbclient import db
import config

hostname = "intecolab.com"

def get_hostname(port):
  if port==4999:
    return "http://%s:%s"%(hostname,port)
  else:
    return "https://%s:%s"%(hostname,port)

def get_mturk_conf(use_sandbox=True):
    requester_conf = {
        "use_sandbox" : use_sandbox,
        "stdout_log" : False,
        "verify_mturk_ssl" : False,
        "aws_key" : config.AWS_KEY,
        "aws_secret_key" : config.AWS_SECRET_KEY
    }
    print requester_conf
    return requester_conf

def get_balance(use_sandbox=False):
    requester_conf = get_mturk_conf(use_sandbox)
    r = mturk.MechanicalTurk(requester_conf).request("GetAccountBalance")
    if r.valid:
        return r.get_response_element("AvailableBalance")

def get_question(config):
    url = '%s/get_hit'%(get_hostname(5000))
    return """<?xml version="1.0" encoding="UTF-8"?>
        <ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
          <ExternalURL>%s</ExternalURL>
          <FrameHeight>800</FrameHeight>
        </ExternalQuestion>
    """%url

def get_hit_incentive(task_config):
  return task_config['hit_options']['message_count_per_hit']*task_config['per_message_incentive']

def create_hit(hit_config, task_config):
    m = mturk.MechanicalTurk(get_mturk_conf(task_config['use_sandbox']))
    description = task_config['title']
    keywords = 'idea, message, text, walking, support, help, physical, activity'
    # v = task_config['incentive']
    v = get_hit_incentive(task_config)
    amt = math.ceil(v*100)/100
    reward = {'Amount':amt, 'CurrencyCode':'USD'}
    duration= 60*20
    autoapp = 60*60*48

    question= get_question(task_config)
    lifetime = 60*60*24
    max_assignments = task_config['max_assignments']
    qualification_req = [{"QualificationTypeId":"000000000000000000L0",
                                "IntegerValue":98,
                                'Comparator':'GreaterThan'},{"QualificationTypeId":"00000000000000000040",
                                "IntegerValue":1000 if task_config['use_sandbox']==False else 1,
                                'Comparator':'GreaterThan'},
                                {"QualificationTypeId":"00000000000000000071",
                                'Comparator':'EqualTo', 'LocaleValue':{'Country':'US'}},
                                ]

    task_type_conf = {'Title': task_config['title'], 
                               'Description' :description, 
                               'MaxAssignments': max_assignments,
                               'Keywords':keywords, 
                               'Reward':reward, 
                               'RequesterAnnotation':task_config.get('taskid'),
                               'AssignmentDurationInSeconds':duration, 
                               'AutoApprovalDelayInSeconds': autoapp,
                               'Question': question,
                               'LifetimeInSeconds': lifetime,
                               'QualificationRequirement': qualification_req
    }


    r = m.request("CreateHIT",task_type_conf)
    try: 
      print 'HITId: %s'%r['CreateHITResponse']['HIT']['HITId']
    except:
      print 'Some problem. AWS Response: %s'%r 
    
    hitid = r[u'CreateHITResponse'][u'HIT'][u'HITId']
    hit_typeid = r[u'CreateHITResponse'][u'HIT'][u'HITTypeId']
    create_time = datetime.now(pytz.utc)
    requirements = { 
                'task_id': task_config.get('task_id','task_id'),
                'experiment_id': task_config.get('experiment_id','experiment_id'),
                'task_type': task_config['task_type'],
                'use_sandbox': task_config['use_sandbox'],
                'max_assignments': task_config['max_assignments']
            }
    
    requirements.update(hit_config)
    d= {'hitId':hitid, 
        'createTime': create_time,
        'hitTypeId': hit_typeid, 
        'task_type': task_config['task_type'],
        'experiment_id': task_config.get('experiment_id','experiment_id'),
        'task_id': task_config.get('task_id',''),
        'url':  '%s/get_hit?hitId=%s'%(get_hostname(task_config['port']), hitid),
        'requirements': requirements,
        'task_type_conf': task_type_conf,
        'task_config': task_config,
        'additional_assignments': 0,
        'shortname': task_config.get('shortname', 'NA')
        }
    
    return d

def extend_hit_assignments(hitid, count):
    m = mturk.MechanicalTurk(get_mturk_conf(False))
    r = m.request("ExtendHIT",
              {'HITId': hitid, 
               'MaxAssignmentsIncrement':count
               })
    print r
    return r

def reject_assignment(assignmentId):
    m = mturk.MechanicalTurk(get_mturk_conf(False))
    r = m.request("RejectAssignment",
              {
               'AssignmentId': assignmentId, 
               'RequesterFeedback': 'Sorry, You failed to rate correctly on our verification message. Please read the instructions carefully next time. More information can be found at https://goo.gl/QAkHaJ. Please contact the requester for more information.'
            })
    print r
    return r

def approve_rejected_assignment(assignmentId):
    m = mturk.MechanicalTurk(get_mturk_conf(False))
    r = m.request("ApproveRejectedAssignment",
              {
               'AssignmentId': assignmentId, 
               'RequesterFeedback': 'Approving some rejected assignments just this time.'
            })
    print r
    return r

def block_worker(workerId):
    if db.blocked_workers.find_one({'WorkerId':workerId}):
        return {'msg':'already blocked', 'workerId':workerId}
    m = mturk.MechanicalTurk(get_mturk_conf(False))
    q= {
            'WorkerId': workerId, 
            'Reason': 'Task was not completed properly. Rating of messages was found to be inappropriate: you failed to vote correctly on our verification messages.'
               }
    db.blocked_workers.insert(q)
    r = m.request("BlockWorker",
              q)
    print r
    return r


def gen_operation(op,q):
    # if db.unblocked_workers.find_one({'WorkerId':workerId}):
        # return {'msg':'already blocked', 'workerId':workerId}
    m = mturk.MechanicalTurk(get_mturk_conf(False))
    # q= {
    #         'WorkerId': workerId, 
    #         'Reason': 'Task was not completed properly. Rating of messages was found to be inappropriate: you failed to vote correctly on our verification messages.'
    #            }
    # db.insert(q)
    r = m.request(op,q)
    print r
    return r

def grant_bonus(assignmentId, amt, reason):
    worker_id = db.responses.find_one({'assignmentId':assignment_id}).get('workerId')
    m = mturk.MechanicalTurk(get_mturk_conf(False))
    r = m.request("GrantBonus",
              {
               'AssignmentId': assignmentId, 
               'WorkerId':worker_id,
               'BonusAmount': {'Amount':amt, 'CurrencyCode':'USD'},
               'Reason':reason
            })
    print r
    return r