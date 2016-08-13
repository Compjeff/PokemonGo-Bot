from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.persistent import persistentEnabled
from pokemongo_bot.persistent import getPersistentHandler

class MapObjectPersistent(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.last_map_object_time = 0;

    def work(self):
        if not self.bot.last_map_object:
            return

        if self.bot.last_time_map_object == self.last_map_object_time:
            return

        self.last_map_object_time = self.bot.last_time_map_object

        if 'responses' not in self.bot.last_map_object:
            return

        if 'GET_MAP_OBJECTS' not in self.bot.last_map_object['responses']:
            return

        dict = self.bot.last_map_object['responses']['GET_MAP_OBJECTS']
        if 'map_cells' not in dict:
            return;

        if not persistentEnabled(self.bot):
            return;

        handler = getPersistentHandler()

        for cell in dict['map_cells']:
            s2_cell_id = cell['s2_cell_id']
            if 'forts' in cell:
                for fort in cell['forts']:
                    if 'owned_by_team'in fort:
                        handler.saveGym(s2_cell_id, fort)
                    if 'type' in fort:
                        if fort['type'] == 1:
                            handler.savePokestop(s2_cell_id, fort)
            if 'spawn_points' in cell:
                for spawnPoint in cell['spawn_points']:
                    handler.savePotentialSpawnPoint(s2_cell_id, spawnPoint)
            if 'catchable_pokemons' in cell:
                for encounter in cell['catchable_pokemons']:
                    handler.saveEncounter(s2_cell_id, encounter)
            if 'wild_pokemons' in cell:
                for encounter in cell['wild_pokemons']:
                    print encounter
            if 'nearby_pokemons' in cell:
                pass
