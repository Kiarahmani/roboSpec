import datetime
import os
from src.Spec import Spec
from matplotlib import pyplot as plt
from .utils import save_trace_to_json




def plot_single_series(trace, gt_policy, specs, directory):
    _DRAW_ACTION_MARKERS = True
    _DRAW_SPECS = True


    init_v_diff = trace[0].state['v_diff']['value']
    init_dist = trace[0].state['x_diff']['value']
    directory = 'plots/' + directory + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    # plot x diff
    plt.clf()
    x_diff_series = [x.state['x_diff']['value'] for x in trace]
    actions = [x.state['output']['value'] for x in trace]
    gt_actions = [gt_policy(x) for x in trace]
    # Create x-axis values ranging from 0 to the length of the data
    series_range = range(0, len(x_diff_series))
    # Plot the sorted data as a line chart
    plt.plot(series_range, x_diff_series, label='ldips')
    
    # Add the legend
    plt.legend(loc='upper right')

    # Add labels and title to the chart
    plt.xlabel('Time (×0.1s)')
    plt.ylabel("Distance (m)")
    plt.title(f'Distance Between Cars vs. Time\n{init_dist=}\n{init_v_diff=}')
    plt.grid(True)
    # Set the minimum values of the x and y axes to 0
    plt.xlim(0, 300)
    plt.ylim(-8, 70)
    plt.minorticks_on()
    plt.grid(True, which='minor', linestyle='--', alpha=0.3)

    if _DRAW_SPECS:
        for spec in specs:
            x, y1, y2 = spec.get_coordinates()
            plt.fill_between(x, y1, y2, where=(y1 > y2), color=spec.get_color(), alpha=0.2)

    if _DRAW_ACTION_MARKERS:
        # draw markers at the bottom for certain things
        for x in series_range:
            if x == 0:
                continue
            start = x
            end = x + 1
            x_diff_value = x_diff_series[x]
            action = actions[x]
            gt_action = gt_actions[x]
            color = 'grey' if action == 'FASTER' else '#D3D3D3'
            gt_color = 'grey' if gt_action == 'FASTER' else '#D3D3D3'
            
            # draw markers for ldips actions
            plt.axvspan(start, end, ymin=0, ymax=0.025, facecolor=color, alpha=1, zorder=5)
            # draw markers for gt actions
            plt.axvspan(start, end, ymin=0.025, ymax=0.05, facecolor=gt_color, alpha=1, zorder=5)
            # draw markers for actions matching
            if action != gt_action:
                plt.axvspan(start, end, ymin=0.05, ymax=0.075, facecolor='black', alpha=1, zorder=5)
            # draw markers for spec sat
            if _DRAW_SPECS:
                spec_color = 'green' if  all([s.is_sat(x,x_diff_value) for s in specs]) else 'red'
                plt.axvspan(start, end, ymin=0.075, ymax=0.1, facecolor=spec_color, alpha=1, zorder=5)
        # show labels for markers
        plt.text(-40, -8, 'cand acts', va='bottom', fontsize=5)
        # show labels for markers
        plt.text(-40, -6, 'GT acts', va='bottom', fontsize=5)
        # show labels for mismatch
        plt.text(-40, -4, 'Mismatch?', va='bottom', fontsize=5)
        if _DRAW_SPECS:
            # show labels for specs
            plt.text(-40, -2, 'Specs SAT?', va='bottom', fontsize=5)



    # SAVE THINGS TO FILES
    # Save the chart as an image file
    timestamp = datetime.datetime.now().strftime("%H%M%S")
    # Define the ID string
    id = f"_{timestamp}"
    plt.savefig(directory+'distance'+id+'.png',  dpi=600)
    # save the given traces as json
    save_trace_to_json(trace=trace, filename=directory+'gt_trace_'+id+'.json')








def DEPRECATED_plot_series(policy, trace_1, trace_2, gt_policy=None, specs=[]):
    # trace2 is gt trace which we are not showing currently
    _DRAW_GT = False
    _DRAW_MATCH = True
    _DRAW_SPEC_SAT = True

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
        if _DRAW_GT:
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
    plt.ylim(-8, 70)
    plt.minorticks_on()
    plt.grid(True, which='minor', linestyle='--', alpha=0.4)

    # plt.axvspan(0, 1, ymin=0.0+0.025, ymax=0.025+0.025,
    #            facecolor='blue', edgecolor='blue', alpha=1, zorder=5)
    for i, action in enumerate(actions):
        if i == 0:
            continue  # do not show the first action since it is not part of the demonstration
        # Determine the x-coordinate range for the rectangle
        start = i
        end = i + 1
        # Determine the color based on the action
        if action == 'FASTER':
            color = 'grey'
        elif action == 'SLOWER':
            color = '#D3D3D3'
        else:
            color = 'blue'
        # Add the colored rectangle
        # Adjust ymin and ymax values for rectangle height
        plt.axvspan(start, end, ymin=0+0.025, ymax=0.025 +
                    0.025, facecolor=color, alpha=1, zorder=5)

    if trace_2 and _DRAW_GT:
        # Iterate over each action
        # plt.axvspan(0, 1, ymin=0.025+0.025, ymax=0.05+0.025,
        #            facecolor='orange', edgecolor='orange', alpha=1, zorder=5)
        for i, action in enumerate([x.state['output']['value'] for x in trace_2]):
            if i == 0:
                continue  # do not show the first action since it is not part of the demonstration
            # Determine the x-coordinate range for the rectangle
            start = i
            end = i + 1
            # Determine the color based on the action
            if action == 'FASTER':
                color = 'grey'
            elif action == 'SLOWER':
                color = '#D3D3D3'
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
                color = 'grey'
            elif gt_policy(s) == 'SLOWER':
                color = '#D3D3D3'
            else:
                color = 'blue'
            # Add the colored rectangle
            # Adjust ymin and ymax values for rectangle height
            plt.axvspan(start, end, ymin=0, ymax=0.025,
                        facecolor=color, alpha=1, zorder=5)
            if _DRAW_MATCH:
                if s.state['output']['value'] == gt_policy(s):
                    #color = 'white'
                    pass
                else:
                    color = 'red'
                    plt.axvspan(start, end, ymin=0.025+0.025, ymax=0.05 +
                                0.025, facecolor=color, alpha=1, zorder=5)

    # Add labels for the series
    if trace_2:
        plt.text(-30, -2, 'green spec?', va='bottom', fontsize=5)
        plt.text(-30, -4, 'ldips acts', va='bottom', fontsize=5)
        plt.text(-30, -6, 'mismatch?', va='bottom', fontsize=5)
        if gt_policy:
            plt.text(-30, -10, 'gt acts', va='bottom', fontsize=5)
    else:
        plt.text(0, 0.015, 'GT', va='bottom')



    if _DRAW_SPEC_SAT:
        for s in trace_1:
            x_value = s.state['x_diff']['value']
            print (x_value)


    # draw the specs
    for x, y1, y2, color in specs:
        plt.fill_between(x, y1, y2, where=(y1 > y2), color=color, alpha=0.2)


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
