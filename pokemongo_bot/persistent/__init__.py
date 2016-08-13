# -*- coding: utf-8 -*-

from pokemongo_bot.tree_config_builder import ConfigException
from mongodb_handler import MongoDBHandler

_handler = None

def persistentEnabled(bot):
    global _handler
    if _handler == None:
        if 'persistent' not in bot.config:
            return False

        settings = bot.config.persistent
        if "backend" not in settings:
            raise ConfigException("Missing backend define")

        if settings['backend'] == 'MongoDB':
            _handler = MongoDBHandler(settings.get("config", {}))
        else:
            raise ConfigException("Unknown persistent backend {}".format(settings['backend']))

    return _handler.connected

def getPersistentHandler():
    global _handler
    return _handler
