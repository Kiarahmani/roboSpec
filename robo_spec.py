import json
import sys
import os
import random
import numpy as np
import gymnasium as gym
from matplotlib import pyplot as plt
from src.Spec import Spec
from learned_policy import policy_ldips
from src.plotter import plot_single_series
from src.simulate import *
from src.utils import analyze_trace, save_trace_to_json, ranges

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
SAMPLES_NUMBER_PER_TRANSITION = 1

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


def flip_action(a):
    assert a in {'SLOWER', 'FASTER'}
    return 'SLOWER' if a == 'FASTER' else 'FASTER'

# Repair using GT: the human chooses which samples to repair and how many


def repair_by_human_and_gt(gt_policy, ldips_trace, over_ride_gt=False):
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
            if ldips_action != gt_action or over_ride_gt:
                print(
                    f'Sample repaired at {index=}: {ldips_action} --> {gt_action}')
                s.state['output']['value'] = flip_action(ldips_action)
                repaired_samples_json.append(s.state)
            else:
                print(
                    f'The action taken by the policy is consistent with the ground-truth at {index=}, {gt_action=}')
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


def identify_spec_violations(specs, trace):
    result = {str(spec): {'L':[], 'U':[]} for spec in specs}
    for spec in specs:
        for idx, s in enumerate(trace):
            spec_begin_idx, spec_end_idx = spec.get_x_range()
            if idx not in range(spec_begin_idx, spec_end_idx):
                continue
            x_diff = s.state['x_diff']['value']
            if not spec.is_sat(idx, x_diff):
                violation_tp = 'L' if spec.get_min_valid_y(idx) > x_diff else 'U'
                result[str(spec)][violation_tp].append(idx)
    return result


# repair by heuristics
def semi_automatic_repair(specs, trace):
    repair_range = 4
    repaired_samples_json = []
    # manually choose the spec for repair
    # spec_idx = 'a'
    # while (not spec_idx.isdigit()):
    #    spec_idx = input("Enter the index of the spec to be used for repair:")
    # spec = specs[int(spec_idx)]

    # search and find the first spec that is violated
    spec = None
    for iter in specs:
        if any([not iter.is_sat(x=x, y=s.state['x_diff']['value']) for x, s in enumerate(trace)]):
            spec = iter
            break
    if not spec:
        print('All specs are satisfied')
        return []

    print(f"Attempting to repair using the given spec {str(spec)}")
    first_violation_point = None
    action_taken_at_violation = None
    for x, s in enumerate(trace):
        y = s.state['x_diff']['value']
        a = s.state['output']['value']
        # print (x, round(y,2), a, spec.is_sat(x=x, y=y))
        if not spec.is_sat(x=x, y=y):
            first_violation_point = (x, y)
            action_taken_at_violation = a
            break

    if not first_violation_point:
        print('The spec is not violated in the given trace')
    else:
        v_x, v_y = first_violation_point
        first_violation_tp = 'L' if spec.get_min_valid_y(v_x) > v_y else 'U'
        print(f'The chosen spec is violated first at index={v_x}')
        print(
            f'Searching for an index to repair based on type of violation:{first_violation_tp}')
        print(
            f'Action taken at the time of violation: {action_taken_at_violation}')
        ###############################
        if first_violation_tp == 'L':
            if action_taken_at_violation == 'FASTER':  # Wrong action at the violation time
                # Repair the actions in a window of time before violation
                for repair_iter in range(repair_range):
                    s = trace[v_x - repair_iter + 1]
                    if s.state['output']['value'] == 'FASTER':
                        s.state['output']['value'] = 'SLOWER'
                        print(
                            f'Repair Suggestion: at index={v_x - repair_iter}, action FASTER needs to be updated to SLOWER')
                        repaired_samples_json.append(s.state)
            elif action_taken_at_violation == 'SLOWER':  # Correct action at the violation time
                repair_idx = v_x
                while repair_idx >= 0:
                    s = trace[repair_idx]
                    a = s.state['output']['value']
                    if a != action_taken_at_violation:
                        # Switch to the correct action earlier
                        s.state['output']['value'] = 'SLOWER'
                        repaired_samples_json.append(s.state)
                        print(
                            f'Repair Suggestion: at index={repair_idx}, action FASTER needs to be updated to SLOWER')
                        break
                    repair_idx -= 1
            else:
                raise Exception('unexpected action type')
        ###############################
        elif first_violation_tp == 'U':
            if action_taken_at_violation == 'SLOWER':  # Wrong action at the violation time
                # Repair the actions in a window of time before violation
                for repair_iter in range(repair_range):
                    s = trace[v_x - repair_iter + 1]
                    if s.state['output']['value'] == 'SLOWER':
                        s.state['output']['value'] = 'FASTER'
                        print(
                            f'Repair Suggestion: at index={v_x - repair_iter}, action SLOWER needs to be updated to FASTER')
                        repaired_samples_json.append(s.state)
            elif action_taken_at_violation == 'FASTER':  # Correct action at the violation time
                repair_idx = v_x
                while repair_idx >= 0:
                    s = trace[repair_idx]
                    a = s.state['output']['value']
                    if a != action_taken_at_violation:
                        # Switch to the correct action earlier
                        s.state['output']['value'] = 'FASTER'
                        repaired_samples_json.append(s.state)
                        print(
                            f'Repair Suggestion: at index={repair_idx}, action SLOWER needs to be updated to FASTER')
                        break
                    repair_idx -= 1
            else:
                raise Exception('unexpected action type')
        else:
            raise Exception('unexpected violation type')
    return repaired_samples_json


