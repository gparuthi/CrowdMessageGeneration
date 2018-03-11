import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ubicomp'))

from datetime import datetime
import pytz
from flask import Flask, url_for, request, session, redirect, render_template
from pymongo import DESCENDING
from dateutil import parser
from common.logger import logger
from functools import wraps
from bson import json_util
import numpy as np
import pandas as pd
from bson import ObjectId
import common.turk_utils as turk_utils
from random import randint

from werkzeug.contrib.fixers import ProxyFix
# from CrossDomain import crossdomain

import common.mturk as mturk

''' Flask Server'''
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

from common.dbclient import db


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

app = Flask(__name__)


@app.route("/")
def index():
    if 'token' not in session:
        output = '''
        Enter username:
        <form action="/signup" method="post">
          <input type="text" name="username"></input>
          <input type="submit" label="Submit"></input>
        </form>
        '''
        return output
    else:
        return redirect(url_for('show_info'))


# r = m.request("GetAccountBalance")
# if r.valid:
#     print r.get_response_element("AvailableBalance")

@app.route('/test', methods=['GET', 'POST'])
def test():
    assignmentId = request.args.get('assignmentId', 'NoAssignmentId')
    workerId = request.args.get('workerId', 'NoWorkerId')
    hitId = request.args.get('hitId', 'NoHitId')
    output = '''
    Test task:
    <form action="https://workersandbox.mturk.com/mturk/externalSubmit" method="post">
        <input type="hidden" id="assignmentId" name="assignmentId" value="{assignmentId}">
        <input type="hidden" id="hitId" name="hitId" value="{hitId}">
        <input type="hidden" id="workerId" name="workerId" value="{workerId}">
        <input type="hidden" id="mygroup" name="mygroup" value="<%=mygroup %>">
        <input type="text" name="q" value="test value"></input>
        <input type="submit" label="Submit"></input>
    </form>
    '''.format(assignmentId=assignmentId, workerId=workerId, hitId=hitId)
    return output

# @app.route('/get_hits')
# def get_hits_default():
#     return redirect(url_for('get_hits', sandbox_flag=False))


@app.route('/get_hits', methods=['GET'])
def get_hits():
    sandbox_flag = request.args.get('sandbox_flag', 'False')
    conf = {
        "use_sandbox": eval(sandbox_flag),
        "stdout_log": False,
        "verify_mturk_ssl": True,
        "aws_key": "AKIAJLJ5F2MLV36GZKAA",
        "aws_secret_key": "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"
    }

    m = mturk.MechanicalTurk(conf)
    # get all hits
    hits = []
    r = m.request(
        "SearchHITs", {'SortDirection': 'Descending', 'PageSize': 100})
    total_hits = int(
        r[u'SearchHITsResponse'][u'SearchHITsResult'][u'TotalNumResults'])
    # hits = [(x['CreationTime'],x['HITId'],x['NumberOfAssignmentsCompleted'])
    # for x in r['SearchHITsResponse']['SearchHITsResult']['HIT']]#[:20]
    pgno = 0

    while len(hits) < 20:
        pgno += 1
        r = m.request("SearchHITs", {
                      'SortDirection': 'Descending', 'PageSize': 100, 'PageNumber': pgno})
        try:
            hits.extend([(x['CreationTime'], x['HITId'], x['NumberOfAssignmentsCompleted'])  # , x['RequesterAnnotation'])
                         for x in r['SearchHITsResponse']['SearchHITsResult']['HIT']])
        except Exception as e:
            print 'some error on page %s: %s' % (pgno, e)
            break
        break
        # time.sleep(1)
    print 'Total HITs', len(hits)
    alldata = []
    for hit in hits[:20]:
        try:
            hitd = db.hits.find_one({'hitId': hit[1]}, {'_id': False})
            output = '<div style="overflow:auto; height:40px; width:300px;"><pre><code class="prettyprint">{hitr}</pre></code></div>'.format(
                hitr=json_util.dumps(hitd, indent=4))
            alldata.append({
                'task_type': hitd.get('taskType', 'NA'),
                'shortname': '%s | %s' % (hitd['requirements'].get('persona', 'NA'), hitd['requirements'].get('shortname', 'NA')),
                'task_title': hitd['requirements'].get('task_title', 'NA'),
                'hitId': hit[1],
                'CreationTime': hit[0],
                'Assignments': hit[2],
                'hitURL': '<a href="%s">Link</a>' % hitd.get('url', 'NA'),
                'hit_json': output,
            })
        except:
            alldata.append({
                'task_type': 'Not Found',
                'hitId': hit[1],
                'CreationTime': hit[0],
                'Assignments': hit[2],
                'hitURL': 'Not Found',
                'hit_json': 'Not Found'
            })

    return render_template('hits.html', data=alldata)


def check_key(key, query, defaultr= False):
    if key in query:
        defaultr = query[key]
        del query[key]
    return defaultr


