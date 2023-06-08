import json
import sys
import os
import random
import numpy as np
import gymnasium as gym
from matplotlib import pyplot as plt
from src.Spec import Spec
from learned_policy import policy_ldips
from src.plotter import  plot_single_series
from src.simulate import *
from src.utils import analyze_trace, save_trace_to_json

EGO_SPEED_RANGE_LOW = 20  # [m/s]
EGO_SPEED_RANGE_HIGH = 40  # [m/s]
EGO_SPEED_INTERVAL = 2  # [m/s]

DURATION = 60  # [s]

DESIRED_DISTANCE = 30  # [m] Desired distance between ego and other vehicle

# [m] Minimum distance between ego and other vehicle in initial state
MIN_DIST = 10
# [m] Maximum distance between ego and other vehicle in initial state
MAX_DIST = 10
D_CRASH = 5  # [m] Distance at which crash occurs in simulation

# set this to any value n>0 if you want to sample n elements for each transition type (e.g. SLOWER->FASTER) to be included in the demo.json
SAMPLES_NUMBER_PER_TRANSITION = 3

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
    slow_to_fast = ((v_diff**2) / 2 + x_diff > DESIRED_DISTANCE) and v_diff > 0

    if pre == "SLOWER":
        if slow_to_fast:
            post = "FASTER"
        else:
            post = "SLOWER"
    elif pre == "FASTER":
        if fast_to_slow:
            post = "SLOWER"
        else:
            post = "FASTER"
    else:
        raise Exception(f'unknown {pre=}')
    return post


# Repair using GT: the human chooses which samples to repair and how many
def repair_by_human_and_gt(gt_policy, ldips_trace):
    repaired_samples_json = []
    while True:
        user_input = input("Enter an index for repair or 'q' to quit: ")
        if user_input == 'q':
            break
        if user_input.isdigit():
            index = int(user_input)
            if index <= 0 or index >= len(ldips_trace) - 1:
                continue
            s = ldips_trace[index]
            gt_action = gt_policy(s)
            ldips_action = s.state['output']['value']
            if ldips_action != gt_action:
                print(
                    f'Sample repaired at {index=}: {ldips_action} --> {gt_action}')
                s.state['output']['value'] = gt_action
                repaired_samples_json.append(s.state)
            else:
                print(
                    f'The action taken by the policy is consistent with the ground-truth at {index=}')
        else:
            print("Invalid input. Please enter an index or 'q' to quit.")
    return repaired_samples_json


# Repair using GT: randomly choose samples that differ from gt and repair
def random_repair_using_gt(gt_policy, ldips_trace, total_repair_cnt):
    repaired_samples_json = []
    cex_cnt = 0
    fast_to_slow_repair = 0
    slow_to_fast_repair = 0
    trace_ldips_popped = ldips_trace[1:]
    random.shuffle(trace_ldips_popped)
    for i, s in enumerate(trace_ldips_popped):
        gt_action = gt_policy(s)
        if s.state['output']['value'] != gt_action:
            if gt_action == 'FASTER':
                slow_to_fast_repair += 1
            else:
                fast_to_slow_repair += 1
            cex_cnt += 1
            s.state['output']['value'] = gt_action
            repaired_samples_json.append(s.state)
            if cex_cnt >= total_repair_cnt:
                break
    print('Repair Stats:', f'{fast_to_slow_repair=}',
          f'{slow_to_fast_repair=}')
    return repaired_samples_json


def repair_by_spec(ldips_trace):
    return []


if __name__ == "__main__":
    # set the desired policy
    if len(sys.argv) != 2:
        print("Usage: python robo_spec.py <policy>")
        sys.exit(1)

    # define specs
    specs = [Spec('include', 0, 10.5, 45, 23, 5, 'green'), Spec('include', 45, 23, 100, 29.8, 3, 'green'), Spec(
        'include', 100, 30, 300, 30, 2, 'green'), Spec('exclude', 0, 2.5, 300, 2.5, 5, 'red')]

    if sys.argv[1] == 'gt':
        env = gym.make("highway-v0", render_mode="rgb_array")
        env.configure(config)
        init_obs = env.reset(seed=5)
        trace = run_simulation(
            policy_ground_truth, show=True, env=env, init_obs=init_obs)
        # plot_series(policy=policy_ground_truth, trace_1=trace, trace_2=None)
        plot_single_series(trace=trace[1:], gt_policy=policy_ground_truth,
                           specs=specs, directory='policy_ground_truth')
        # we don't need the first element other than for plotting purposes
        trace.pop()

        # if you want to have a fix and same number of samples for each type of transition
        if SAMPLES_NUMBER_PER_TRANSITION > 0:
            sampled_trace = []
            # sampled_trace = trace[1:]
            # add 10 samples for each type of transition
            samples_map = analyze_trace(trace=trace)
            for k in samples_map.keys():
                if len(samples_map[k]) >= SAMPLES_NUMBER_PER_TRANSITION:
                    for s in random.sample(samples_map[k], SAMPLES_NUMBER_PER_TRANSITION):
                        sampled_trace.append(s)
                else:
                    for s in samples_map[k]:
                        sampled_trace.append(s)

            # add the first 50 samples too
            # for i in range(1, 50):
            #    sample = trace[i]
            #    if sample not in sampled_trace:
            #        sampled_trace.append(sample)

            save_trace_to_json(trace=sampled_trace,
                               filename='demos/sampled_demo.json')
            save_trace_to_json(trace=trace, filename='demos/full_demo.json')
    ########
    elif sys.argv[1] == 'ldips':
        env_init_seed = 5  # the value does not really matter
        env = gym.make("highway-v0", render_mode="rgb_array")
        env.configure(config)
        init_obs = env.reset(seed=5)
        trace_ldips = run_simulation(
            policy_ldips, show=True, env=env, init_obs=init_obs)
        init_obs = env.reset(seed=5)
        trace_gt = []  # run_simulation(
        # policy_ground_truth, show=True, env=env, init_obs=init_obs)

        # plot_series(policy=policy_ldips, trace_1=trace_ldips,
        #            trace_2=trace_gt, gt_policy=policy_ground_truth, specs=specs)

        plot_single_series(
            trace=trace_ldips[1:], gt_policy=policy_ground_truth, specs=specs, directory='policy_ldips')

        # we don't need the first element other than for plotting purposes
        trace_ldips.pop()

        print('-'*80)
        # repair some subset of samples using one of the existing repair functions
        # CHOOSE A REPAIR STRATEGY
        # 1
        # repaired_samples_json = random_repair_using_gt(
        #    policy_ground_truth, trace_ldips, total_repair_cnt=10)
        # 2
        repaired_samples_json = repair_by_human_and_gt(policy_ground_truth, trace_ldips)
        # 3
        # repaired_samples_json = repair_by_spec(trace_ldips)

        # write the repaired samples to a file to be used in the next iterations
        with open('demos/repaired_samples.json', "w") as f:
                f.write(json.dumps(repaired_samples_json))
        print('-'*80)

    else:
        raise Exception('policy should be either gt or ldips')
