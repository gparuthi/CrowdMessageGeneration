PCBC Technical Documentation
===
Author: Gaurav Paruthi
Date Created: 1/23/15

Requirements
---
1. Python and Libraries:
	- Pandas, [Flask](http://flask.pocoo.org/), pymongo, rqueue
2. MongoDB
3. Redis server and [Python-rq](http://python-rq.org/ "python-rq") for asynchronous and future scalability
4. [minimongo](https://github.com/slacy/minimongo.git)


All the controllers directly related to a given subproject are stored with the experiments directory. For example, for the first project, the "Task1" directory contains all the controllers for submiting, templates, on get_html, unittests/simulations, etc.
Within Project1

The bakeoff contains the pipeline and expert/turk evaluation tasks. The pipeline is a bit different as multiple personas can be used here.


Modules
---
| Name     | Description |
| :-------------- | :-------------------- |
| server.py | Runs the flask server|
| experiment_controller.py    | Defines an experiment and code for the tasks   |
| check_task_status.py     | Polls the task status on mturk. If finished then triggers the next step of the task. |
| comomon/mturk.py     | Mturk API code from ThirdParty.    |
| common/task_utils.py     | Helper methods for experiment_controller.    |
| common/turk_utils.py     | Helper methods for turk related stuff.  |
| common/logger.py     | Helper logging methods.  |
| models/*    | Models for the data objects used  |
| Task1/controllers/*    | Classes that controll task start and end  |
| Task1/spec/*    | Specs for the different tasks  |
| Task1/templates/*    | HTML templates for the generate, rate, grammar task  |


Flow Diagram
---
```sequence
participant Me
participant rq
participant MongoDb
participant Flask
participant Mturk
participant Turker
participant CheckStatus

Me-->CheckStatus: Start Process
Note over CheckStatus: Polls Turk status every minute. \nTriggers rq.
Note over Me: 1. Create the spec.\nCreate experiment\n Generate_task 
Me-->MongoDb: store HIT details
Me->Mturk: Create HIT
Mturk->Turker: 2. Open generate task
Turker-->Flask: query
Flask->Turker: Show HTML
Turker->Flask: 3. Submit
Flask-->MongoDb: store 'messages'

Note over CheckStatus: Check if generate_task is finished
Note over rq: 4. Create Rate_task
Me-->MongoDb: rate_messages_input and store HIT detail
Me->Mturk: Create HIT
Mturk->Turker: 5. Open rate task
Turker-->Flask: query
Flask->Turker: Show HTML
Turker->Flask: 6. Submit
Flask-->MongoDb: store in 'message_ratings'

rq->MongoDb: 7. Aggregate into rated_messages

```

Collections used
---

misc
    studies: to manually store all the group of experiments I am running like Project1
    responses: for all submitted results
    operations: all operations performed including duplicate submissions, clicks (future), etc.
    
generate_tips

    messages
    
rate_messages

    ratemessages_input
    message_votes
    rated_messages
    ratesetmessages_input
    worker_ratings : for calculation of zscores
    
rate_set

    ratesetmessages_input
    rateset_inputsets
    rated_sets
    rateset_output
    setmessage_votes
    rated_setmessages
    
logging
    
    db.log
    
bad_responses

    db.bad_votes
    db.blocked_workers
    db.worker_locations: older ip addreses and workerIds 


Ensure Indices:
---
db.experiments.ensure_index('hitId', unique= True,dropDups = True)
db.tasks.ensure_index('id', unique= False)
db.responses.ensure_index('assignmentId', unique= True, dropDups = True)
db.messages.ensure_index('id', unique= True, dropDups = True)
db.worker_ratings.ensure_index('id', unique= True, dropDups = True)
db.worker_locations.ensure_index('workerId', unique= True, dropDups = True)