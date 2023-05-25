# this file should be copied into the pips container
# this script reads the json files in the same directory and translates the pips expressions into pythonic form
#!/usr/bin/python3


import json
import os

policy_template = """
######################################
# THIS FILE IS AUTOMATICALLY GENERATED FROM PIPS'S SOLUTION
# DO NOT EDIT 
######################################


def policy_ldips(state):
    x_diff = state.get("x_diff")
    v_diff = state.get("v_diff")
    acc = state.get("acc")
    #v_self = state.get("v_self")
    #v_front = state.get("v_front")


    ### PIPS LEARNED EXPRESSIONS
XXX
    ###

    pre = state.get("start")
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
"""


def translate_json_to_expression(json_str):
    data = json.loads(json_str)
    expression = translate_node(data)
    return expression


def translate_node(node):
    if node["node"] == "BinOp":
        left = translate_node(node["left"])
        op = translate_operator(node["op"])
        right = translate_node(node["right"])
        return f"({left} {op} {right})"
    elif node["node"] == "Var":
        return node["name"]
    elif node["node"] == "UnOp" and node["op"] == "Sq":
        return "(" + translate_node(node["input"]) + ") ** 2"
    elif node["node"] == "UnOp" and node["op"] == "Halve":
        return "(" + translate_node(node["input"]) + ")/2"
    elif node["node"] == "Param":
        return translate_parameter(node["value"])
    elif node["node"] == 'Feature':
      return translate_node(node["value"])
    else:
        #return None
        raise ValueError(f"Unsupported node type: {node['node']}")

def translate_operator(op):
    if op == "Gt":
        return ">"
    elif op == "DividedBy":
        return "/"
    elif op == "Lt":
        return "<"
    elif op == "Minus":
        return "-"
    elif op == "Plus":
        return "+"
    elif op == "And":
        return "and"
    elif op == "Or":
        return "or"
    else:
        raise ValueError(f"Unsupported operator: {op}")

def translate_parameter(param):
    if param["node"] == "Num":
        return str(param["value"])
    else:
        raise ValueError(f"Unsupported parameter type: {param['node']}")

def translate_feature(param):
    if param["node"] == "Var":
        return str(param["name"])
    else:
        raise ValueError(f"Unsupported feature type: {param['node']}")


# Get the current directory
current_directory = os.getcwd()

# Get a list of all files in the current directory
#files = os.listdir(current_directory)
files = os.listdir('pips/solutions/')


# Filter out only the text files
text_files = [file for file in files if file.endswith(".json")]

exps = ''
# Open and read the contents of each text file
for file in text_files:
    with open('pips/solutions/'+file, "r") as f:
        #print(f"{file}:".replace('.json','').replace('_',' -> '))
        exps += '    '+f"{file}".replace('.json','').replace('_','_to_').lower().replace('er','') + "=" + translate_json_to_expression(f.read()) + '\n'

# Specify the file path and the string to write
file_path = "learned_policy.py"  # Replace with your desired file path
# Write the string to the file using 'with' statement
with open(file_path, "w") as file:
    file.write(policy_template.replace('XXX',exps))