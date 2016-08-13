import json
import os

from pokemongo_bot import inventory
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.services.item_recycle_worker import ItemRecycler
from pokemongo_bot.tree_config_builder import ConfigException
from pokemongo_bot.worker_result import WorkerResult

DEFAULT_MIN_EMPTY_SPACE = 6

class RecycleItems(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    """
    Recycle undesired items if there is less than five space in inventory.
    You can use either item's name or id. For the full list of items see ../../data/items.json

    It's highly recommended to put this task before move_to_fort and spin_fort task in the config file so you'll most likely be able to loot.

    Example config :
    {
      "type": "RecycleItems",
      "config": {
        "min_empty_space": 6,           # 6 by default
        "item_filter": {
          "Pokeball": {"keep": 20},
          "Greatball": {"keep": 50},
          "Ultraball": {"keep": 100},
          "Potion": {"keep": 0},
          "Super Potion": {"keep": 0},
          "Hyper Potion": {"keep": 20},
          "Max Potion": {"keep": 50},
          "Revive": {"keep": 0},
          "Max Revive": {"keep": 20},
          "Razz Berry": {"keep": 20}
        }
      }
    }
    """

    def initialize(self):
        self.items_filter = self.config.get('item_filter', {})
        self.min_empty_space = self.config.get('min_empty_space', None)
        self._validate_item_filter()

    def _validate_item_filter(self):
        """
        Validate user's item filter config
        :return: Nothing.
        :rtype: None
        :raise: ConfigException: When an item doesn't exist in ../../data/items.json
        """
        item_list = json.load(open(os.path.join(_base_dir, 'data', 'items.json')))

        for config_item_name, bag_count in self.items_filter.iteritems():
            if config_item_name == 'All Balls':
                continue
            if config_item_name == 'All Portions':
                continue

            if config_item_name not in item_list.viewvalues():
                if config_item_name not in item_list:
                    raise ConfigException(
                        "item {} does not exist, spelling mistake? (check for valid item names in data/items.json)".format(
                            config_item_name))

    def should_run(self):
        """
        Returns a value indicating whether the recycling process should be run.
        :return: True if the recycling process should be run; otherwise, False.
        :rtype: bool
        """
        if inventory.items().get_space_left() < (DEFAULT_MIN_EMPTY_SPACE if self.min_empty_space is None else self.min_empty_space):
            return True
        return False

    def work(self):
        items_in_bag = self.bot.get_inventory_count('item')
        total_bag_space = self.bot.player_data['max_item_storage']
        free_bag_space = total_bag_space - items_in_bag

        if self.min_empty_space is not None:
            if free_bag_space >= self.min_empty_space and items_in_bag < total_bag_space:
                    self.emit_event(
                        'item_discard_skipped',
                        formatted="Skipping Recycling of Items. {space} space left in bag.",
                        data={
                            'space': free_bag_space
                        }
                    )
                    return

        self.bot.latest_inventory = None
        item_count_dict = self.bot.item_inventory_count('all')

        # build item filter dynamicly if we have total limit
        if "All Balls" in self.items_filter:
            all_balls_limit = self.items_filter.get("All Balls").get("keep", 50)
            pokeball_count = item_count_dict.get(1, 0)
            greatball_count = item_count_dict.get(2, 0)
            ultraball_count = item_count_dict.get(3, 0)
            masterball_count = item_count_dict.get(4, 0)

            if ( pokeball_count + greatball_count + ultraball_count + masterball_count) > all_balls_limit:
                if ( greatball_count + ultraball_count + masterball_count ) > all_balls_limit:
                    self.items_filter["Pokeball"] = {"keep":0}
                    self.items_filter["1"] = {"keep":0}
                    if ( ultraball_count + masterball_count ) > all_balls_limit:
                        self.items_filter["Greatball"] = {"keep":0}
                        self.items_filter["2"] = {"keep":0}
                        if masterball_count > all_balls_limit:
                            self.items_filter["Ultraball"] = {"keep":0}
                            self.items_filter["3"] = {"keep":0}
                            self.items_filter["Masterball"] = {"keep":all_balls_limit}
                            self.items_filter["4"] = {"keep":all_balls_limit}
                        else:
                            self.items_filter["Ultraball"] = {"keep":all_balls_limit - masterball_count}
                            self.items_filter["3"] = {"keep":all_balls_limit - masterball_count}
                    else:
                        self.items_filter["Greatball"] = {"keep":all_balls_limit - ultraball_count - masterball_count}
                        self.items_filter["2"] = {"keep":all_balls_limit - ultraball_count - masterball_count}
                else:
                    self.items_filter["Pokeball"] = {"keep":all_balls_limit - greatball_count - ultraball_count - masterball_count}
                    self.items_filter["1"] = {"keep":all_balls_limit - greatball_count - ultraball_count - masterball_count}

        if "All Portions" in self.items_filter:
            all_portions_limit = self.items_filter.get("All Portions").get("keep", 50)
            portion_count = item_count_dict.get(101, 0)
            super_count = item_count_dict.get(102, 0)
            hyper_count = item_count_dict.get(103, 0)
            max_count = item_count_dict.get(104, 0)

            if ( portion_count + super_count + hyper_count + max_count) > all_portions_limit:
                if ( super_count + hyper_count + max_count ) > all_portions_limit:
                    self.items_filter["Portion"] = {"keep":0}
                    self.items_filter["101"] = {"keep":0}
                    if ( hyper_count + max_count ) > all_portions_limit:
                        self.items_filter["Super Portion"] = {"keep":0}
                        self.items_filter["102"] = {"keep":0}
                        if max_count > all_portions_limit:
                            self.items_filter["Hyper Portion"] = {"keep":0}
                            self.items_filter["103"] = {"keep":0}
                            self.items_filter["Max Portion"] = {"keep":all_portions_limit}
                            self.items_filter["104"] = {"keep":all_portions_limit}
                        else:
                            self.items_filter["Hyper Portion"] = {"keep":all_portions_limit - max_count}
                            self.items_filter["103"] = {"keep":all_portions_limit - max_count}
                    else:
                        self.items_filter["Super Portion"] = {"keep":all_portions_limit - hyper_count - max_count}
                        self.items_filter["102"] = {"keep":all_portions_limit - hyper_count - max_count}
                else:
                    self.items_filter["Portion"] = {"keep":all_portions_limit - super_count - hyper_count - max_count}
                    self.items_filter["101"] = {"keep":all_portions_limit - super_count - hyper_count - max_count}

        for item_id, bag_count in item_count_dict.iteritems():
            item_name = self.bot.item_list[str(item_id)]
            id_filter = self.items_filter.get(item_name, 0)
            id_filter_keep = 0
            if id_filter is not 0:
                id_filter_keep = id_filter.get('keep', 20)
            else:
                id_filter = self.items_filter.get(str(item_id), 0)
                if id_filter is not 0:
                    id_filter_keep = id_filter.get('keep', 20)

            bag_count = self.bot.item_inventory_count(item_id)

            if (item_name in self.items_filter or str(item_id) in self.items_filter) and bag_count > id_filter_keep:
                items_recycle_count = bag_count - id_filter_keep
                response_dict_recycle = self.send_recycle_item_request(item_id=item_id, count=items_recycle_count)
                result = response_dict_recycle.get('responses', {}).get('RECYCLE_INVENTORY_ITEM', {}).get('result', 0)

                if result == 1: # Request success
                    self.emit_event(
                        'item_discarded',
                        formatted='Discarded {amount}x {item} (maximum {maximum}).',
                        data={
                            'amount': str(items_recycle_count),
                            'item': item_name,
                            'maximum': str(id_filter_keep)
                        }
                    )
                else:
                    self.emit_event(
                        'item_discard_fail',
                        formatted="Failed to discard {item}",
                        data={
                            'item': item_name
                        }
                    )

    def send_recycle_item_request(self, item_id, count):
        # Example of good request response
        # {'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        return self.bot.api.recycle_inventory_item(
            item_id=item_id,
            count=count
        )

        """
        Discard items if necessary.
        :return: Returns wether or not the task went well
        :rtype: WorkerResult
        """
        # TODO: Use new inventory everywhere and then remove the inventory update
        # Updating inventory
        inventory.refresh_inventory()
        worker_result = WorkerResult.SUCCESS
        if self.should_run():

            # For each user's item in inventory recycle it if needed
            for item_in_inventory in inventory.items().all():
                amount_to_recycle = self.get_amount_to_recycle(item_in_inventory)

                if self.item_should_be_recycled(item_in_inventory, amount_to_recycle):
                    action_delay(self.bot.config.action_wait_min, self.bot.config.action_wait_max)
                    if ItemRecycler(self.bot, item_in_inventory, amount_to_recycle).work() == WorkerResult.ERROR:
                        worker_result = WorkerResult.ERROR

        return worker_result

    def item_should_be_recycled(self, item, amount_to_recycle):
        """
        Returns a value indicating whether the item should be recycled.
        :param amount_to_recycle:
        :param item:
        :return: True if the title should be recycled; otherwise, False.
        :rtype: bool
        """
        return (item.name in self.items_filter or str(
            item.id) in self.items_filter) and amount_to_recycle > 0

    def get_amount_to_recycle(self, item):
        """
        Determine the amount to recycle accordingly to user config
        :param item: Item to determine the amount to recycle
        :return: The amount to recycle
        :rtype: int
        """
        amount_to_keep = self.get_amount_to_keep(item)
        return 0 if amount_to_keep is None else item.count - amount_to_keep

    def get_amount_to_keep(self, item):
        """
        Determine item's amount to keep in inventory.
        :param item:
        :return: Item's amount to keep in inventory.
        :rtype: int
        """
        item_filter_config = self.items_filter.get(item.name, 0)
        if item_filter_config is not 0:
            return item_filter_config.get('keep', 20)
        else:
            item_filter_config = self.items_filter.get(str(item.id), 0)
            if item_filter_config is not 0:
                return item_filter_config.get('keep', 20)
