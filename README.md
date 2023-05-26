# RoboSpec

Effective Synthesis of Robotics Programs from Demonstrations and Safety/Reachability Specifications

  
  
## Setup:
- 0) Go the root directory: `cd roboSpec`
- 1) Run `git submodule update --init --recursive` 
- 2) `cd pips`
- 3) `git checkout base`
- 3) Run `make`



## Run Experiments:

- 1) Go the root directory: `cd roboSpec`

- 2) Run `./scripts/init.sh`

- 3) Run `./scripts/simul_gt.sh` to generate the initial samples from the ground truth policy.

- 4) Run `./scripts/run_pips.sh` to run pips on the generated samples and write  (Pythonic version of) the learned policy in `learned_policy.py` file. 

- 5) Run `python robo_spec.py ldips`. The behaviors of this policy will be plotted in `plots/policy_ldips/distance.png`.

- 6) Append the repaired samples from the above simulation to the sample file `python scripts/append_repaired_samples.py`

- Repeat from step 4 to learn a new policy using the repaired samples.