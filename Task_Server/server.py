from datetime import datetime
import pytz
from flask import Flask, request, jsonify, render_template
from common.dbclient import db, client
import json
from common.logger import logger
from urllib2 import urlopen
from functools import wraps
from bson import json_util
import random
from models.Hit import HitInstance

from werkzeug.contrib.fixers import ProxyFix

from project1.controllers import TurkService as quality
# from task.ubi import ubi


import common.check_task_status as check_task_status
import redis
from rq import Queue
red = redis.Redis()
q = Queue(connection=redis.Redis())

# import common.mturk as mturk

''' Flask Server'''
app = Flask(__name__) 


def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f().data) + ')'
            return app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function


def get_header_ip():
    if request.headers.get("REMOTE_ADDR"):
        return request.headers.get('REMOTE_ADDR')
    else:
        return request.remote_addr


def record_actions(data):
    # logr.plog("Data: "+ json.dumps(data, default=json_util.default), class_name='action')
    # find task_type and operation
    data['__name__'] = __name__
    data['worker_ip'] = get_header_ip()
    if client:
        try:
            res = db.operations.insert(data)
            logr.debug("Successfully pushed a response to MongoDB. Document _id is %s." %
                      res, class_name='record_actions')
        except Exception as e:
            logr.warning("Couldnt push the response to DB. Exceptions: %s" %
                      e, class_name='record_actions')
    else:
        logr.error("Couldn't connect to MongoDB. Please check the connection.",
                  class_name='record_actions')


@app.route("/action", methods=['GET', 'POST'])
@support_jsonp
def action():
    if request.method == 'POST':
        print request.json
        task_type, operation, data = record_actions(request.json)
        return call_method(task_type, operation, data)
    return jsonify(foo="No post request")


@app.route("/submit", methods=['GET', 'POST'])
@support_jsonp
def submit():
    if request.method == 'POST':
        session_data = request.json
        record_actions(session_data)

        experiment_name = session_data['experiment_name']
        operation = session_data['operation']
        session_data['endTime'] = datetime.now(pytz.utc)
        data = session_data['data']

        response = {'worker_ip': get_header_ip()}
        for item in data:
            if item['name'] != '_id':
                response[item['name']] = item['value']
        # logr.plog("Clean Data: "+ json.dumps(response, default=json_util.default), class_name='submit')
        response['endTime'] = datetime.now(pytz.utc)

        if client:
            try:
                res = db.responses.insert(response)
                try:
                    HitInstance.objects.get(hit_id=response.get('hitId')).isSubmitted(worker_id=response.get('workerId'))
                except Exception as e:
                    print "HitInstance not found, hitId = %s"%response.get('hitId')
                logr.plog(
                    "Successfully pushed a response to MongoDB. Document _id is %s." % res, class_name='submit')
            except Exception as e:
                logr.error(
                    "Couldnt push the response to DB. Exceptions: %s" % e, class_name='submit')
        else:
            logr.error(
                "Couldn't connect to MongoDB. Please check the connection.", class_name='submit')

        session_data['data'] = response
        # try:
        #     q.enqueue(check_task_status.doWork, session_data)
        # except Exception as e:
        #     logr.warning("Problem with reqdis queue. Exceptions: %s" %
        #               e, class_name='submit')

        return call_method(experiment_name, operation, session_data)
    return jsonify(foo="No post request")


def call_method(experiment_name, operation, data):
    try:
        module = eval(experiment_name)
        # the module loading can be done in real time by using module
        # import_module. We will have to find a way map experiment_name to
        # module path
        method_name = getattr(module, operation)
        res = method_name(data)
        logr.debug("Successfully executed method: %s. Results is %s." %
                  (operation, res), class_name='call_method')
        return json_util.dumps({'foo': "Success!", 'result': res})
    except Exception as e:
        logr.error("Some exception occurred: %s" % e, class_name='call_method')
        logr.exception(e)
        return json_util.dumps({'foo': "Error!"})


@app.route("/")
def index():
    output = '''
    Test Server for research. Contact gparuthi [at] umich.edu if you have any questions.
    '''
    return output



@app.route("/writingtask" , methods=['GET', 'POST'])
def writingtask():
    hitids = [
            # '351S7I5UG987E8W3MC3TVFYBT14NJB', #John
            '35NNO802AV8BJXCX4UITJEJBGMFNIZ',
            '3P0I4CQYVYJB2DWEUQMLZUSOL7IWOU', # Grace
            '37AQKJ12TX0ZNOXSV2396KRCGLHTTN', #Mary
            '33N1S8XHHMXU0GUIZB8HM29Y9YCZ10' # Charles
            ]
    chosen_id = random.choice(hitids)
    ipadd = get_header_ip()
    url = 'http://intecolab.com:4999/get_hit?hitId=%s&assignmentId=%s_%s&workerId=%s'%(chosen_id, ipadd, random.randint(0,9), ipadd)
    output = '''
    <html><head><meta http-equiv="refresh" content="0;%s"></head></html>
    '''%url
    return output

