from pymongo import MongoClient
import mongoengine

def findl(c,q={}):
	return c.find(q).sort('_id',-1)[0]

DB_NAME = "pcbc_mturk"

mongoengine.connect(DB_NAME)

# db.experiments.ensure_index('hitId', unique= True,dropDups = True)
# db.tasks.ensure_index('id', unique= False)
# db.responses.ensure_index('assignmentId', unique= True, dropDups = True)
# db.messages.ensure_index('id', unique= True, dropDups = True)
# db.worker_ratings.ensure_index('id', unique= True, dropDups = True)
# db.worker_locations.ensure_index('workerId', unique= True, dropDups = True)

client = None 
db = None

'''Mongo Connection'''
try:
    client = MongoClient()
    #use the test database
    db = client[DB_NAME]
except Exception as e:
    print "Mongo connection error %s"%e