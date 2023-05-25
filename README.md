# RoboSpec

Effective Synthesis of Robotics Programs from Demonstrations and Safety/Reachability Specifications

  
  

## Run Experiments:

- Go the root directory: `cd roboSpec`

- Make sure the file `pips/highway_input_demos.json` exists and contains an empty list

- Make sure the file `demos/repaired_samples.json` exists and contains an empty list

  

#### Generate the initial samples from the ground truth policy:

- run the ground truth using the command `python robo_spec.py gt`. Make sure the plot `plots/policy_ground_truth/distance.png` is updated and the new samples are generated and stored in `demos/sampled_demo.json`

- copy the initial set of samples to the file passed to pips: `cp demos/sampled_demo.json pips/highway_input_demos.json`

 
#### Run pips on the sampled trace:

- Run pips: `./scripts/run_pips.sh`. This runs pips on samples given in `pips/highway_input_demos.json`, and generates transition expressions stored in `pips/solutions`. Double check the solutions exist. For the runnig example (highway) there should be 4 files, e.g. `pips/solutions/FASTER_FASTER.json`.
- Translate the pips solutions to python: `python scripts/translate_solutions_to_python.py`. This will translated and write the learned policy into `learned_policy.py` file. 

#### Run the simulator on the learned policy:
 - Run `python robo_spec.py ldips`. This will run the learned policy and plot its trace in `plots/policy_ldips/distance.png`. 