from matplotlib import pyplot as plt


class LDIPSState(object):
    def __init__(self, state) -> None:
        self.state = state

    def get(self, name):
        return self.state[name]["value"]
    def set(self, name, value):
        self.state[name]["value"] = value

    def pretty_print(self):
        return 'x_diff=' + str(round(self.get('x_diff'), 2)).ljust(5, ' ') + '     ' + \
            'v_diff=' + str(round(self.get('v_diff'), 2)).ljust(5, ' ') + \
                '     ' + str(self.get('start')) + '->' + str(self.get('output'))


def dimensionless_template(name, value):
    return {
        name: {
            "dim": [0, 0, 0],
            "type": "NUM",
            "name": name,
            "value": value,
        }
    }


def distance_template(name, value):
    return {
        name: {
            "dim": [1, 0, 0],
            "type": "NUM",
            "name": name,
            "value": value,
        }
    }


def speed_template(name, value):
    return {
        name: {
            "dim": [1, -1, 0],
            "type": "NUM",
            "name": name,
            "value": value,
        }
    }


def acceleration_template(name, value):
    return {
        name: {
            "dim": [1, -2, 0],
            "type": "NUM",
            "name": name,
            "value": value,
        }
    }


def start_template(value):
    return {
        "start": {"dim": [0, 0, 0], "type": "STATE", "name": "start", "value": value}
    }


def output_template(value):
    return {
        "output": {"dim": [0, 0, 0], "type": "STATE", "name": "output", "value": value}
    }


def compute_state(obs):
    """Compute the state in LDIPS format (json object) from the given observation"""
    return {
        **distance_template("x_diff", float(obs[1][0] - obs[0][0])),
        **speed_template("v_diff", float(obs[1][1] - obs[0][1])),
        **acceleration_template("acc", float(2.0)),
    }


def compute_ldips_state(obs, prev_action):
    """Compute the LDIPS state in LDIPS format (json object) from the given observation"""
    return LDIPSState(
        {
            **start_template(prev_action),
            **compute_state(obs),
        }
    )


def compute_ldips_sample(obs, prev_action, action):
    """Compute the Full LDIPS sample in LDIPS format (json object) from the given observation"""
    return LDIPSState(
        {
            **start_template(prev_action),
            **compute_state(obs),
            **output_template(action),
        }
    )


def run_simulation(policy, show=False, env=None, init_obs=None):
    print(policy, env)
    count = 0
    stable_cnt = 0
    assert init_obs
    action = 'FASTER'  # let's assume the first action is always 'FASTER'
    action_idx = env.action_type.actions_indexes[action]
    init_state = compute_ldips_sample(init_obs[0], None, action)
    trace = [init_state]
    while True:
        count += 1
        obs, reward, done, truncated, info = env.step(action_idx)
        prev_action = action

        state = compute_ldips_state(obs, prev_action)
        action = policy(state)
        action_idx = env.action_type.actions_indexes[action]
        assert env.action_space.contains(action_idx)

        sample = compute_ldips_sample(obs, prev_action, action)
        trace.append(sample)

        # check if stability has been achieved
        if state.get("x_diff") < 32 and state.get("x_diff") > 28:
            stable_cnt += 1
        else:
            stable_cnt = 0

        if show:
            env.render()
        if done:
            break
        if truncated or state.get("x_diff") < 0 or stable_cnt > 130 or count > 300:
            # Corner case when vehicle in front goes out of view
            # remove last element from history
            trace.pop()
            break
    if show:
        plt.imshow(env.render())
    return trace
