import pymongo
from datetime import datetime

class MongoDBHandler:

    def __init__(self, config):
        self.multiplier = 100000000000000L

        if 'host' not in config:
            config['host'] = '127.0.0.1'
        if 'port' not in config:
            config['port'] = 27017
        if 'database' not in config:
            config['database'] = 'pokemongo_bot'

        self.config = config
        self.connected = False

        self.conn = pymongo.MongoClient('mongodb://%s:%d' % (config['host'], config['port']))

        self.db = self.conn[config['database']]

        try:
            self.conn.server_info()
            self.connected = True
        except pymongo.errors.ServerSelectionTimeoutError as err:
            pass

    def saveGym(self, s2_cell_id, gymInfo):
        self.db.gyms.update_one({'_id':gymInfo['id']}, {
                "$set": {
                    "gym_points": gymInfo["gym_points"],
                    "guard_pokemon_id": gymInfo["guard_pokemon_id"],
                    "owned_by_team": gymInfo['owned_by_team'],
                    'last_modified': datetime.fromtimestamp(round(gymInfo['last_modified_timestamp_ms']/1000)),
                    'enabled': gymInfo['enabled']
                },
                "$setOnInsert": {
                    '_id': gymInfo['id'],
                    's2_cell_id': str(s2_cell_id),
                    'loc': [gymInfo['latitude'], gymInfo['longitude']]
                }
        }, upsert=True)

    def savePokestop(self, s2_cell_id, pokestopInfo):
        self.db.pokestops.update_one({'_id':pokestopInfo['id']}, {
            '$set': {
                'enabled': pokestopInfo['enabled'],
                'last_modified': datetime.fromtimestamp(round(pokestopInfo['last_modified_timestamp_ms']/1000))
            },
            '$setOnInsert': {
                '_id': pokestopInfo['id'],
                's2_cell_id': str(s2_cell_id),
                'loc': [pokestopInfo['latitude'], pokestopInfo['longitude']]
            }
        }, upsert=True)

    def makeSignature(self, info):
        return "%d,%d"%(round(info["latitude"]*self.multiplier), round(info['longitude']*self.multiplier))

    def savePotentialSpawnPoint(self, s2_cell_id, info):
        try:
            self.db.potential_spawnpoints.insert_one({
                "_id": self.makeSignature(info),
                "loc": [info["latitude"], info["longitude"]],
                "s2_cell_id": str(s2_cell_id)
            })
        except pymongo.errors.DuplicateKeyError:
            pass

    def saveSpawnPoint(self, s2_cell_id, info):
        self.db.spawnpoints.update_one({
            '_id': info['spawn_point_id']
        }, {
            '$set': {
                's2_cell_id': str(s2_cell_id),
            },
            '$setOnInsert': {
                '_id': info['spawn_point_id'],
                "loc": [info["latitude"], info["longitude"]]
            }
        }, upsert=True)

    def saveEncounter(self, s2_cell_id, info):
        self.saveSpawnPoint(s2_cell_id, info)
        try:
            self.db.encounters.insert_one({
                '_id': str(info['encounter_id']),
                's2_cell_id': str(s2_cell_id),
                'loc': [info["latitude"], info["longitude"]],
                'spawn_point_id': info['spawn_point_id'],
                'pokemon_id': info['pokemon_id']
            })
        except pymongo.errors.DuplicateKeyError:
            pass
