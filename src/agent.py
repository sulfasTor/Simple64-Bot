from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pysc2.lib import units
from random import randrange
from time import sleep

import sys, numpy, math

# Features
_PLAYER_SELF = features.PlayerRelative.SELF
_PLAYER_NEUTRAL = features.PlayerRelative.NEUTRAL
_PLAYER_ENEMY = features.PlayerRelative.ENEMY
_UNIT_TYPE = features.SCREEN_FEATURES.unit_type.index

# Functions
_SELECT_IDLE_WORKER = actions.FUNCTIONS.select_idle_worker.id
_HARVEST_GATHER_SCREEN = actions.FUNCTIONS.Harvest_Gather_screen.id
_HARVEST_RETURN_QUICK = actions.FUNCTIONS.Harvest_Return_quick.id
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_TRAIN_SCV_QUICK = actions.FUNCTIONS.Train_SCV_quick.id
_BUILD_SUPPLYDEPOT_SCREEN = actions.FUNCTIONS.Build_SupplyDepot_screen.id
_BUILD_BARRACKS_SCREEN =  actions.FUNCTIONS.Build_Barracks_screen.id
_ATTACK_SCREEN = actions.FUNCTIONS.Attack_screen.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_SELECT_RECT = actions.FUNCTIONS.select_rect.id
_NO_OP = actions.FUNCTIONS.no_op.id
_FUNCTIONS = actions.FUNCTIONS

# Parameters
_NOT_QUEUED = [0]
_SCREEN = [0]
_SELECT = [0]

# Costs
_SUPPLY_DEPOT_COST = [100, 0]
_BARRACKS_COST = [150, 0]
_SCV_COST = [50, 0]
_MARINE_COST = [50, 0]
_MARAUDER_COST = [100, 25]


def printf(format, *args):
    sys.stdout.write(format % args)
    
def erode_with_min(screen):
    output = [] 
    for i in range(84):
        output.append([0] * 84)
    for i in range(1,83) :
        for j in range(1,83) :
            if(screen[i][j] == 1):
                output[i][j] = int(min(screen[i][j], 
                                       screen[i+1][j],
                                       screen[i-1][j], 
                                       screen[i][j+1],
                                       screen[i][j-1]))
    return output

def print_screen(mine):
    for i in range(0,84) :
        for j in range(0,84) :
            printf("%d", mine[i][j])
            print("")

def define_action(obs, action_id, args=[]):
    if action_id in obs.observation.available_actions:
        return actions.FunctionCall(action_id, args)
    else:
        return actions.FunctionCall(_NO_OP, [])

def has_enough_ressources(wanted_ressource, ressources):
    return wanted_ressource[0] <= ressources[0] and wanted_ressource[1] <= ressources[1]

def get_mineral_coord(obs):
    unit_type = obs.observation.feature_screen[_UNIT_TYPE]
    mine = (unit_type == units.Neutral.MineralField)
    mine = erode_with_min(mine)
    mineral_y, mineral_x = numpy.array(mine).nonzero()
    return [mineral_x[0], mineral_y[0]]


