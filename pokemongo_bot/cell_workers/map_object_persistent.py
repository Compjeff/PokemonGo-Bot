from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult

class MapObjectPersistent(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        print self.config

    def work(self):
        print "dsdsds ddss"
