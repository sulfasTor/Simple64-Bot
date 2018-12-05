from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pysc2.lib import units

import sys
import numpy as np
import time

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
        
# Functions
_SELECT_IDLE_WORKER = actions.FUNCTIONS.select_idle_worker.id
_HARVEST_GATHER_SCREEN = actions.FUNCTIONS.Harvest_Gather_screen.id
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_TRAIN_SCV_QUICK = actions.FUNCTIONS.Train_SCV_quick.id
_BUILD_SUPPLYDEPOT_SCREEN = actions.FUNCTIONS.Build_SupplyDepot_screen.id

# python3 -m pysc2.bin.agent --map Simple64 --agent agent.Bot64
class Bot64(base_agent.BaseAgent):

    def __init__(self):
        super(Bot64, self).__init__()

    def setup(self, obs_spec, action_spec):
        super(Bot64, self).setup(obs_spec, action_spec)
        if "feature_units" not in obs_spec:
            raise Exception("feature_units observation not active. Activate it with --use_feature_units")    

    def reset(self):
        
        
    def step(self, obs):
        super(Bot64, self).step(obs)
