import json


def policy(start_a, x, v):

    slow_to_fast = x > 15.0
    fast_to_slow = x > 28.0

    if start_a == 'SLOWER':
        if slow_to_fast:
            post = "FASTER"
        else:
            post = "SLOWER"
    elif start_a == 'FASTER':
        if fast_to_slow:
            post = "SLOWER"
        else:
            post = "FASTER"
    else:
        raise Exception('unknown start action')
    return post


def cons_with_policy(start_a, end_a, x, v):
    return policy(start_a=start_a, x=x, v=v) == end_a


if __name__ == "__main__":
    print ('+'*60)
    with open('tests/positive_samples.json', 'r') as file:
        samples = json.load(file)
        iter = 0
        for sample in samples:
            pre = sample['start']['value']
            x = round(sample['x_diff']['value'], 2)
            v = round(sample['v_diff']['value'], 2)
            a = sample['acc']['value']
            post = sample['output']['value']
            print(f'(+)  #{iter}  ', pre, '-->', post, '   ', f'{x = }'.ljust(10,
                  ' '), f'{v = }'.ljust(10,
                  ' '), cons_with_policy(pre, post, x, v))
            iter += 1
    print ('-'*60)
    with open('tests/negative_samples.json', 'r') as file:
        samples = json.load(file)
        iter = 0
        for sample in samples:
            pre = sample['start']['value']
            x = round(sample['x_diff']['value'], 2)
            v = round(sample['v_diff']['value'], 2)
            a = sample['acc']['value']
            post = sample['output']['value']
            print(f'(-)  #{iter}  ', pre, '-->', post, '   ', f'{x = }'.ljust(10,
                  ' '), f'{v = }'.ljust(10,
                  ' '), cons_with_policy(pre, post, x, v))
            iter += 1
    pass


""" 
# To run pips on the positive_samples.json file  
cd ~/roboSpec
rm ./pips/solutions/*.json 
./pips/bin/ldips-l3 -lib_file pips/ops/highway_op_library.json  -neg_ex_file tests/negative_samples.json -min_accuracy 1 -multi_thread -ex_file tests/positive_samples.json -out_dir "pips/solutions/" -debug -feat_depth 3 -sketch_depth 3 -window_size 0 
python scripts/translate_solutions_to_python.py

# Single Cmd:
cd ~/roboSpec && rm ./pips/solutions/*.json && ./pips/bin/ldips-l3 -neg_ex_file tests/negative_samples.json -lib_file pips/ops/highway_op_library.json  -min_accuracy 1 -multi_thread -ex_file tests/positive_samples.json -out_dir "pips/solutions/" -debug -feat_depth 3 -sketch_depth 3 -window_size 0 && python scripts/translate_solutions_to_python.py
"""
