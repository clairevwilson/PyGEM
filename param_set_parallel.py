# Built-in libraries
import os
import time
import copy
# External libraries
import pandas as pd
import pickle
from multiprocessing import Pool
# Internal libraries
import pygem_eb.input as eb_prms
import run_simulation_eb as sim
import pygem_eb.massbalance as mb
from objectives import *

# OPTIONS
repeat_run = True  # True if restarting an already begun run
run_type = 'long'   # 'long' or '2024'
# Define sets of parameters
params = {'kw':[1,1.5,2,2.5,3],
          'Boone_c5':[0.018,0.02,0.022,0.024,0.026,0.028],
          'kp':[2.4,2.5,2.6,2.7,2.8,3]}
# params = {'kw':[1.5,2],'Boone_c5':[0.018],'kp':[2.8]}

# Set the ones you want constant
# kw = 2
# c5 = 0.025
# kp = 3
k_snow = 'VanDusen'

# Define sites
if run_type == '2024':
    sites = ['AB','ABB','B','BD','D','T'] # 
else:
    sites = ['A','AU','B','D'] # 

# Read command line args
args = sim.get_args()
n_processes = args.n_simultaneous_processes

# Determine number of runs for each process
n_runs = len(sites)
for param in list(params.keys()):
    n_runs *= len(params[param])
print(f'Beginning {n_runs} model runs on {n_processes} CPUs')

# Check if we need multiple (serial) runs per (parallel) set
if n_runs <= n_processes:
    n_runs_per_process = 0
    n_process_with_extra = 0
else:
    n_runs_per_process = n_runs // n_processes  # Base number of runs per CPU
    n_process_with_extra = n_runs % n_processes    # Number of CPUs with one extra run

# Force some args
args.store_data = True              # Ensures output is stored
if run_type == '2024': # Short AWS run
    args.use_AWS = True
    eb_prms.AWS_fn = '../climate_data/AWS/Preprocessed/gulkana2024.csv'
    eb_prms.store_vars = ['MB','layers']
    args.startdate = pd.to_datetime('2024-04-18 00:00:00')
    args.enddate = pd.to_datetime('2024-08-20 00:00:00')
else: # Long MERRA-2 run
    args.use_AWS = False
    eb_prms.store_vars = ['MB']     # Only store mass balance results
    args.startdate = pd.to_datetime('2000-04-20 00:00:00')
    args.enddate = pd.to_datetime('2024-08-20 00:00:00')

# Create output directory
if 'trace' in eb_prms.machine:
    eb_prms.output_filepath = '/trace/group/rounce/cvwilson/Output/'

if repeat_run:
    date = '11_22'
    n_today = '1'
    out_fp = f'{date}_{n_today}/'
else:
    date = str(pd.Timestamp.today()).replace('-','_')[5:10]
    n_today = 0
    out_fp = f'{date}_{n_today}/'
    while os.path.exists(eb_prms.output_filepath + out_fp):
        n_today += 1
        out_fp = f'{date}_{n_today}/'
    os.mkdir(eb_prms.output_filepath + out_fp)

# Transform params to strings for comparison
for key in params:
    for v,value in enumerate(params[key]):
        params[key][v] = str(value)

# Parse list for inputs to Pool function
packed_vars = [[] for _ in range(n_processes)]
run_no = 0  # Counter for runs added to each set
set_no = 0  # Index for the parallel process

# Loop through sites
for site in sites:
    # Initialize the model for the site
    args_site = copy.deepcopy(args)
    args_site.site = site
    climate = sim.initialize_model(args.glac_no[0],args_site)

    # Loop through parameters
    for kw in params['kw']:
        for kp in params['kp']:
            for c5 in params['Boone_c5']:
                # Get args for the current run
                args_run = copy.deepcopy(args_site)

                # Set parameters
                args_run.k_snow = k_snow
                args_run.kw = kw
                args_run.site = site
                args_run.Boone_c5 = c5
                args_run.kp = kp

                # Set identifying output filename
                args_run.out = out_fp + f'grid_{date}_set{set_no}_run{run_no}_'

                # Specify attributes for output file
                store_attrs = {'k_snow':k_snow,'kw':kw,
                                'c5':c5,'kp':kp,'site':site}

                # Set task ID for SNICAR input file
                args_run.task_id = set_no
                args_run.run_id = run_no

                # Store model inputs
                packed_vars[set_no].append((args_run,climate,store_attrs))

                # Check if moving to the next set of runs
                n_runs_set = n_runs_per_process + (1 if set_no < n_process_with_extra else 0)
                if run_no == n_runs_set - 1:
                    set_no += 1
                    run_no = -1

                # Advance counter
                run_no += 1

def run_model_parallel(list_inputs):
    global outdict
    # Loop through the variable sets
    for inputs in list_inputs:
        # Unpack inputs
        args,climate,store_attrs = inputs

        # Check if model run should be performed
        n_iters = 0
        while not os.path.exists(eb_prms.output_filepath + args.out + '0.nc') and n_iters <= 5:
            n_iters += 1
            if n_iters > 1:
                print('Beginning repeat run... ')
            try:
            # for aaaa in [0]:
                # Start timer
                start_time = time.time()

                # Initialize the mass balance / output
                massbal = mb.massBalance(args,climate)

                # Add attributes to output file in case it crashes
                massbal.output.add_attrs(store_attrs)

                # Run the model
                massbal.main()

                # End timer
                time_elapsed = time.time() - start_time

                # Store output
                massbal.output.add_vars()
                massbal.output.add_basic_attrs(args,time_elapsed,climate)

            except:
                print('Failed site',args.site,'with kw =',args.kw,'c5 =',args.Boone_c5,'kp =',args.kp)
                print('Removing:',args.out + '0.nc')
                os.remove(eb_prms.output_filepath + args.out + '0.nc')
                print()
                print('Retrying...')
    return

# Run model in parallel
with Pool(n_processes) as processes_pool:
    processes_pool.map(run_model_parallel,packed_vars)