import json
import mtl
import os


def check_desired_distance(dist):
    if dist < 31 and dist > 29:
        return (1/abs(dist - 30))
    else:
        return -1 * abs(dist - 30)


def B(dist):
    if dist > 5.1:
        return +1
    else:
        return -1

# Specify the directory containing the JSON files
directory = 'plots/policy_ground_truth'
for filename in os.listdir(directory):
    if filename.endswith('.json'):  # Check if the file has a .json extension
        file_path = os.path.join(directory, filename)  # Get the full path of the file
        
        with open(file_path, 'r') as file:
            print ("<<<<<",file_path.replace('plots/policy_ground_truth/',''), ">>>>>")
            samples = json.load(file)
            
            dists = {'desired_distance': [(i, check_desired_distance(x['x_diff']['value']))
                        for i, x in enumerate(samples)]}
            desired_distance = mtl.parse('desired_distance')
            phi = (desired_distance.always()).eventually(lo=0, hi=100)


            #for (i, dist) in dists['desired_distance']:
            #    print(i, dist)

            
            print(f'|=? {phi}:', phi(dists, quantitative=False))
            print('-'*80)
