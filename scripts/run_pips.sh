rm ./pips/solutions/*.json 
./pips/bin/ldips-l3 -lib_file pips/ops/highway_op_library.json -ex_file pips/highway_input_demos.json -out_dir "pips/solutions/" -debug -feat_depth 3 -sketch_depth 2 -window_size 0 
# can be optionally given to the above command: -multi_thread
python scripts/translate_solutions_to_python.py