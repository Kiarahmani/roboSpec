# use the function implemented in this file to check what percentage of all samples given to LDIPS are  consistent with the GT.
import json
from tabulate import tabulate


def policy_ground_truth(pre, x, v, a):

    slow_to_fast = ((v**2)/a + x > 30) and v > 0
    fast_to_slow = ((v**2)/a - x > -30) and v < 0

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


def learned_policy(pre, x, v, a, slow_to_fast, fast_to_slow):
    if pre == "SLOWER":
        if slow_to_fast(x, v, a):
            post = "FASTER"
        else:
            post = "SLOWER"
            
    elif pre == "FASTER":
        if fast_to_slow(x, v, a):
            post = "SLOWER"
        else:
            post = "FASTER"
    return post



slow_to_fast =lambda x,v,a:   ((v > 0.22149699926376343) and ((((v)**2 / a) + x) > 29.64337158203125))
fast_to_slow = lambda x,v,a:  (((((v)**2 / a) - x) > -30.00271987915039) and (v < -0.22149699926376343))



gt_slow_to_fast = lambda x,v,a:  ((v**2)/a + x > 30) and v > 0
gt_fast_to_slow = lambda x,v,a:  ((v**2)/a - x > -30) and v < 0



# check sanity
consistent = 0
gt_consistent = 0
with open('pips/highway_input_demos.json', 'r') as file:
    samples = json.load(file)
    iter = 0 
    for sample in samples:
        
        pre = sample['start']['value']
        x = round(sample['x_diff']['value'], 20)
        v = round(sample['v_diff']['value'], 20)
        a = sample['acc']['value']
        post = sample['output']['value']
        print (f'SAMPLE #{iter}: ',pre , '-->', post)
        iter += 1

        plicy_action = learned_policy(pre=pre, x=x, v=v, a=a, 
                                      fast_to_slow=fast_to_slow, slow_to_fast=slow_to_fast)
        gt_action = policy_ground_truth(pre=pre, x=x, v=v, a=a)

        if plicy_action == post:
            consistent += 1
        else:
            print('Inconsistent Prediction for this Sample.')
            print(f'Sample State: {x=}, {v=}, {a=}:')
            #print(f'Predictions:  {plicy_action=}, {gt_action=}')
            exp_data = [['Policy', 'slow_to_fast',  'fast_to_slow', 'Final Prediction'],
                        ['GT', gt_slow_to_fast(x,v,a),  gt_fast_to_slow(x,v,a), gt_action],
                        ['LDIPS', slow_to_fast(x,v,a),  fast_to_slow(x,v,a), plicy_action]]

            print (tabulate(exp_data, tablefmt="fancy_grid"))
        print('--'*55)
        if gt_action == post:
            gt_consistent += 1
        else:
            print('INCONSISTENCY DETECTED (gt and samples)!')

    print(f'\n\nTotal={len(samples)}, Consistent(learned)={round(consistent/len(samples),4)*100}%, Consistent(gt)={round(gt_consistent/len(samples),4)*100}%')
