class Response:

    def __init__(self, data):
        self.data = data
        self.use_sandbox = data['use_sandbox']
        self.experiment_id = data['experiment_id']
        self.assignment_id = data['assignmentId']  # as an id for vote
        self.worker_id = data['workerId']
        self.hit_id = data['hitId']
        self.task_id = data['task_id']