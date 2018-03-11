import common.mturk as mturk
import common.task_utils as task_utils
from common.logger import logger
from bson import ObjectId
import traceback
import time
from datetime import datetime
import pytz
from common.dbclient import db


logr = logger('./Logs','check_status_task', insertDate=False)
# logr.plog("Checking status...")

conf_turk = {
"use_sandbox" : False,
"stdout_log" : False,
"verify_mturk_ssl" : True,
"aws_key" : "AKIAJLJ5F2MLV36GZKAA",
"aws_secret_key" : "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"
}
conf_sbox = {
"use_sandbox" : True,
"stdout_log" : False,
"verify_mturk_ssl" : True,
"aws_key" : "AKIAJLJ5F2MLV36GZKAA",
"aws_secret_key" : "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"
}

m_Turk = mturk.MechanicalTurk(conf_turk)
m_sandbox = mturk.MechanicalTurk(conf_sbox)

# r = m_Turk.request("GetAccountBalance")
# if r.valid:
#     print r.get_response_element("AvailableBalance")


def doWork(response, timeout=60):
    print 'sleeping for %d seconds'%timeout

    # add timeout
    time.sleep(timeout)
    # logr.plog("Received request: %s"%data)
    data = response['data']

    # Update last n HITs' satus HITs status 
    UpdateAllHITS()
    
    # get HITId
    hitId = data['hitId']
    
    # get taskd for this HIT
    taskd = get_hit_taskd(hitId)

    # if the task is not finished yet then get updated taskd and check if its finished
    if taskd.get('FINISHED', False) == False:
        new_taskd = get_hit_updated_taskd(hitId)
        if new_taskd:
            if new_taskd.get('FINISHED',False) == True:
                start_next_task(new_taskd) # task is finished, trigger its end and start the next task

def UpdateAllHITS():
    # get all hits and update db
    hits = get_hits(m_Turk)
    hits.extend(get_hits(m_sandbox))
    # get balance
    r = m_Turk.request("GetAccountBalance")
    if r.valid:
        print r.get_response_element("AvailableBalance")

    logr.plog("Adding HITS from API to mongodb")
    # put hits in mongodb
    for h in hits:
        taskd = db.api_hits.find_and_modify({'HITId':h['HITId']},
                                            h, upsert=True, new=True)
    logr.plog("Updated/Added %s hits"% len(hits))

def start_next_task(taskd):
    logr.plog("Triggering the end of this task!")
    ec.experiment_task_finished(taskd)

def get_hits(m):
    r = m.request("SearchHITs",{'SortDirection':'Descending','PageSize':50})
    hits = []
    try:
        hits.extend([x for x in r['SearchHITsResponse']['SearchHITsResult']['HIT']])
    except:
        print 'some error while retrieving HITS'
    return hits

def get_hit_taskd(hitId):
    try:
        tid = db.hits.find_one({'hitId':hitId})['task_id']
        return get_current_taskd(tid)
    except Exception as e:
        print 'problem in getting task info: %s'%e 
        traceback.print_stack()
def get_current_taskd(tid):
    try:
        # ipdb.set_trace()
        taskd = db.tasks.find_one({'_id':tid})
        print 'Current Taskd '
        print 'Task: NumberOfAssignmentsAvailable = ', taskd.get('NumberOfAssignmentsAvailable','NA')        
        print 'Task: NumberOfAssignmentsCompleted = ', taskd.get('NumberOfAssignmentsCompleted','NA')        
        print 'Task: NumberOfAssignmentsPending = ', taskd.get('NumberOfAssignmentsPending','NA')
        
        return taskd
    except Exception as e:
        print 'problem in getting task info: %s'%e 
        traceback.print_stack()

def get_hit_updated_taskd(hitId):
    try:
        tid = db.hits.find_one({'hitId':hitId})['task_id']
        return get_updated_taskd(tid)
    except Exception as e:
        print 'problem in updating task info: %s'%e 
        traceback.print_stack()

def get_updated_taskd(tid):
    print 'getting updated task for task_id: %s'%tid
    try:
        taskd = db.tasks.find_one({'_id':ObjectId(tid)})
        taskd['NumberOfAssignmentsAvailable'] = 0 
        taskd['NumberOfAssignmentsCompleted'] = 0 
        taskd['NumberOfAssignmentsPending'] = 0 
        for hd in taskd['hits']:
            hid =hd['hitId']
            h = db.api_hits.find_one({'HITId':hid})
            hd['NumberOfAssignmentsAvailable'] = h['NumberOfAssignmentsAvailable']
            hd['NumberOfAssignmentsCompleted'] = h['NumberOfAssignmentsCompleted']
            hd['NumberOfAssignmentsPending'] = h['NumberOfAssignmentsPending']
            taskd['NumberOfAssignmentsAvailable'] += int(h['NumberOfAssignmentsAvailable'])
            taskd['NumberOfAssignmentsCompleted'] += int(h['NumberOfAssignmentsCompleted'])
            taskd['NumberOfAssignmentsPending'] += int(h['NumberOfAssignmentsPending'])
        
        print 'Updated Task: %s | %s'% (taskd['task_type'], taskd['_id'])
        print 'Task: NumberOfAssignmentsAvailable = ', taskd['NumberOfAssignmentsAvailable']        
        print 'Task: NumberOfAssignmentsCompleted = ', taskd['NumberOfAssignmentsCompleted']        
        print 'Task: NumberOfAssignmentsPending = ', taskd['NumberOfAssignmentsPending']
        
        if (taskd['NumberOfAssignmentsAvailable'] + taskd['NumberOfAssignmentsPending'] == 0):
            taskd['FINISHED'] = True
            taskd['endTime'] = datetime.now(pytz.utc)
        else:
            taskd['FINISHED'] = False
        db.tasks.save(taskd)
        logr.plog("Updated task: %s"%(taskd))
        return taskd
    except Exception as e:
        print 'problem in updating task info: %s'%e 
        traceback.print_stack()
