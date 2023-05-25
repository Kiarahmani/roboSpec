import json

def pretty_str_state(state, iter):
    pre_action = state.state['start']['value']
    post_action = state.state['output']['value']
    distance = state.state['x_diff']['value']
    # v_self = state.state['v_self']['value']
    # v_front = state.state['v_front']['value']
    v_diff = state.state['v_diff']['value']
    if iter:
        result = '(' + str(iter) + ') '
    else:
        result = ''
    result += (pre_action + ' -> ' + post_action + ':\n')
    tab = '   '
    result += tab + 'distance: ' + str(distance) + '\n'
    # result += tab + 'v_self: ' + str(v_self) + '\n'
    # result += tab + 'v_front: ' + str(v_front) + '\n'
    result += tab + 'v_diff: ' + str(v_diff)
    return result


def save_trace_to_json(trace, filename="demo.json"):
    trace_json = json.dumps([s.state for s in trace])
    with open(filename, "w") as f:
        f.write(trace_json)



# takes a trace and returns a map with keys being transitions and values being the samples from the trace
def analyze_trace(trace):
    result = {('SLOWER', 'SLOWER'): [], ('SLOWER', 'FASTER'): [],
              ('FASTER', 'FASTER'): [], ('FASTER', 'SLOWER'): []}
    iter = 0
    for s in trace:
        # print(pretty_str_state(s, iter))
        iter += 1
        # print('-'*50)
        pre_action = s.state['start']['value']
        if pre_action:
            post_action = s.state['output']['value']
            result[(pre_action, post_action)].append(s)
    return result