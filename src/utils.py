import json
import numpy as np


def ranges(data):
    result = []
    #print (f'{data=}')
    if not data:
    #    print ('no data')
        return result
    idata = iter(data)
    first = prev = next(idata)
    for following in idata:
        if following - prev == 1:
            prev = following
        else:
            result.append((first, prev + 1))
            first = prev = following
    # There was either exactly 1 element and the loop never ran,
    # or the loop just normally ended and we need to account
    # for the last remaining range.
    result.append((first, prev+1))
    return result

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

def DEPRECATED_draw_spec(x1,y1,x2,y2,w):
        a = (y2-y1)/(x2-x1) # slope
        b = y1-x1*a  # intercept
        # calculate intercept of the edges
        c1 = b+w/2  # y-intercept of first line
        c2 = b-w/2  # y-intercept of second line 
        x = np.linspace(x1, x2, 1000)
        y1 = a * x + c1
        y2 = a * x + c2
        return x, y1, y2

def save_trace_to_json(trace, filename="demo.json"):
    trace_json = json.dumps([s.state for s in trace])
    with open(filename, "w") as f:
        f.write(trace_json)

def red(text):
    return "\033[91m" + text + "\033[0m"
def green(text):
    return "\033[92m" + text + "\033[0m"
def orange(text):
    return "\033[93m" + text + "\033[0m"
def blue(text):
    return "\033[94m" + text + "\033[0m"

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