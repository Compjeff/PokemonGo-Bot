from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.persistent import persistent_enabled

class MapObjectPersistent(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.last_map_object_time = 0;

    def work(self):
        if not self.bot.last_map_object:
            return

        if self.bot.last_time_map_object == self.last_map_object_time:
            return

        if 'responses' not in self.bot.last_map_object:
            return

        if 'GET_MAP_OBJECTS' not in self.bot.last_map_object['responses']:
            return

        dict = self.bot.last_map_object['responses']['GET_MAP_OBJECTS']
        if 'map_cells' not in dict:
            return;

        if not persistent_enabled(self.bot):
            return;

        for cell in dict['map_cells']:
            s2_cell_id = cell['s2_cell_id']
            if 'forts' in cell:
                for fort in cell['forts']:
                    if 'owned_by_team'in fort:
                        pass
                    if 'type' in fort:
                        if fort['type'] == 1:
                            pass
            if 'spawn_points' in cell:
                pass
            if 'catchable_pokemons' in cell:
                pass
            if 'wild_pokemons' in cell:
                pass
            if 'nearby_pokemons' in cell:
                pass
