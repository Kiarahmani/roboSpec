import json


#### POSITIVE SAMPLES
# Read data from file1
with open('pips/highway_input_demos.json', 'r') as file:
    data1 = json.load(file)

# Read data from file2
with open('demos/repaired_samples.json', 'r') as file:
    data2 = json.load(file)

# Append data2 to data1
data1.extend(data2)

# Write the appended list back to file1.json
with open('pips/highway_input_demos.json', 'w') as file:
    json.dump(data1, file)




# NEGATIVE SAMPLES:
# Read data from the original file
with open('pips/highway_input_negative_demos.json', 'r') as file:
    data1 = json.load(file)

# Read data from newly generated negative samples
with open('demos/negative_samples.json', 'r') as file:
    data2 = json.load(file)

# Append data2 to data1
data1.extend(data2)

# Write the appended list back to the original json file
with open('pips/highway_input_negative_demos.json', 'w') as file:
    json.dump(data1, file)
