from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pysc2.lib import units

import sys, numpy, time

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
_ATTACK_SCREEN = actions.FUNCTIONS.Attack_screen.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_SELECT_RECT = actions.FUNCTIONS.select_rect.id
_NO_OP = actions.FUNCTIONS.no_op.id
_FUNCTIONS = actions.FUNCTIONS

# Parameters
_NOT_QUEUED = [0]
_SCREEN = [0]
_SELECT = [0]

#COSTS
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

def xy_locs(mask):
    y, x = mask.nonzero()
    return list(zip(x, y))

def define_action(obs, action_id, args=[]):
    if action_id in obs.observation.available_actions:
        return actions.FunctionCall(action_id, args)
    else:
        return actions.FunctionCall(_NO_OP, [])

def has_enough_ressources(wanted_ressource, ressources):
    return wanted_ressource[0] <= ressources[0] and wanted_ressource[1] <= ressources[1]

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

        # buildings
        self.nb_supply_depot = 0
        self.nb_supply_depot_in_build = 0
        self.nb_barracks = 0

        # units
        self.nb_scv = 12
        self.nb_marines = 0
        self.nb_harvest_gather = 0
        self.nb_scv_in_train = 0

        # rates
        self.supply_depot_rate = 1
        self.barracks_rate = 0
        self.scv_rate = nb_scv

        # flags
        self.scv_training_counter = 0
        self.marine_training_counter = 0
        self.commandcenter_selected = False
        self.inactive_scv_selected = False
        self.random_scv_selected = False
        self.marine_selected = False
        self.attack_mode_on = False
        self.enemy = None
                
    def step(self, obs):
        super(Bot64, self).step(obs)

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
        if self.nb_supply_depot <= self.supply_depot_rate:
            if has_enough_ressources(_SUPPLY_DEPOT_COST, resources):
                self.barracks_rate += 1 if self.nb_supply_depot >=  2 else 0
                return self.build_supply_depot()

        # Build barrack
        if self.nb_barracks < self.barracks_rate:
            if has_enough_ressources(_BARRACKS_COST, resources):
                return self.build_barrack()

        # Train SCV
        if self.scv_training_counter > 0 and self.scv_training_counter < 5:
            self.scv_training_counter += 1
            return self.train_SCV(obs)
        self.scv_training_counter = 0
        
        # Train more SCVs
        if self.nb_scv <= self.scv_rate:
            if has_enough_ressources([i * 5 for i in _SCV_COST], resources):
                self.scv_rate += 1
                self.scv_training_counter += 1

        # Train Marine
        if self.marine_training_counter > 0 and self.marine_training_counter < 5:
            self.marine_training_counter += 1
            return self.train_Marine(obs)
        self.marine_training_counter = 0
        
        # Train more Marines
        if self.nb_marine <= self.marine_rate:
            if has_enough_ressources([i * 5 for i in _MARINE_COST], resources):
                self.marine_rate += 1
                self.marine_training_counter += 1
    
        return _FUNCTIONS.no_op()
