
import json
from src.utils import *

def policy_ground_truth(sample):
    """Ground truth policy."""
    x_diff = sample["x_diff"]['value']
    v_diff = sample["v_diff"]['value']
    pre = sample["start"]['value']

    fast_to_slow = ((v_diff**2) / 2 - x_diff > - 30) and v_diff < 0
    slow_to_fast = ((v_diff**2) / 2 + x_diff > 30) and v_diff > 0

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
    return post


# this holds for the first 80 seconds of the demo
# returns +1 if the actual value of the sample is above the threshold
# returns -1 if the actual value of the sample is below the threshold
# returns 0 if the actual value of the sample is within the threshold 

def LS1(sample, time):
    assert time in range(80)
    x_diff = sample["x_diff"]['value']
    if x_diff > 0.13333*time + 22:
        return +1
    elif x_diff < 0.13333*time + 18:
        return -1
    else:
        return 0


def LS2(sample, time):
    assert time >= 80
    x_diff = sample["x_diff"]['value']
    if x_diff > 31:
        return +1
    elif x_diff < 29:
        return -1
    else:
        return 0



def value_limit_repair(signal, lo, hi, beging_idx, end_idx, original_trace):
    repaired_samples = []
    original_trace = original_trace[1:]
    mismatch_indices = []
    # these are automatically detected based on the given spec
    indices_chosen_for_repair = []

    for i, sample in enumerate(original_trace):

        x_diff = round(sample["x_diff"]['value'], 2)
        v_diff = round(sample["v_diff"]['value'], 2)
        pre = sample["start"]['value']
        original_post = sample["output"]['value']
        gt_post = policy_ground_truth(sample=sample)

        # automatically (without using GT) detect if the post action in the current sample is wrong
        if i in range(80):
            print (green(f'Linear Specification #1: {LS1(sample, i)}'))
        if i >= 80:
            print (blue(f'Linear Specification #2: {LS2(sample, i)}'))

        print(f'Analyzing Sample #{i}')
        print(f'   x={x_diff}')
        print(f'   v={v_diff}')
        print(f'   org={pre}->{original_post}')
        print(f'   gt post  =  {gt_post}')
        if gt_post != original_post:
            mismatch_indices.append(i)
            print(red('   MISMATCH!'))

        print('-'*85)

    print(mismatch_indices, f'\n{len(mismatch_indices)=}')
    return repaired_samples


# Specify the directory containing the JSON files
file_name = 'plots/policy_ldips/ldips_trace__103153.json'
with open(file_name, 'r') as file:
    samples = json.load(file)
    repaired_samples = value_limit_repair(
        signal='x_diff', lo=29, hi=31, beging_idx=120, end_idx=500, original_trace=samples)
