import time
import common.check_task_status
from bson import json_util, ObjectId

from common.dbclient import db

eids = [ObjectId('54d199961c96b944755936c2'),
 ObjectId('54d245d41c96b944755936d0'),
 ObjectId('54d275551c96b944755936de')]
while True:
    for e in eids:
        tasks = [t for t in db.tasks.find({'experiment_id':e, 'FINISHED':False})]
        for taskd in tasks:
            check_task_status.doWork({'data':taskd['hits'][0]})
    print'Sleeping now...'
    time.sleep(120)