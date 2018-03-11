from models.Task import Task 


class GenerateTask(Task):
    default_task_config = {
        'task_type': 'generate_task',
        'task_path' : 'generate_quality.html',
        'per_message_incentive': 0.14,
        'title': 'Help someone to walk more in his daily routine by generating messages.',
        'hit_options':{
            'message_count_per_hit': 3
        }
    }

    def prepare_input(self):
        # No preparing needed
        pass

    def initialize_hits(self):
        self.final_hits = self.input_hit_conf
        print 'found %s hits'%len(self.final_hits)
