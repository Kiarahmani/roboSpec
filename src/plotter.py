import datetime
import os
from matplotlib import pyplot as plt
from .utils import draw_spec, save_trace_to_json


def plot_series(policy, trace_1, trace_2, gt_policy=None):
    # the initial states in both experiments must be the same
    if trace_2:
        assert trace_1[0].state['x_diff']['value'] == trace_2[0].state['x_diff']['value']
        assert trace_1[0].state['v_diff']['value'] == trace_2[0].state['v_diff']['value']
    init_v_diff = trace_1[0].state['v_diff']['value']
    init_dist = trace_1[0].state['x_diff']['value']
    directory = 'plots/' + str(policy.__name__) + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)

    # plot x diff
    plt.clf()
    diff_series_1 = [x.state['x_diff']['value'] for x in trace_1]

    # Create x-axis values ranging from 0 to the length of the data
    x1 = range(0, len(diff_series_1))
    print(f'{x1=}')
    actions = [x.state['output']['value'] for x in trace_1]
    # Plot the sorted data as a line chart

    if trace_2:
        diff_series_2 = [x.state['x_diff']['value'] for x in trace_2]
        x2 = range(0, len(diff_series_2))
        print(f'{x2=}')
        plt.plot(x1, diff_series_1, label='ldips')
        plt.plot(x2, diff_series_2, label='gt')
        print(f'{trace_2[0].get("x_diff")}', f'{trace_1[0].get("x_diff")}')
        print(f'{trace_2[0].get("v_diff")}', f'{trace_1[0].get("v_diff")}')
    else:
        # if the second trace is not given then this is a simulation of only gt
        plt.plot(x1, diff_series_1, label='GT')

    # Add the legend
    plt.legend(loc='upper right')

    # Add labels and title to the chart
    plt.xlabel('Time (100 ms)')
    plt.ylabel("Distance (m)")
    plt.title(f'Distance Between Cars vs. Time\n{init_dist=}\n{init_v_diff=}')
    plt.grid(True)
    # Set the minimum values of the x and y axes to 0
    plt.xlim(0, 300)
    plt.ylim(0, 60)
    plt.minorticks_on()
    plt.grid(True, which='minor', linestyle='--', alpha=0.4)

    plt.axvspan(0, 1, ymin=0.0+0.025, ymax=0.025+0.025,
                facecolor='blue', edgecolor='blue', alpha=1, zorder=5)
    for i, action in enumerate(actions):
        if i == 0:
            continue  # do not show the first action since it is not part of the demonstration
        # Determine the x-coordinate range for the rectangle
        start = i
        end = i + 1
        # Determine the color based on the action
        if action == 'FASTER':
            color = 'green'
        elif action == 'SLOWER':
            color = 'red'
        else:
            color = 'blue'
        # Add the colored rectangle
        # Adjust ymin and ymax values for rectangle height
        plt.axvspan(start, end, ymin=0+0.025, ymax=0.025 +
                    0.025, facecolor=color, alpha=1, zorder=5)
    if trace_2:
        # Iterate over each action
        plt.axvspan(0, 1, ymin=0.025+0.025, ymax=0.05+0.025,
                    facecolor='orange', edgecolor='orange', alpha=1, zorder=5)
        for i, action in enumerate([x.state['output']['value'] for x in trace_2]):
            if i == 0:
                continue  # do not show the first action since it is not part of the demonstration
            # Determine the x-coordinate range for the rectangle
            start = i
            end = i + 1
            # Determine the color based on the action
            if action == 'FASTER':
                color = 'green'
            elif action == 'SLOWER':
                color = 'red'
            else:
                color = 'blue'
            # Add the colored rectangle
            # Adjust ymin and ymax values for rectangle height
            plt.axvspan(start, end, ymin=0.025+0.025, ymax=0.05 +
                        0.025, facecolor=color, alpha=1, zorder=5)

    if gt_policy:
        # Iterate over each action
        for i, s in enumerate(trace_1):
            if i == 0:
                continue  # do not show the first action since it is not part of the demonstration
            # Determine the x-coordinate range for the rectangle
            start = i
            end = i + 1
            # Determine the color based on the action
            if gt_policy(s) == 'FASTER':
                color = 'green'
            elif gt_policy(s) == 'SLOWER':
                color = 'red'
            else:
                color = 'blue'
            # Add the colored rectangle
            # Adjust ymin and ymax values for rectangle height
            plt.axvspan(start, end, ymin=0, ymax=0.025,
                        facecolor=color, alpha=1, zorder=5)

    # Add labels for the series
    if trace_2:
        plt.text(-30, 1.5, 'ldips', va='bottom', fontsize=5)
        plt.text(-30, 3, 'gt', va='bottom', fontsize=5)
        if gt_policy:
            plt.text(-30, 0, 'gt_ldips', va='bottom', fontsize=5)
    else:
        plt.text(0, 0.015, 'GT', va='bottom')

    # Draw thin black lines between the series
    plt.axhline(y=0.025, color='black', linewidth=0.5)
    plt.axhline(y=0.05, color='black', linewidth=0.5)

    # the linear spec 1
    x, y1, y2 = draw_spec(0, 10.5, 45, 23, 5)
    plt.fill_between(x, y1, y2, where=(y1 > y2), color='red', alpha=0.2)

    # the linear spec 2
    x, y1, y2 = draw_spec(45, 23, 100, 29.8, 3)
    plt.fill_between(x, y1, y2, where=(y1 > y2), color='orange', alpha=0.2)

    # the linear spec 3
    x, y1, y2 = draw_spec(100, 30, 300, 30, 2)
    plt.fill_between(x, y1, y2, where=(y1 > y2), color='green', alpha=0.2)

    # Save the chart as an image file
    timestamp = datetime.datetime.now().strftime("%H%M%S")
    # Define the ID string
    id = f"_{timestamp}"
    plt.savefig(directory+'distance'+id+'.png',  dpi=600)

    # save the given traces as json
    if trace_2:
        save_trace_to_json(trace=trace_1,
                           filename=directory+'ldips_trace_'+id+'.json')
        save_trace_to_json(trace=trace_2,
                           filename=directory+'gt_trace_'+id+'.json')
    else:
        save_trace_to_json(trace=trace_1,
                           filename=directory+'gt_trace_'+id+'.json')
