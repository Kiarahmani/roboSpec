#!/bin/bash

# Check if the number of iterations is provided as an argument
if [[ $# -eq 0 ]]; then
    echo "Please provide the number of iterations as an argument."
    exit 1
fi

num_iterations=$1

# Iterate 'num_iterations' times using a for loop
for ((i=1; i<=num_iterations; i++))
do
    ./scripts/run_pips.sh && python robo_spec.py ldips && python scripts/append_repaired_samples.py
done