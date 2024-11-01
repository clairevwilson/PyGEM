# Built-in libraries
import os
import time
import copy
# External libraries
import pandas as pd
from multiprocessing import Pool
# Internal libraries
import pygem_eb.input as eb_prms
import run_simulation_eb as sim
import pygem_eb.massbalance as mb

# Read command line args
args = sim.get_args()
n_processes = args.n_simultaneous_processes

# Define sets of parameters
params = {'k_snow':['VanDusen'],
          'a_ice':[0.4],
          'kw':[1],
          'T_threshold':[[0,1],[0,2],[1.2,3.2]],
          'Boone_c5':[0.018,0.05],
          'kp':[1,3]}
kw = 1
a_ice = 0.4
k_snow = 'VanDusen'

# Define sites
sites = ['A','B','D']

# Determine number of runs for each process
n_runs = len(sites)
for param in list(params.keys()):
    n_runs *= len(params[param])
n_runs_per_process = n_runs // n_processes  # Base number of runs per CPU
n_runs_with_extra = n_runs % n_processes    # Number of CPUs with one extra run

# Force some args
args.store_data = True              # Ensures output is stored
args.use_AWS = False                # Use available AWS data
args.debug = False                  # Don't need debug prints
eb_prms.store_vars = ['MB']         # Only store mass and energy balance results
args.startdate = pd.to_datetime('2000-04-20 00:00:00')
args.enddate = pd.to_datetime('2024-08-21 00:00:00')

# Parse list for inputs to Pool function
packed_vars = [[] for _ in range(n_processes)]
run_no = 0  # Counter for runs added to each set
set_no = 0  # Index for the parallel process
# Loop through sites
for site in sites:
    # Initialize the model
    args_site = copy.deepcopy(args)
    args_site.site = site
    climate = sim.initialize_model(args.glac_no[0],args_site)
    # Loop through parameters
    for threshold in params['T_threshold']:
        # for k_snow in params['k_snow']:
        # for a_ice in params['a_ice']:
        # for kw in params['kw']:
        for kp in params['kp']:
            for c5 in params['Boone_c5']:
                # Get args for the current run
                args_run = copy.deepcopy(args)
                args_run.site = site

                # Set parameters
                args_run.k_snow = k_snow
                args_run.a_ice = a_ice
                args_run.kw = kw
                args_run.site = site
                args_run.snow_threshold = threshold
                args_run.Boone_c5 = c5
                args_run.kp = kp

                # Set identifying output filename
                args_run.out = f'gulkana_gridsearch_11_01_{site}_'

                # Specify attributes for output file
                store_attrs = {'k_snow':str(k_snow),'a_ice':str(a_ice),'kw':str(kw),
                                'threshold_low':str(threshold[0]),
                                'threshold_high':str(threshold[1]),
                                'c5':str(c5),'kp':str(kp)}

                # Check if moving to the next set of runs
                n_runs_set = n_runs_per_process + (1 if set_no < n_runs_with_extra else 0)
                if run_no >= n_runs_set:
                    set_no += 1
                    run_no = 0

                # Set task ID for SNICAR input file
                args_run.task_id = set_no
            
                # Store model inputs
                packed_vars[set_no].append((args_run,climate,store_attrs))

                # Advance counter
                run_no += 1

def run_model_parallel(list_inputs):
    # Loop through the variable sets
    for inputs in list_inputs:
        # Unpack inputs
        args,climate,store_attrs = inputs
        
        # Check if model run should be performed
        # if not os.path.exists(eb_prms.output_filepath + args.out + '0.nc'):
        # Start timer
        start_time = time.time()

        # Run the model
        massbal = mb.massBalance(args,climate)
        massbal.main()

        # Completed model run: end timer
        time_elapsed = time.time() - start_time

        # Store output
        massbal.output.add_vars()
        massbal.output.add_basic_attrs(args,time_elapsed,climate)
        massbal.output.add_attrs(store_attrs)
    return

# Run model in parallel
with Pool(n_processes) as processes_pool:
    processes_pool.map(run_model_parallel,packed_vars)