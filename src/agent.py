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
_BUILD_REFINERY_SCREEN = actions.FUNCTIONS.Build_Refinery_screen.id
_BUILD_BARRACKS_SCREEN =  actions.FUNCTIONS.Build_Barracks_screen.id
_ATTACK_SCREEN = actions.FUNCTIONS.Attack_screen.id
_TRAIN_MARINE_QUICK = actions.FUNCTIONS.Train_Marine_quick.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_SELECT_RECT = actions.FUNCTIONS.select_rect.id
_MOVE_CAMERA = actions.FUNCTIONS.move_camera.id
_MOVE_SCREEN = actions.FUNCTIONS.Move_screen.id
_NO_OP = actions.FUNCTIONS.no_op.id
_FUNCTIONS = actions.FUNCTIONS

# Parameters
_NOT_QUEUED = [0]
_SCREEN = [0]
_SELECT = [0]

# Costs
_SUPPLY_DEPOT_COST = [100, 0]
_COMMAND_CENTER_COST = [400, 0]
_REFINERY_COST = [75, 0]
_BARRACKS_COST = [150, 0]
_SCV_COST = [50, 0]
_MARINE_COST = [50, 0]
_MARAUDER_COST = [100, 25]

def _xy_locs(mask):
    y, x = mask.nonzero()
    return list(zip(x, y))

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

def get_vespene_coord(obs):
    unit_type = obs.observation.feature_screen[_UNIT_TYPE]
    vesp_y, vesp_x = (unit_type == units.Neutral.VespeneGeyser).nonzero()
    rand_idx = randrange(len(vesp_y))
    x = vesp_x[rand_idx]
    y = vesp_y[rand_idx]
    return [x, y]

