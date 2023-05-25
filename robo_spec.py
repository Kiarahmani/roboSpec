import json
import sys
import os
import random
import numpy as np
import gymnasium as gym
from matplotlib import pyplot as plt
from learned_policy import policy_ldips
from src.plotter import plot_series
from src.simulate import *
from src.utils import analyze_trace, save_trace_to_json

EGO_SPEED_RANGE_LOW = 28  # [m/s]
EGO_SPEED_RANGE_HIGH = 40  # [m/s]
EGO_SPEED_INTERVAL = 1  # [m/s]

DURATION = 60  # [s]

DESIRED_DISTANCE = 30  # [m] Desired distance between ego and other vehicle

# [m] Minimum distance between ego and other vehicle in initial state
MIN_DIST = 10
# [m] Maximum distance between ego and other vehicle in initial state
MAX_DIST = 10
D_CRASH = 5  # [m] Distance at which crash occurs in simulation

# set this to any value n>0 if you want to sample n elements for each transition type (e.g. SLOWER->FASTER) to be included in the demo.json
SAMPLES_NUMBER_PER_TRANSITION = 10

_ego_speed_num_points = (
    int(EGO_SPEED_RANGE_HIGH - EGO_SPEED_RANGE_LOW) // EGO_SPEED_INTERVAL + 1
)
_ego_speeds = np.linspace(
    EGO_SPEED_RANGE_LOW, EGO_SPEED_RANGE_HIGH, _ego_speed_num_points
)

_dist_interval = 1
_dist_num_points = int(MAX_DIST - MIN_DIST) // _dist_interval + 1
# space between ego and other is vehicle_distance = 30 / vehicle_density
vehicle_densities_choices = np.linspace(
    30 / MAX_DIST, 30 / MIN_DIST, _dist_num_points)

config = {
    "lanes_count": 1,
    "duration": DURATION,
    "policy_frequency": 10,
    "simulation_frequency": 40,
    "screen_width": 1500,
    "observation": {
        "type": "Kinematics",
        "vehicles_count": 2,
        "features": ["x", "vx", "presence"],
        "absolute": True,
        "normalize": False,
    },
    "action": {
        "type": "DiscreteMetaAction",
        "target_speeds": _ego_speeds,  # Speed range of ego vehicle
    },
    "vehicles_count": 1,
    "other_vehicles_type": "src.my_vehicle.MyVehicle",
    "vehicles_density": random.choice(vehicle_densities_choices)
}


def policy_ground_truth(state):
    """Ground truth policy."""
    x_diff = state.get("x_diff")
    v_diff = state.get("v_diff")

    pre = state.get("start")
    fast_to_slow = ((v_diff**2) / 2 - x_diff > -
                    DESIRED_DISTANCE) and v_diff < 0
    fast_to_fast = ((v_diff**2) / 2 + x_diff > DESIRED_DISTANCE) and v_diff > 0
    slow_to_fast = ((v_diff**2) / 2 + x_diff > DESIRED_DISTANCE) and v_diff > 0
    slow_to_slow = ((v_diff**2) / 2 - x_diff > -
                    DESIRED_DISTANCE) and v_diff < 0

    if pre == "SLOWER":
        if slow_to_fast:
            post = "FASTER"
        elif slow_to_slow:
            post = "SLOWER"
        else:
            post = "SLOWER"
    elif pre == "FASTER":
        if fast_to_slow:
            post = "SLOWER"
        elif fast_to_fast:
            post = "FASTER"
        else:
            post = "FASTER"
    return post


def spec_1(trace):
    last_state = trace[-1]
    if abs(last_state.get("x_diff") - DESIRED_DISTANCE) > 1:
        return False
    else:
        return True



if __name__ == "__main__":
    # set the desired policy
    if len(sys.argv) != 2:
        print("Usage: python highway_one_lane_simulator.py <policy>")
        sys.exit(1)

    if sys.argv[1] == 'gt':
        env = gym.make("highway-v0", render_mode="rgb_array")
        env.configure(config)
        init_obs=env.reset()
        sat, trace = run_simulation(
            policy_ground_truth, spec_1, show=True, env=env, init_obs=init_obs)
        plot_series(policy=policy_ground_truth, trace_1=trace, trace_2=None)
        # we don't need the first element other than for plotting purposes
        trace.pop()

        # if you want to have a fix and same number of samples for each type of transition
        if SAMPLES_NUMBER_PER_TRANSITION > 0:
            sampled_trace = []
            samples_map = analyze_trace(trace=trace)
            for k in samples_map.keys():
                if len(samples_map[k]) >= SAMPLES_NUMBER_PER_TRANSITION:
                    for s in random.sample(samples_map[k], SAMPLES_NUMBER_PER_TRANSITION):
                        sampled_trace.append(s)
                else:
                    for s in samples_map[k]:
                        sampled_trace.append(s)
            save_trace_to_json(trace=sampled_trace,
                               filename='demos/sampled_demo.json')
            save_trace_to_json(trace=trace, filename='demos/full_demo.json')
    ########
    elif sys.argv[1] == 'ldips':
        env = gym.make("highway-v0", render_mode="rgb_array")
        env.configure(config)
        init_obs = env.reset()
        sat, trace_ldips = run_simulation(
            policy_ldips, spec_1, show=True, env=env, init_obs=init_obs)
        env.reset()
        _, trace_gt = run_simulation(
            policy_ground_truth, spec_1, show=True, env=env, init_obs=init_obs)

        plot_series(policy=policy_ldips, trace_1=trace_ldips, trace_2=trace_gt)
        # save_trace_to_json(trace=trace, filename='demos/full_demo.json')
        
        # we don't need the first element other than for plotting purposes
        trace_ldips.pop()

        # HACKY CHEATY repair using GT
        violation_found = False
        repaired_samples_json = []
        cex_cnt = 0
        fast_to_slow_repair = 0
        slow_to_fast_repair = 0
        trace_ldips_popped = trace_ldips[1:]
        random.shuffle(trace_ldips_popped)
        for i, s in enumerate(trace_ldips_popped):
            gt_action = policy_ground_truth(s)
            if s.state['output']['value'] != gt_action:
                if gt_action == 'FASTER':
                    slow_to_fast_repair += 1
                else:
                    fast_to_slow_repair += 1

                cex_cnt += 1
                violation_found = True
                # print('State BEFORE repair:')
                # print(pretty_str_state(state=s, iter=i))
                # print("GT prediction: ", gt_action)
                s.state['output']['value'] = gt_action
                repaired_samples_json.append(s.state)
                # print('State AFTER repair:')
                # print(pretty_str_state(state=s, iter=i))
                # only one state should be repaired per iteration
                if cex_cnt >= 20:
                    break

        print('-'*110)
        if violation_found:
            # print('All repaired samples:\n')
            # print(repaired_samples_json)
            print('Repaired sample stats:',
                  f'{fast_to_slow_repair=}', f'{slow_to_fast_repair=}')
            # write the repaiered samples into a file
            with open('demos/repaired_samples.json', "w") as f:
                f.write(json.dumps(repaired_samples_json))
        else:
            print('No violation was found!')
    else:
        raise Exception('policy should be either gt or ldips')
