import project1.controllers.pipeline as pipeline
import pandas as pd
import ipdb
from common.dbclient import db, client
from datetime import datetime
import pytz
import project1.tests.unit_test as ut
from random import shuffle

pipeline.use_sandbox = False

if __name__ == "__main__":
      
## Uncomment the lines corresponding to the task you would like to begin

# # Generate Messages
#   personas = ["Charles","Jose","Mary","Grace","John"]

#   shuffle(personas)

#   ### Generate Task ###
#   eids = []
#   for p in personas:
#     pipeline.exp = pipeline.get_new_experiment()
#     print '**** GENERATE TASK | %s | %s ****'%(p, pipeline.exp.exp_id)
#     task, exp = pipeline.create_generate_task(persona=p)
#     eids.append(str(pipeline.exp.exp_id))

#   if client:
#     db.session.insert({'experiment_ids': eids, 'datetime':str(datetime.now(pytz.utc))})

#   print eids
#     # ipdb.set_trace()
#     # print [x['url'] for x in task.get_taskd()['hits']]
  
#   print "Analytics can be found here: http://intecolab.com:4998/get_experiment?eids=%s"%(','.join(eids))
#   # ### End Generate ###

#   ## Rate Task ###
#   experiment_ids = [['5606f5cba54d75603cc403c2','5609acbb5ea22a13c556e463'],
# ['5606f5cea54d75603cc403c5','5609acba5ea22a13c556e45d'],
# ['5606f5cfa54d75603cc403c8','5609acba5ea22a13c556e460'],
# ['5606f5d0a54d75603cc403cb','5609acb75ea22a13c556e457'],
# ['5606f5d1a54d75603cc403ce','5609acb95ea22a13c556e45a']]
#   shuffle(experiment_ids)
#   for eid_group in experiment_ids:
#     # exp = pipeline.get_experiment(eid)
#     print '**** Rating  ****'
#     # print exp
#     task, experiment = pipeline.create_rating_task(eid_group) 
#     # pipeline.create_rating_task([eid]) 
#     # ipdb.set_trace()
#   print 'Rating Experiment started at ',experiment.exp_id

#   ## End Rate Task ###

  # print '**** Aggregate Ratings ****'

  # ut.aggregate_ratings()

    # EVAL TASKS: rating task
    # messages = pd.read_json('/Users/gparuthi/Dropbox/UMICH/Projects/Timing/code/PCBC_MTURK_WebApp/ubicomp/eval/sim_messages.json').to_dict(orient='records')

    # tr, new_experiment = create_eval_task(messages, "evaluation_sim_experts",EvalExpertRateMessages)
    # tr, new_experiment = pipeline.create_eval_task(messages)
    # tr, new_experiment = pipeline.create_eval_task(messages, task=pipeline.EvalExpertRateMessages, task_type='rating_quality')
    
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