def get_barracks_coord(obs):
    unit_type = obs.observation.feature_screen[_UNIT_TYPE]
    br = (unit_type == units.Terran. Barracks)
    br = erode_with_min(br)
    br_y, br_x = numpy.array(br).nonzero()
    rand_idx = randrange(len(br_y))
    return [br_x[rand_idx], br_y[rand_idx]]
    

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

        # camera
        self.camera_location = [36,43] # if spawned left side is [18,21]

        # spending
        self.spent_on_scv_training = 0
        self.spent_on_supply_depots = 0
        self.spent_on_refinery = 0
        self.spent_on_barracks = 0
        self.spent_on_marines_training = 0
        
        # buildings
        self.nb_supply_depot = 0
        self.nb_refineries = 0
        self.nb_barracks = 0
        self.supply_depot_last_location = [-1, -1]
        self.prev_total_value_structures = sum(_COMMAND_CENTER_COST)
        self.barrack_last_location = [-1,-1]
        self.prev_total_value_structures = 400 # CC

        # units
        self.nb_scv = 12
        self.nb_marines = 0

        # rates
        self.refineries_rate = 1
        self.supply_depot_rate = 4 # Add 1
        self.barracks_rate = 1
        self.scv_rate = 15
        self.marines_rate = 15

        # counters
        self.scv_training_counter = 0
        self.marine_training_counter = 0
        self.supply_depot_construction_tries = 0

        # flags
        # # selection
        self.army_selected = False
        self.commandcenter_selected = False
        self.inactive_scv_selected = False
        self.all_inactive_scv_selected = False
        self.random_scv_selected = False
        self.barrack_selected = False
        self.marine_selected = False

        # # modes
        self.attack_mode_on = False
        self.enemy = None
        self.spawned_right_side = False

        # # constructions
        self.supply_depot_in_construction = False
        self.barrack_in_construction = False
        self.refinery_in_construction = False

    def update_buildings(self, obs):
        total_value_structures = obs.observation.score_cumulative.total_value_structures
        spent_minerals = obs.observation.score_cumulative.spent_minerals

        if total_value_structures != self.prev_total_value_structures:
            diff = (total_value_structures - self.prev_total_value_structures)
            if self.nb_supply_depot < self.supply_depot_rate:
                if diff == sum(_SUPPLY_DEPOT_COST):
                    self.nb_supply_depot += 1
                    self.supply_depot_in_construction = False
                    self.supply_depot_construction_tries = 0
            elif self.nb_barracks < self.barracks_rate:
                if diff == sum(_BARRACKS_COST):
                    self.nb_barracks += 1
                    self.barrack_in_construction = False
            elif self.nb_refineries < self.refineries_rate:
                if diff == sum(_REFINERY_COST):
                    self.nb_refineries += 1
                    self.refinery_in_construction = False
            else:
                print("reached end of building verification without conflicts")
                  
        self.prev_total_value_structures = total_value_structures

        expected_spent_minerals = self.spent_on_supply_depots + self.spent_on_scv_training + self.spent_on_refinery + self.spent_on_barracks
        if spent_minerals != expected_spent_minerals:
            if self.nb_supply_depot >= self.supply_depot_rate:
                print("Spent minerals: %d, expected %d" %(spent_minerals, expected_spent_minerals))
                # print("Failed to construct a barrack")
                # self.spent_on_barracks -= sum(_BARRACKS_COST)
                self.barrack_in_construction = False
            else:
                print("Failed to construct a supply depot")
                self.supply_depot_construction_tries += 1
                self.spent_on_supply_depots -= sum(_SUPPLY_DEPOT_COST)
                self.supply_depot_in_construction = False
                
    def step(self, obs):
        super(Bot64, self).step(obs)
        self.update_buildings(obs)
        resources = [obs.observation.score_cumulative.collected_minerals,
                     obs.observation.score_cumulative.collected_vespene]

        self.print_state()        
        # Check for enemies
        if self.attack_mode_on:
            self.enemy = None
            self.enemy = _xy_locs(obs.observation.feature_screen.player_relative == _PLAYER_ENEMY)
            
            if self.enemy:
                if self.army_selected:
                    self.army_selected = False
                    target = self.enemy[numpy.argmax(numpy.array(self.enemy)[:, 1])]
                    return define_action(obs, _ATTACK_SCREEN, [_NOT_QUEUED, target])
                
                self.army_selected = True
                return define_action(obs, _SELECT_RECT, [_SELECT, [0,0], [83,83]])
            else:
                self.adjust_camera(1,1)
                return define_action(obs, _MOVE_CAMERA, [self.camera_location])
                          
        # Build supply depot
        if self.nb_supply_depot <= self.supply_depot_rate and self.supply_depot_in_construction == False:
            if has_enough_ressources(_SUPPLY_DEPOT_COST, resources):
                return self.build_supply_depot(obs)

        # Train SCV
        if self.scv_training_counter > 0 and self.scv_training_counter < 3:
            self.scv_training_counter += 1
            return self.train_SCV(obs)
        self.scv_training_counter = 0
        
        # Turn on SCV training
        if self.nb_scv <= self.scv_rate:
            if has_enough_ressources([i * 5 for i in _SCV_COST], resources):
                self.scv_training_counter += 1 # First increment

        # Build barrack
        if self.nb_supply_depot >= self.supply_depot_rate and \
           self.nb_barracks < self.barracks_rate and self.barrack_in_construction == False:
            if has_enough_ressources(_BARRACKS_COST, resources):
                self.barrack_in_construction = True
                return self.build_barrack(obs)

        # Build refinery
        if self.nb_barracks >= self.barracks_rate and \
           self.nb_refineries < self.refineries_rate and self.refinery_in_construction == False:
            if has_enough_ressources(_REFINERY_COST, resources):
                return self.build_refinery(obs)

        # Train Marine
        if self.marine_training_counter > 0 and self.marine_training_counter < 5:
            self.marine_training_counter += 1
            return self.train_Marine(obs)
        self.marine_training_counter = 0
        
        # Turn on Marine training
        if self.nb_barracks > 0 and self.nb_marines < self.marines_rate:
            if has_enough_ressources([i * 5 for i in _MARINE_COST], resources):
                self.marine_training_counter += 1

        # Increment rates
        if self.nb_marines >= self.marines_rate:
            if self.supply_depot_rate < 8:
                self.supply_depot_rate += 3
            if self.barracks_rate < 2:
                self.barracks_rate += 1
            if self.scv_rate < 25:
                self.scv_rate += 6
            if self.marines_rate > 60:
                self.attack_mode_on = True
            else:
                self.marines_rate += 7
            self.adjust_camera(1, 1)
            return define_action(obs, _MOVE_CAMERA, [self.camera_location])

        # print("no op")
        return _FUNCTIONS.no_op()

    def build_refinery(self, obs):
        if self.inactive_scv_selected == False and self.random_scv_selected == False:
            return self.select_unit_or_building(obs, "scv")

        if _BUILD_REFINERY_SCREEN in obs.observation.available_actions:
            self.refinery_in_construction = True
            target = get_vespene_coord(obs)
            print("TARGET of payed refinery is [%d, %d]" %(target[0], target[1]))
            self.spent_on_refinery += sum(_REFINERY_COST)
            # return _FUNCTIONS.Move_screen("now", target)
            return _FUNCTIONS.Build_Refinery_screen("queued", target)

        self.inactive_scv_selected = False
        self.random_scv_selected = False
        print("\nFailed to select %s \n" %("a random worker" if self.random_scv_selected else ("a idle worker" if self.inactive_scv_selected else "anything")))
        return _FUNCTIONS.no_op()

    def build_barrack(self,obs):
        if self.inactive_scv_selected == False and self.random_scv_selected == False:
            return self.select_unit_or_building(obs, "scv")

        if _BUILD_BARRACKS_SCREEN in obs.observation.available_actions:
            target = self.get_new_barracks_location(obs)
            if target == [-1,-1]:
                self.barrack_in_construction = False
                return _FUNCTIONS.no_op()
            
            print("Target of payed br is [%d, %d]" %(target[0], target[1]))
            self.spent_on_barracks += sum(_BARRACKS_COST)
            # return _FUNCTIONS.Move_screen("now", target)
            return _FUNCTIONS.Build_Barracks_screen("queued", target)

        print("failed")
        return _FUNCTIONS.no_op()
    
    def build_supply_depot(self, obs):
        if self.inactive_scv_selected == False and self.random_scv_selected == False:
            return self.select_unit_or_building(obs, "scv")

        if self.supply_depot_construction_tries > 10:
            self.supply_depot_construction_tries = 0
            return self.approach_camera_to_center(obs)
        
        if _BUILD_SUPPLYDEPOT_SCREEN in obs.observation.available_actions:
            target = self.get_new_supply_depot_location(obs)            
            if target == [-1,-1]:
                self.supply_depot_in_construction = False
                return _FUNCTIONS.no_op()

            self.supply_depot_in_construction = True
            print("Target of payed sp is [%d, %d]" %(target[0], target[0]))
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
                self.camera_location = [18,21] # corrects camera location
        else:
            unit_type = obs.observation.feature_screen[_UNIT_TYPE]
            sp_y, sp_x = (unit_type == units.Terran.SupplyDepot).nonzero()
            if sp_x == []:
                self.supply_depot_last_location = [-1,-1]
                return self.supply_depot_last_location
            
            rand_idx = randrange(len(sp_x))
            if self.spawned_right_side:
                self.supply_depot_last_location[1] = sp_y[rand_idx] + 4
            else:
                self.supply_depot_last_location[1] = sp_y[rand_idx] - 4
                
            while self.supply_depot_last_location[0] < 0 or self.supply_depot_last_location[0] > 83 or \
                  self.supply_depot_last_location[1] < 0 or self.supply_depot_last_location[1] > 83:
                rand_idx = randrange(len(sp_x))
                self.supply_depot_last_location[0] = sp_x[rand_idx] + (5 if self.spawned_right_side else -5)
                self.supply_depot_last_location[1] = sp_y[rand_idx] + (5 if self.spawned_right_side else -5)

        return self.supply_depot_last_location

    def get_new_barracks_location(self, obs):
        unit_type = obs.observation.feature_screen[_UNIT_TYPE]
        sp_y, sp_x = (unit_type == units.Terran.Barracks).nonzero()

        if len(sp_y) == 0:
            if self.spawned_right_side:
                #                            [29, 29]
                self.barrack_last_location = [25, 20]
            else:
                self.barrack_last_location = [73, 25]
        else:
            rand_idx = randrange(len(sp_x))
            self.barrack_last_location[0] = sp_x[rand_idx] + randrange(-5,5)
            self.barrack_last_location[1] = sp_y[rand_idx] + randrange(-5,5)
                
            while self.barrack_last_location[0] < 0 or self.barrack_last_location[0] > 83 or \
                  self.barrack_last_location[1] < 0 or self.barrack_last_location[1] > 83:
                rand_idx = randrange(len(sp_x))
                self.barrack_last_location[0] = sp_x[rand_idx] + randrange(-5,5)
                self.barrack_last_location[1] = sp_y[rand_idx] + randrange(-5,5)

        return self.barrack_last_location
    
    def select_unit_or_building(self, obs, unit_or_building):
        if unit_or_building == "scv":
            if self.random_scv_selected == False:
                self.random_scv_selected = True
                self.inactive_scv_selected = False
                self.commandcenter_selected = False
                self.marine_selected = False
                self.barrack_selected = False
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
                self.barrack_selected = False
                unit_type = obs.observation.feature_screen[_UNIT_TYPE]
                commandcenter_y, commandcenter_x = (unit_type == units.Terran.CommandCenter).nonzero()
                cc_center_x = numpy.mean(commandcenter_x, axis=0).round()
                cc_center_y = numpy.mean(commandcenter_y, axis=0).round()
                target = [cc_center_x, cc_center_y]
                return _FUNCTIONS.select_point("select", target)
        elif unit_or_building == "br":
            if self.barrack_selected == False:
                self.barrack_selected = True
                self.commandcenter_selected = False
                self.inactive_scv_selected = False
                self.random_scv_selected = False
                self.marine_selected = False
                target = get_barracks_coord(obs)
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

    def train_Marine(self, obs):
        if self.barrack_selected == False:
            return self.select_unit_or_building(obs, "br")
        
        if _TRAIN_MARINE_QUICK in obs.observation.available_actions:
            self.nb_marines += 1
            self.spent_on_marines_training += sum(_MARINE_COST)
            print("started training of a marine")
            self.barrack_selected = False
            return _FUNCTIONS.Train_Marine_quick("queued")
        print("something failed while training a marine")
        self.barrack_selected = False
        
        return _FUNCTIONS.no_op()

    def approach_camera_to_center(self, obs):
        dest = [39,45] if self.spawned_right_side else [20,23]
        return define_action(obs, _MOVE_CAMERA, [dest])

    def adjust_camera(self, incX, incY):
        if self.camera_location[0]  + incX > 62 or self.camera_location[0] + incX < 2:
            self.camera_location[0] = randrange(63)
        else:
            self.camera_location[0] += -1 if self.spawned_right_side else 1 * incX;

        if self.camera_location[1]  + incY > 62 or self.camera_location[1] + incY < 2:
            self.camera_location[1] = randrange(63)
        else:
            self.camera_location[1] += 1 if self.spawned_right_side else -1 * incY;
        
    def print_state(self):
        print("----------------------------")
        print("nb_scv %d/%d" %(self.nb_scv, self.scv_rate))
        print("nb_marines %d/%d" %(self.nb_marines, self.marines_rate))
        print("nb_supply_depot %d/%d" %(self.nb_supply_depot, self.supply_depot_rate))
        print("nb_barracks %d/%d" %(self.nb_barracks, self.barracks_rate))
        print("nb_refineries %d/%d" %(self.nb_refineries, self.refineries_rate))
        print("----------------------------")