@app.route("/evaltask" , methods=['GET', 'POST'])
def evaltask():
    # output = '''
    # Sorry about the inconvience. We are checking if there is a problem in submitting the HIT.
    # '''
    # return output
    assignment_id = request.args.get('assignmentId', 'NoAssignmentId')
    worker_id = request.args.get('workerId', 'NoWorkerId')

    hitids = [u'3S37Y8CWI8C7YKMWB67CLWMK3U54W8',
         u'38XPGNCKHTCUJVMRLW2GZU36WL34VY',
         u'3UDTAB6HH6BFN0RNZUAIV9OWOH409Y',
         u'3EGKVCRQFW4V8O255MZNE7D6OULYB6',
         u'39O0SQZVJNJZ9BNTEAVD19YD2HG7RS',
         u'3ZG552ORAMGKGH74HIJS6F68C772V0',
         u'3J5XXLQDHMN91Z3NLIXXPPB0IL6V33',
         u'3E9VAUV7BWQQPEXDZ8ZRJWT06C0YAB',
         u'30EV7DWJTV7P2CLA9VIF3RREATAY6L',
         u'36BTXXLZ2VK2QO5ACCX6YXE3BFQ4R5',
         u'38VTL6WC4APTJ8LW4C8ABLDEEYZY55',
         u'337F8MIIMZPEQULBIZERE1DG2PQ042',
         # u'3G3AJKPCXL4BNPHWQ7P06T70E24Y40',
         # u'3RBI0I35XEFQ5TYSQTKHWOFU028Y3F',
         # u'37MQ8Z1JQE81KB29MT6CDEA2UO8Y24',
         # u'3SMIWMMK61H6FIGBQCYUY0KE27SUWK',
         u'33N1S8XHHMXU0GUIZB8HM29Z8C0Z1H',
         u'341H3G5YF0QUTR903S4H8XQP3KUZ0E',
         u'31SIZS5W59R9FTS8A94J10F8779RQB',
         u'38RHULDV9YR16RLBWV9GFXW38C7WIG',
         u'3HXCEECSQM5RQM5LB0FQ0PK9FX9YZE',
         u'3UY4PIS8QRX0JRGZWNXNRF2QYYSN1O',
         u'3VCK0Q0PO5Q0C2VH04TNDAJGT6MN0L',
         u'3EPG8DX9LK2ZAUTVDPCRYUK2ATYP54',
         u'3OWZNK3RYL1K32I4CS9NAT4PY0ZU24',
         u'3MXX6RQ9EVHHEBPVZKTHT2EOAX3P4Z',
         u'3MQKOF1EE20KYG5P4H85O0GQG7ZWDE',
         u'33TGB4G0LPT6456C0C46VNCJSVTTXN',
         u'3A3KKYU7P3TN2AB2HA787Q3KPLRMWM',
         u'3SV8KD29L44W6HG47LEZRH5YHI0KZ5',
         u'3X52SWXE0XHATOZB4LDU4UY8V7NWCE',
         u'3QGHA0EA0JCRJJ75QLHZTASQDMNWB7']

    
    chosen_id = HitInstance.get_with_least_submits(hitids)

    return get_hit_html(chosen_id)

@app.route("/dummyIncentiveHit" , methods=['GET', 'POST'])
def dummyIncentiveHit():
    assignment_id = request.args.get('assignmentId', 'NoAssignmentId')
    worker_id = request.args.get('workerId', 'NoWorkerId')
    
    logr.plog('%s requested dummy hit'%worker_id)
    if worker_id in ['A38ZV8LBZ034IZ','A5N6QK76RTR7R','A2CGCAQA2IKLRV','APEQ60QNQ3WQT','ADTNOFJHTTB1L','A2R1JVEVFXAGUI','A28L1K6D8QUCML','A9KLWB70I12U7','APEQ60QNQ3WQT']:
        output =  render_template('dummy_hit.html',requirements={'use_sandbox': use_sandbox, 'worker_id': worker_id})
    else:
        output = """This HIT is only available to those participants who were unable to submit in HIT 3QREJ3J4339C1SZ0SKS8PYJ18NCKLY due to a bug. Please accept the HIT if the requester sent you this link."""
        output += " %s"%worker_id
    return output

