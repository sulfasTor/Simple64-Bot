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

        self.nb_scv = 12
        self.nb_harvest_gather = 0
        self.nb_supply_depot = 0
        self.nb_scv_in_train = 0
        self.nb_supply_depot_in_build = 0
        self.prev_total_value_structures = 400
        self.inactive_scv_selected = False
        self.random_scv_selected = False
        self.commandcenter_selected = False
        self.attack_mode_on = False
        self.harvest_mode_on = True
        self.enemy = None        
                
    def step(self, obs):
        super(Bot64, self).step(obs)

        # Find enemy seen on screen
        collected_minerals = obs.observation.score_cumulative.collected_minerals
        self.enemy= xy_locs(obs.observation.feature_screen.player_relative == _PLAYER_ENEMY)

        if self.enemy:
            if not _ATTACK_SCREEN in obs.observation.available_actions:
                return define_action(obs, _SELECT_RECT, [_SELECT, [0,0], [83,83]])

            if not self.attack_mode_on:
                target = self.enemy[numpy.argmax(numpy.array(self.enemy)[:, 1])]
                self.attack_mode_on = True
                self.harvest_mode_on = False
                return define_action(obs, _ATTACK_SCREEN, [_SELECT, target])

        self.attack_mode_on = False
        if not self.harvest_mode_on:
            self.harvest_mode_on = True
            return define_action(obs, _HARVEST_RETURN_QUICK, [_NOT_QUEUED])

        if collected_minerals > 100 and collected_minerals < 200:
            return self.train_SCV(obs)

        if collected_minerals > 200:
            return self.build_supply_depot(obs, 0, 0)
        
        return _FUNCTIONS.no_op()