@app.route('/get/<collection>', methods=['GET'])
def get_documents(collection):
    mongo_collection = db[collection]
    query = dict(request.args.items())
    print 'query:', query

    logr.plog("Received request: %s" % query, class_name='get/collection')
    projd = {'_id': False}
    sortd = [('_id', -1)]

    isjson = check_key('json', query, True)
    lastn = int(check_key('lastn', query, 10))

    if 'proj' in query:
        nd = dict([(x, True) for x in query['proj'].split(',')])
        print nd
        projd.update(nd)
        del query['proj']

    if 'sort' in query:
        nd = [(x, DESCENDING) for x in query['sort'].split(',')]
        print nd
        sortd = nd
        del query['sort']

    

    alldata = [x for x in mongo_collection.find(
        query, projd).sort(sortd).limit(lastn)]

    print "found = ", len(alldata)

    if isjson: 
        return json_util.dumps({'data': alldata})
    else:
        fin_data = []
        for r in alldata:
            nr = {}
            for d in r:
                if type(r[d]) == unicode:
                    nr[d] = r[d]
            fin_data.append(nr)
        return render_template('hits.html', data=fin_data)


@app.route('/get_results', methods=['GET'])
def get_results():
    query = dict(request.args.items())
    logr.plog("Received request: %s" % query, class_name='get_results')
    if 'json' in query:
        isjson = query['json']
        del query['json']
    if 'lastn' in query:
        lastn = int(query['lastn'])
        del query['lastn']
    else:
        lastn = 10

    alldata = [x for x in db.responses.find(
        query, {'_id': False}).sort('_id', -1).limit(lastn)]

    if isjson:
        return json_util.dumps({'data': alldata})
    else:
        return render_template('hits.html', data=alldata)
# app.secret_key = _keys.client_secret


@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    query = dict(request.args.items())
    logr.plog("Received request: %s" % query, class_name='get_tasks')
    if 'json' in query:
        isjson = query['json']
        del query['json']
    else:
        isjson = False
    if 'lastn' in query:
        lastn = int(query['lastn'])
        del query['lastn']
    else:
        lastn = 10

    projd = []
    if 'proj' in query:
        projd = [(x) for x in query['proj'].split(',')]
        del query['proj']

    if 'experiment_id' in query:
        query['experiment_id'] = ObjectId(query['experiment_id'])

    alldata = []
    for x in db.tasks.find(query).sort('_id', -1).limit(lastn):
        rec = get_task_info(x, query)
        if rec:
            for t in projd:
                del rec[t]
            alldata.append(rec)
    if isjson:
        return json_util.dumps({'data': alldata})
    else:
        return render_template('hits.html', data=alldata)


def get_time(timeob):
    if type(timeob) == datetime:
        return timeob.replace(tzinfo=None)
    if type(timeob) == str or type(timeob) == unicode:
        return parser.parse(timeob).replace(tzinfo=None)

    raise Exception


def get_task_info(x, query={}):
    n_hits = len(x['hits'])
    n_ass_perhit = x.get('max_assignments', 10)
    n_additional_assignment = 0
    ret = []
    times = []
    for h in x['hits']:
        query['hitId'] = h['hitId']
        n_additional_assignment += h.get('additional_assignments', 0)
        ret.extend([r for r in db.responses.find(query)])
        times.extend([((r['endTime'] - get_time(r['startTime'])).seconds if 'endTime' in r else 0)
                      for r in db.responses.find(query)])
    # print x
    thits = x.get('hits')
    if len(thits) == 0:
        return {}
    cost = float(x.get('total_cost')) / len(thits) / int(x['max_assignments'])
    rec = {
        'id': x.get('task_type', 'NA'),
        'taskid': x.get('taskid', 'NA'),
        'experiment_id': str(x.get('experiment_id', 'NA')),
        'Finished': x.get('FINISHED', 'NA'),
        'submit_to': 'Sandbox' if x['use_sandbox'] else 'Turk',
        'Assignments': n_ass_perhit * n_hits + n_additional_assignment,
        'AComp': len(ret),
        'AAvail': x.get('NumberOfAssignmentsAvailable', 'NA'),
        'APend': x.get('NumberOfAssignmentsPending', 'NA'),
        'Avg Hourly Cost': '$%.2f' % (cost / np.mean(times) * 60 * 60),
        'Median Hourly Cost': '$%.2f' % (cost / np.median(times) * 60 * 60)
    }

    rec['desc'] = thits[0].get('desc', '|').split('|')[1]
    rec['url'] = thits[0].get('url', '')
    return rec


def get_desc(e):
    t = e['tasks']
    if len(t) > 0:
        hit = t[0]['hits']
        if len(hit) > 0:
            return hit[0]['desc']


def get_count(c, experiment_id):
    if c == 'tasks':
        return db[c].find({'orig.experiment_id': ObjectId(experiment_id)}).count()
    return db[c].find({'orig.experiment_id': experiment_id}).count()