@app.route("/evaltask2" , methods=['GET', 'POST'])
def evaltask2():
    assignment_id = request.args.get('assignmentId', 'NoAssignmentId')
    worker_id = request.args.get('workerId', 'NoWorkerId')

    hitids = [u'3XABXM4AJ1H3XODCB0YJAJK3FNOQ8F',
                u'3P7QK0GJ3TX1P1CEIF8VRLJ4YQHZ2F',
                u'3MA5N0ATTCNSCMBZWYUSSDBGYOZWK8',
                u'31ODACBENURLG8SLPY4ORAK4RHVSQH',
                u'3LN3BXKGC07NA0FG679DULJNR7IWG5',
                u'3CIS7GGG65VCYIUK5C4OCUDETBSUEN',
                u'3R0WOCG21ML76CGK9HT46CVTTZRUDU',
                u'3UY4PIS8QRX0JRGZWNXNRF2QW6W1NK',
                u'3VJ4PFXFJ3J985D8P722GBNN8WUUAS',
                u'3LCXHSGDLTIWJ52GG79OXTVQ8E7SE5',
                u'3MA5N0ATTCNSCMBZWYUSSDBGYOZKWW',
                u'391FPZIE4CYOISLMVDCUXXARLRKHUQ',
                u'3N5YJ55YXGFWDFTZS6QG2GVT001NAT',
                u'3G5RUKN2ECFI8WJU00CG6LK9UIJN9E',
                u'34ZTTGSNJX0WQZE5E4SPNWD2I6EHQL',
                u'3UYRNV2KITBIUR0KV8626PPYAC1N8P']

    workers_per_hit = 5

    hit_instances = HitInstance.objects(hit_id__in = hitids, loadedAndSubmitted__lt = workers_per_hit)

    if len(hit_instances) > 0:
        chosen_instance = random.choice(hit_instances)
        chosen_id = chosen_instance.hit_id
    else:
        print 'Can not find hit with loadedAndSubmitted__lt 5. Returning hit with least submits.'
        chosen_id = HitInstance.get_with_least_submits(hitids).hit_id

    
    return get_hit_html(chosen_id)

@app.route("/thanks" , methods=['GET', 'POST'])
def thanks():
    output = '''
    Thanks for helping out! Please do it <a href="/writingtask">again</a> if possible. 
    '''
    return output

@app.route('/get_hit', methods=['GET'])
def get_hit():
    hit_id = request.args.get('hitId', 'NoHitId')
    return get_hit_html(hit_id)

def get_hit_html(hit_id):
    assignment_id = request.args.get('assignmentId', 'NoAssignmentId')
    worker_id = request.args.get('workerId', 'NoWorkerId')
    
    start_time = datetime.now(pytz.utc)
    record_actions({'type': 'get_hit', 'workerId': worker_id,
                    'hitId': hit_id, 'assignmentId': assignment_id,
                    'startTime': start_time})

    try:
        HitInstance.objects.get(hit_id=hit_id).isLoaded(worker_id=worker_id)
    except Exception as e:
        print "HitInstance not found, hitId = %s"%hit_id
    

    logr.plog("HIT Requested: %s" %
              [assignment_id, worker_id, hit_id, start_time], class_name='get_hit')

    if hit_id != 'NoHitId':
        # get requirements for this HIT
        exp = db.hits.find_one({'hitId': hit_id})
        if 'requirements' in exp:
            requirements = exp['requirements']
            task_type = exp['task_type']
        else:
            requirements = {}
            logr.plog('Requirements or task_type not found',
                      class_name='get_hit')

        task_config = exp['task_config'][task_type]
        module = eval(task_config['experiment_name'])

        if 'task_path' in task_config:
            task_path = task_config['task_path']
        else:
            task_path = task_type + ".html"

        requirements['assignmentId'] = assignment_id
        requirements['hitId'] = hit_id
        requirements['workerId'] = worker_id
        requirements['startTime'] = start_time


        html = module.get_html(requirements, task_type, task_path)
        return html
    else:
        logr.error('get hit failed', class_name='get_hit')
    return 'Sorry, some error has occurred.'

@app.route('/unloaded', methods=['GET'])
def unloaded():
    hit_id = request.args.get('hitId', 'NoHitId')
    worker_id = request.args.get('workerId', 'NoHitId')
    try:
        HitInstance.objects.get(hit_id=hit_id).isUnLoaded(worker_id=worker_id)
    except Exception as e:
        print "HitInstance not found, hitId = %s"%hit_id
    return "hit unloaded"

@app.route('/get_ipinfo', methods=['GET'])
@support_jsonp
def get_ipinfo():
    ip = get_header_ip()
    response = json.loads(urlopen('http://ipinfo.io/%s/json' % ip).read())
    return jsonify(response)

use_sandbox = True

if __name__ == "__main__":
    logr = logger('./Logs', 'pcbc-mturk-dev', insertDate=False)
    app.run(host='0.0.0.0', port=4999, debug=True)
else:
    # init logger
    app.wsgi_app = ProxyFix(app.wsgi_app)
    logr = logger('./Logs', 'pcbc-mturk-server', insertDate=False)
    use_sandbox = False