# python3 -m pysc2.bin.agent --map Simple64 --agent agent.Bot64 --agent_race terran
class Bot64(base_agent.BaseAgent):

    def __init__(self):
        super(Bot64, self).__init__()

    def setup(self, obs_spec, action_spec):
        super(Bot64, self).setup(obs_spec, action_spec)
        # if "feature_units" not in obs_spec:
        #     raise Exception("feature_units observation not active. Activate it with --use_feature_units") 
    def reset(self):
        super(Bot64, self).reset()

        # spending
        self.spent_on_scv_training = 0
        self.spent_on_supply_depots = 0
        self.spent_on_barracks_depots = 0
        
        # buildings
        self.nb_supply_depot = 0
        self.nb_barracks = 0
        self.supply_depot_last_location = [-1, -1]
        self.barrack_depot_last_location = [-1,-1]
        self.prev_total_value_structures = 400 # CC

        # units
        self.nb_scv = 12
        self.nb_marines = 0
        self.nb_harvest_gather = 0
        self.nb_scv_in_train = 0

        # rates
        self.supply_depot_rate = 3
        self.barracks_rate = 0
        self.scv_rate = 13

        # flags
        self.scv_training_counter = 0
        self.marine_training_counter = 0
        self.commandcenter_selected = False
        self.inactive_scv_selected = False
        self.all_inactive_scv_selected = False
        self.random_scv_selected = False
        self.marine_selected = False
        self.attack_mode_on = False
        self.enemy = None
        self.spawned_right_side = False
        self.supply_depot_in_construction = False
        self.barrack_in_construction = False

    def update_buildings(self, obs):
        total_value_structures = obs.observation.score_cumulative.total_value_structures
        spent_minerals = obs.observation.score_cumulative.spent_minerals
        if total_value_structures != self.prev_total_value_structures:
            diff = (total_value_structures - self.prev_total_value_structures)
            if diff == sum(_SUPPLY_DEPOT_COST):
                self.nb_supply_depot += 1
                self.supply_depot_in_construction = False
                self.scv_rate += 5
                print("changed flag supply_depot_in construction to False")
            elif diff == sum(_BARRACKS_COST):
                self.nb_barracks += 1
                self.barrack_in_construction = False
            self.prev_total_value_structures = total_value_structures

        print("-----spent_minerals (%d)------\n\t- supply depot = %d \n\t- scv = %d" %(spent_minerals, self.spent_on_supply_depots, self.spent_on_scv_training))
        if spent_minerals != (self.spent_on_supply_depots + self.spent_on_scv_training) :
            print("Failed to construct a supply depot")
            self.spent_on_supply_depots -= sum(_SUPPLY_DEPOT_COST)
            self.supply_depot_in_construction = False
        if spent_minerals != (self.spent_on_barracks_depots + self.spent_on_scv_training) :
            print("Failed to construct a barrack")
            self.spent_on_barracks_depots -= sum(_BARRACKS_COST)
            self.barrack_in_construction = False
                                
    def step(self, obs):
        super(Bot64, self).step(obs)
        print(obs.observation.available_actions)
        self.update_buildings(obs)
        resources = [obs.observation.score_cumulative.collected_minerals,
                     obs.observation.score_cumulative.collected_vespene]

        # # Check for enemies
        # self.enemy = xy_locs(obs.observation.feature_screen.player_relative == _PLAYER_ENEMY)
        
        # if self.enemy and self.nb_marines > 0:
        #     if not self.marine_selected:
                
        #     if not _ATTACK_SCREEN in obs.observation.available_actions:
        #         return define_action(obs, _SELECT_RECT, [_SELECT, [0,0], [83,83]])

        #     if not self.attack_mode_on:
        #         target = self.enemy[numpy.argmax(numpy.array(self.enemy)[:, 1])]
        #         self.attack_mode_on = True
        #         self.harvest_mode_on = False
        #         return define_action(obs, _ATTACK_SCREEN, [_SELECT, target])
        #     return define_action(obs, _HARVEST_RETURN_QUICK, [_NOT_QUEUED])
        
        # Build supply depot
        if self.nb_supply_depot <= self.supply_depot_rate and self.supply_depot_in_construction == False:
            if has_enough_ressources(_SUPPLY_DEPOT_COST, resources):
                self.barracks_rate += 1 if self.nb_supply_depot >=  2 else 0
                return self.build_supply_depot(obs)
        #Build barrack
        if self.nb_barracks < self.barracks_rate and self.nb_barracks < 10:
            if has_enough_ressources(_BARRACKS_COST, resources):
                return self.build_barrack(obs)

        # Train SCV
        if self.scv_training_counter > 0 and self.scv_training_counter < 5:
            self.scv_training_counter += 1
            return self.train_SCV(obs)
        self.scv_training_counter = 0
        self.supply_depot_rate += 1
        
        # Train more SCVs
        if self.nb_scv <= self.scv_rate:
            if has_enough_ressources([i * 5 for i in _SCV_COST], resources):
                self.scv_training_counter += 1

        # Send idle workers to harvest
        if _SELECT_IDLE_WORKER in obs.observation.available_actions:
            self.all_inactive_scv_selected = True
            return _FUNCTIONS.select_idle_worker("select")

        if self.all_inactive_scv_selected:
            print("sent idle workers to harvest")
            # dest = get_mineral_coord(obs)
            self.all_inactive_scv_selected = False
            # return _FUNCTIONS.Harvest_Gather_screen("queued", dest)
            return _FUNCTIONS.Harvest_Return_quick("queued")

        # # Train Marine
        # if self.marine_training_counter > 0 and self.marine_training_counter < 5:
        #     self.marine_training_counter += 1
        #     return self.train_Marine(obs)
        # self.marine_training_counter = 0
        
        # # Train more Marines
        # if self.nb_marine <= self.marine_rate:
        #     if has_enough_ressources([i * 5 for i in _MARINE_COST], resources):
        #         self.marine_rate += 1
        #         self.marine_training_counter += 1

        # print("no op")
        return _FUNCTIONS.no_op()

    def build_barrack(self,obs):
        if self.inactive_scv_selected == False and self.random_scv_selected == False:
            return self.select_unit_or_building(obs, "scv")

        if _BUILD_BARRACKS_SCREEN in obs.observation.available_actions:
            self.nb_barracks += 1
            target = self.get_new_barracks_location(obs)
            self.barrack_in_construction = True
            print("succeded")
            
            return _FUNCTIONS.Build_Barracks_screen("queued", target)

        print("failed")
        return _FUNCTIONS.no_op()
    
    def build_supply_depot(self, obs):
        if self.inactive_scv_selected == False and self.random_scv_selected == False:
            print("TRYING TO SELECT A SCV...")
            return self.select_unit_or_building(obs, "scv")

        if _BUILD_SUPPLYDEPOT_SCREEN in obs.observation.available_actions:
            self.supply_depot_in_construction = True
            target = self.get_new_supply_depot_location(obs)
            print("---------- target of payed sp is [%d, %d] ------------" %(target[0], target[0]))
            self.spent_on_supply_depots += sum(_SUPPLY_DEPOT_COST)
            return _FUNCTIONS.Build_SupplyDepot_screen("queued", target)

        self.inactive_scv_selected = False
        self.random_scv_selected = False
        print("\nFailed to select %s \n" %("a random worker" if self.random_scv_selected else ("a idle worker" if self.inactive_scv_selected else "anything")))
        return _FUNCTIONS.no_op()

    def get_new_supply_depot_location(self, obs):
        if self.supply_depot_last_location == [-1,-1]:
            unit_type = obs.observation.feature_screen[_UNIT_TYPE]
            y_coord = (unit_type == units.Neutral.MineralField).nonzero()[0]
            self.spawned_right_side = numpy.mean(y_coord, axis=0).round() > 42

            if self.spawned_right_side:
                self.supply_depot_last_location = [10, 10]
            else:
                self.supply_depot_last_location = [73,73]
        else:
            unit_type = obs.observation.feature_screen[_UNIT_TYPE]
            sp_y, sp_x = (unit_type == units.Terran.SupplyDepot).nonzero()
            rand_idx = randrange(len(sp_x))
            print("randix is %d" %(rand_idx))

            if self.spawned_right_side:
                self.supply_depot_last_location[1] = sp_y[rand_idx] + 5
            else:
                self.supply_depot_last_location[1] = sp_y[rand_idx] - 5
                
            while self.supply_depot_last_location[0] < 0 or self.supply_depot_last_location[0] > 83 or \
                   self.supply_depot_last_location[1] < 0 or self.supply_depot_last_location[1] > 83:
                   rand_idx = randrange(len(sp_x))
                   print("randix is %d" %(rand_idx))
                   self.supply_depot_last_location[0] = sp_x[rand_idx] + (5 if self.spawned_right_side else -5)
                   self.supply_depot_last_location[1] = sp_y[rand_idx] + (5 if self.spawned_right_side else -5)

        return self.supply_depot_last_location
                
    def get_new_barracks_location(self, obs):
        if self.barrack_depot_last_location == [-1,-1]:
            unit_type = obs.observation.feature_screen[_UNIT_TYPE]
            y_coord = (unit_type == units.Neutral.MineralField).nonzero()[0]
            self.spawned_right_side = numpy.mean(y_coord, axis=0).round() > 42
            
            if self.spawned_right_side:
                self.barrack_depot_last_location= [30, 30]
            else:
                self.barrack_depot_last_location= [53,53]
        else:
            unit_type = obs.observation.feature_screen[_UNIT_TYPE]
            sp_y, sp_x = (unit_type == units.Terran.Barracks).nonzero()
            rand_idx = randrange(len(sp_x))
            print("randix is %d" %(rand_idx))

            if self.spawned_right_side:
                self.barrack_depot_last_location[1] = sp_y[rand_idx] + 5
            else:
                self.barrack_depot_last_location[1] = sp_y[rand_idx] - 5
                
            while self.barrack_depot_last_location[0] < 0 or self.barrack_depot_last_location[0] > 83 or \
                   self.barrack_depot_last_location[1] < 0 or self.barrack_depot_last_location[1] > 83:
                   rand_idx = randrange(len(sp_x))
                   print("randix is %d" %(rand_idx))
                   self.barrack_depot_last_location[0] = sp_x[rand_idx] + (5 if self.spawned_right_side else -5)
                   self.barrack_depot_last_location[1] = sp_y[rand_idx] + (5 if self.spawned_right_side else -5)

        return self.barrack_depot_last_location


                
    def select_unit_or_building(self, obs, unit_or_building):
        if unit_or_building == "scv":
            # if self.inactive_scv_selected == False:
            #     if _SELECT_IDLE_WORKER in obs.observation.available_actions:
            #         self.inactive_scv_selected = True
            #         self.random_scv_selected = False
            #         self.commandcenter_selected = False
            #         self.marine_selected = False
            #         return _FUNCTIONS.select_idle_worker("select")
            if self.random_scv_selected == False:
                self.random_scv_selected = True
                self.inactive_scv_selected = False
                self.commandcenter_selected = False
                self.marine_selected = False
                unit_type = obs.observation.feature_screen[_UNIT_TYPE]
                scv_y, scv_x = (unit_type == units.Terran.SCV).nonzero()
                rand_idx = randrange(len(scv_y))
                target = [scv_x[rand_idx], scv_y[rand_idx]]
                return define_action(obs, _SELECT_POINT, [_SCREEN, target])
        elif unit_or_building == "cc":
            if self.commandcenter_selected == False:
                self.commandcenter_selected = True
                self.inactive_scv_selected = False
                self.random_scv_selected = False
                self.marine_selected = False
                unit_type = obs.observation.feature_screen[_UNIT_TYPE]
                commandcenter_y, commandcenter_x = (unit_type == units.Terran.CommandCenter).nonzero()
                cc_center_x = numpy.mean(commandcenter_x, axis=0).round()
                cc_center_y = numpy.mean(commandcenter_y, axis=0).round()
                target = [cc_center_x, cc_center_y]
                return _FUNCTIONS.select_point("select", target)
            
        return _FUNCTIONS.no_op()

    def train_SCV(self, obs):
        if self.commandcenter_selected == False:
            return self.select_unit_or_building(obs, "cc")
        
        if _TRAIN_SCV_QUICK in obs.observation.available_actions:
            self.nb_scv += 1
            self.spent_on_scv_training += sum(_SCV_COST)
            print("started training of a scv")
            return _FUNCTIONS.Train_SCV_quick("queued")
        return actions.FUNCTIONS.no_op()

    # def train_Marine(self, obs):
    #     if self.barrack_selected == False:
    #         return self.select_unit_or_building(obs, "br")
        
    #     if _TRAIN_MARINE_QUICK in obs.observation.available_actions:
    #         self.nb_marines_in_train += 1
    #         return _FUNCTIONS.Train_Marine_quick("select")
    #     return actions.FUNCTIONS.no_op()