def generate_negative_examples_by_human(specs, trace):
    negative_examples = []
    while True:
        user_input = input("Enter an index for repair or 'q' to quit: ")
        if user_input == 'q':
            break
        if user_input.isdigit():
            index = int(user_input)
            if index <= 0 or index >= len(trace) - 1:
                continue
            s = trace[index]
            print(f'Negative sample identified at {index=}, original actions: {s.state["start"]["value"]}->{s.state["output"]["value"]}')
            user_input = input('Accept?')

            if user_input not in {'y', 'yes', 'Y'}:
                continue
            
            print ('negative sample added')
            negative_examples.append(s.state)
        else:
            print("Invalid input. Please enter an index or 'q' to quit.")
    return negative_examples


if __name__ == "__main__":
    # set the desired policy
    if len(sys.argv) != 2:
        print("Usage: python robo_spec.py <policy>")
        sys.exit(1)

    # define specs
    specs = [Spec('include', 0, 10.5, 45, 23, 5, 'green'), Spec('include', 45, 23, 100, 29.8, 5, 'green'), Spec(
        'include', 100, 30, 300, 30, 5, 'green')  # , Spec('exclude', 0, 2.5, 300, 2.5, 5, 'red')
    ]

    if sys.argv[1] == 'gt':
        env = gym.make("highway-v0", render_mode="rgb_array")
        env.configure(config)
        init_obs = env.reset(seed=5)
        trace = run_simulation(
            policy_ground_truth, show=True, env=env, init_obs=init_obs)
        # plot_series(policy=policy_ground_truth, trace_1=trace, trace_2=None)
        plot_single_series(trace=trace[1:], gt_policy=policy_ground_truth,
                           specs=specs, directory='policy_ground_truth', synthesis_data={})
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

        with open('pips/highway_input_demos.json', 'r') as file:
            samples = json.load(file)
            no_samples = len(samples)
        with open('pips/highway_input_negative_demos.json', 'r') as file:
            neg_samples = len(json.load(file))

        synthesis_data = {'no_samples': no_samples, 'neg_samples': neg_samples}
        plot_single_series(
            trace=trace_ldips[1:], gt_policy=policy_ground_truth, specs=specs, directory='policy_ldips', synthesis_data=synthesis_data)

        # we don't need the first element other than for plotting purposes
        trace_ldips.pop()

        print('-'*80)
        # repair some subset of samples using one of the existing repair functions
        # CHOOSE A REPAIR STRATEGY
        # 1
        # repaired_samples_json = random_repair_using_gt(
        #    policy_ground_truth, trace_ldips, total_repair_cnt=10)
        # 2
        # repaired_samples_json = repair_by_human_and_gt(
        #    policy_ground_truth, trace_ldips)
        #
        # 3 semi-automatic repair
        # repaired_samples_json = semi_automatic_repair(
        #    specs=specs, trace=trace_ldips)


        # analyze the trace w.r.t. the specs
        analysis_result = identify_spec_violations(specs=specs, trace=trace_ldips)
        for k in analysis_result:
            for tp in {'U','L'}:
                print(k.ljust(50, ' '), tp, ':  ' , ranges(analysis_result[k][tp]))
        print ('-'*75)


        repaired_samples_json = []
        negative_samples_json = generate_negative_examples_by_human(
            specs, trace_ldips)


        # write the repaired samples to a file to be used in the next iterations
        with open('demos/repaired_samples.json', "w") as f:
            f.write(json.dumps(repaired_samples_json))

        # write the negative samples to a file to be used in the next iterations
        with open('demos/negative_samples.json', "w") as f:
            f.write(json.dumps(negative_samples_json))
        print('-'*80)

    else:
        raise Exception('policy should be either gt or ldips')