def get_html(taskd):
    html = '<p>CreateTime: %s | Experiment ID: %s</br> | Task Id: %s | Finished: %s </p>'%(taskd['createTime'], taskd['experiment_id'], taskd['task_type'], taskd['FINISHED'])
    for d in taskd['hits']:
        url = '%s&assignmentId=test%s'%(d['url'],randint(1,999999))
        html += """<a href=%s target='_blank'> %s | %s | %s</a> <br />"""%(url, 
                                                                           'Sandbox' if taskd['use_sandbox'] else 'Turk',
                                                                           taskd['task_type'],taskd.get('hit_options',{}).get('task_sub_type','NA'))
        html += "<a href='#' onClick='unit_test_%s()'>Test</a>"%d['hitId']
        
    html += """<a href='%s' target='_blank'> | Amazon HITS search</a> <br />"""%('https://www.mturk.com/mturk/searchbar?selectedSearchType=hitgroups&searchWords=gaurav&minReward=0.00&x=0&y=0')
    html += "total cost= %s for %s hits"%(taskd.get('total_cost','NA'), len(taskd['hits']))
    return html

@app.route('/last_tasks', defaults={'count': 15})
@app.route('/last_tasks/<count>', methods=['GET'])
def last_tasks(count=15):
    tasks = [x for x in db.tasks.find().sort('_id',-1).limit(int(count))]
    # print [x for x in tasks]
    html = "</br> ".join([get_html(t) for t in tasks])
    
    return html

@app.route('/last_experiments', defaults={'count': 15})
@app.route('/last_experiments/<count>', methods=['GET'])
def last_experiments(count=15):
    q = {}#{'use_sandbox':False}
    experiments = [x for x in db.experiments.find(q).sort('_id',-1).limit(int(count))]
    html = "</br> ".join(['{date} | {2} | <a class="link" href="/get_experiment?eids={0}">{0} | {1}</a>'.format(str(exp['_id']), get_desc(exp), exp.get('use_sandbox'),date=exp.get('createTime')) for exp in experiments])
    
    return html

@app.route('/get_experiment', methods=['GET'])
def get_experiment():
    query = dict(request.args.items())
    title = query.get('title', '').strip()
    use_sandbox = eval(query.get('use_sandbox', 'True').strip())
    experiments = [x for x in db.experiments.find(
        {'use_sandbox': {'$in': [use_sandbox, False]}}).sort('_id', -1).limit(10)]
    last_sessions  = db.session.find().sort('_id',-1).limit(10)

    eids = query.get('eids')
    if eids:
        eids = eids.split(',')
    else:
        last_session  = last_sessions[0]
        url = '/get_experiment?eids=%s'%(','.join(last_session['experiment_ids']))
        output = '''
        <html><head><meta http-equiv="refresh" content="0;%s"></head></html>
        '''%url
        return output
        
    tasks = {}
    for eid in list(eids):
        ts = [x for x in db.tasks.find(
            {'experiment_id': ObjectId(eid), 'use_sandbox': {'$in': [use_sandbox, False]}})]
        if not ts:
            print 'removing | ' + eid
            eids.remove(eid)
            continue
        tasks[eid] = ts
        for taskd in tasks[eid]:
            taskd.update(get_task_info(taskd))
            # find endtime
            try:
                end_time = db.responses.find(
                    {'experiment_id': eid}).sort('_id', -1)[0]['endTime']
                taskd['duration'] = end_time - taskd['createTime']
            except:
                taskd['duration'] = datetime.now(pytz.utc).replace(
                    tzinfo=None) - taskd['createTime']
    getc = get_count

    responses = [x for x in db.responses.find(
        {'experiment_id': {'$in': eids}}).sort('_id', -1)]
    if len(responses)>0:
        df = pd.DataFrame(responses)
        worker_dist = df.workerId.value_counts().to_dict()

    # experiment ids
    exp_ids = [(str(e['_id']), get_desc(e)) for e in experiments]

    bad_votes = [x for x in db.bad_votes.find(
        {'experiment_id': {'$in': eids}}).sort('_id', -1)]
    if len(bad_votes) > 0:
        df = pd.DataFrame(bad_votes)
        
        bad_workers = df.workerId.value_counts().to_dict()
        for w in bad_workers:
            bad_workers[w] = {'bad': bad_workers[w]}
            bad_workers[w]['badass'] = [x['assignmentId']
                                        for x in bad_votes if x['workerId'] == w]
            bad_workers[w]['all'] = db.responses.find({'workerId': w}).count()

    return render_template('experiment.html', **locals())


@app.route('/utils/<op>', methods=['GET'])
def utils(op):
    query = dict(request.args.items())
    # aid = query.get('aid',False)#.strip()
    # f = getattr(turk_utils,op)
    # raise
    res = turk_utils.gen_operation(op, query)
    # if not aid:
    #     res = f()
    # else:
    #     res = f(aid)
    return json_util.dumps(res)

if __name__ == "__main__":
    logr = logger('./Logs', 'pcbc-mturk-analysis-dev')
    app.run(host='0.0.0.0', port=4998, debug=True)
else:
    # init logger
    logr = logger('./Logs', 'pcbc-mturk-analysis-server')
