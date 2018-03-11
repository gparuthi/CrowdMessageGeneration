from pymongo import * 
from datetime import datetime
import pandas as pd
import common.turk_utils as turk_utils
import numpy as np
from random import randint
from bson import ObjectId
import math
from common.dbclient import db
from models.Hit import HitInstance
import ipdb

def shuffle_hits(finalhits_df):
    df = finalhits_df.reset_index(drop=True)
    fin_df = df.reindex(np.random.permutation(df.index))[:]
    # print 'All HITS::'
    for s in fin_df.to_dict(outtype='records'):
        # print s
        print 'Shuffle HITS | %s'%(s['shortname'])
    print '----'
    tdf = fin_df.copy()
    # tdf['sit_per_id'] = tdf.persona + '_' + tdf.shortname
    # perm_inc = 0.02
    # tdf['message_count_per_hit'] = fin_df.messages.apply(lambda x: len(x))
    # tdf['total_inc'] = fin_df.messages.apply(lambda x: len(x)*perm_inc*5)
    #tdf.shortname.value_counts()#groupby('sit_per_id').size() #.groupby('persona').suma()
    return tdf

def add_task_exp(exp_id, task, task_id, task_hits, task_createTime):
    res = db.experiments.find_and_modify({'_id':exp_id},{'$addToSet': {'tasks': {'task_type':task, 'hits':task_hits, 'task_id':task_id, 
        'createTime':task_createTime}}}, upsert=True, new=True)
    return res

def create_task(task_config, finalhits):
    taskd = task_config.copy()
    taskd.update({'hits':[]})
    print 'TITLE:%s'% task_config['title']
    tot_cost = 0

    #insert task into task collection
    task_id = db.tasks.insert(taskd)

    task_config['task_id']= task_id

    print 'Total hits found= %s'% len(finalhits)
    for idx, r in enumerate(finalhits):
        desc = '%s | %s'%(taskd['task_type'],r.get('shortname','shortname'))

        if 'messages' in r:
            task_config['message_count_per_hit']= len(r['messages'])

        # cost_for_hit = task_config['incentive']*task_config['max_assignments']
        cost_for_hit = turk_utils.get_hit_incentive(task_config)*task_config['max_assignments']
        cost_for_hit = math.ceil(cost_for_hit*100)/100

        print '%s | Cost for hit=%s | '%((idx+1), cost_for_hit), desc,
        tot_cost+=cost_for_hit

        hit_config = r
        d = turk_utils.create_hit(hit_config, task_config)
        d['cost'] = cost_for_hit

        db.hits.save(d)

        HitInstance(hit_id=d['hitId']).save()

        taskd = db.tasks.find_and_modify({'_id':task_id},
                                            {'$addToSet': {'hits': {'hitId':d['hitId'], 'desc': desc, 'url':d['url']}},
                                             '$inc': {'number_of_hits':1},
                                             '$inc': {'max_assignments':task_config['max_assignments']},
                                             '$inc': {'total_cost':cost_for_hit}
                                             },
                                            upsert=True, new=True)
    # add task to experiment doc in mongodb 
    add_task_exp(task_config['experiment_id'], task_config['task_type'], taskd['_id'], taskd['hits'], task_config['createTime'])
    print 'total_cost = %s'%tot_cost
    print 'Balance Left = $%s'%turk_utils.get_balance(task_config['use_sandbox'])['Amount']
    return taskd
