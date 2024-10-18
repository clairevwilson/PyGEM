import argparse
import time
import os
# External libraries
import numpy as np
import xarray as xr
import pandas as pd
from multiprocessing import Pool
# Internal libraries
import pygem_eb.input as eb_prms
import pygem_eb.massbalance as mb
import pygem.pygem_modelsetup as modelsetup
import pygem_eb.climate as climutils

# Start timer
start_time = time.time()

# ===== INITIALIZE UTILITIES =====
def get_args(parse=True):
    parser = argparse.ArgumentParser(description='pygem-eb model runs')
    # add arguments
    parser.add_argument('-glac_no', action='store', default=eb_prms.glac_no,
                        help='',nargs='+')
    parser.add_argument('-elev',action='store',default=eb_prms.elev,type=float,
                        help='Elevation in m a.s.l.')
    parser.add_argument('-site',action='store',default=eb_prms.site,type=str,
                        help='Site name')
    parser.add_argument('-start','--startdate', action='store', type=str, 
                        default=eb_prms.startdate,
                        help='pass str like datetime of model run start')
    parser.add_argument('-end','--enddate', action='store', type=str,
                        default=eb_prms.enddate,
                        help='pass str like datetime of model run end')
    parser.add_argument('-use_AWS', action='store_true',
                        default=eb_prms.use_AWS,help='use AWS or just reanalysis?')
    parser.add_argument('-use_threads', action='store_true',
                        help='use threading to import climate data?')
    parser.add_argument('-store_data', action='store_true', 
                        help='store the model output?')
    parser.add_argument('-out',action='store',type=str,default=eb_prms.output_name,
                        help='Output file name EXCLUDING extension (.nc)')
    parser.add_argument('--new_file', action='store_true',
                        default=eb_prms.new_file, help='')
    parser.add_argument('-debug', action='store_true', 
                        default=eb_prms.debug, help='')
    parser.add_argument('-switch_LAPs',action='store', type=int,
                        default=eb_prms.switch_LAPs, help='')
    parser.add_argument('-switch_melt',action='store', type=int, 
                        default=eb_prms.switch_melt, help='')
    parser.add_argument('-switch_snow',action='store', type=int,
                        default=eb_prms.switch_snow, help='')
    parser.add_argument('-k_snow',default=eb_prms.kcond_snow,action='store',
                        help='Thermal conductivity of snow')
    parser.add_argument('-a_ice',default=eb_prms.albedo_ice,action='store',type=float,
                        help='Broadband albedo of ice')
    parser.add_argument('-kw',default=eb_prms.wind_factor,action='store',type=float,
                        help='Multiplicative wind factor')
    parser.add_argument('-kp',default=eb_prms.kp,action='store',type=float,
                        help='Multiplicative precipitation factor')
    parser.add_argument('-n','--n_simultaneous_processes',default=1,type=int,
                        help='Number of parallel processes to run')
    parser.add_argument('-task_id',default=-1,type=int,
                        help='Task ID if submitted as batch job')
    parser.add_argument('-params_fn',action='store',default='None',
                        help='Filepath to params .txt file')
    parser.add_argument('-initial_snow_depth',action='store',type=float,
                        default=eb_prms.initial_snow_depth,
                        help='Snow depth in m')
    parser.add_argument('-initial_firn_depth',action='store',type=float,
                        default=eb_prms.initial_firn_depth,
                        help='Firn depth in m')
    parser.add_argument('-f', '--fff', help='Dummy arg to fool ipython', default='1')
    if parse:
        args = parser.parse_args()
        return args
    else:
        return parser

def initialize_model(glac_no,args):
    """
    Loads glacier table and climate dataset for one glacier to initialize
    the model inputs.

    Parameters
    ==========
    glac_no : str
        RGI glacier ID
    
    Returns
    -------
    climate
        Class object from climate.py
    """
    # check for known glacier properties
    data_fp = os.getcwd()+'/pygem_eb/sample_data/'
    if eb_prms.glac_name in os.listdir(data_fp):
        site = args.site if args.site != 'AWS' else 'B'
        site_fp = os.path.join(data_fp,eb_prms.glac_name+'/site_constants.csv')
        site_df = pd.read_csv(site_fp,index_col='site')
        args.elev = site_df.loc[site]['elevation']
        eb_prms.slope = site_df.loc[site]['slope']
        eb_prms.aspect = site_df.loc[site]['aspect']
        eb_prms.sky_view = site_df.loc[site]['sky_view']
        args.initial_snow_depth = site_df.loc[site]['snowdepth']
        args.initial_firn_depth = site_df.loc[site]['firndepth']
        eb_prms.shading_fp = os.getcwd() + f'/shading/out/{eb_prms.glac_name}{site}_shade.csv'
        if site not in eb_prms.output_name:
            eb_prms.output_name += f'{site}_'    

    # CHECK FOR PARAMS INPUT FILE
    if args.params_fn != 'None':
        params = pd.read_csv(args.params_fn,index_col=0)
        args.kp = params.loc['kp',args.site].astype(float)
        args.kw = params.loc['kw',args.site].astype(float)
        args.a_ice = params.loc['a_ice',args.site].astype(float)

    # ===== GET GLACIER CLIMATE =====
    # get glacier properties and initialize the climate class
    glacier_table = modelsetup.selectglaciersrgitable(np.array([glac_no]),
                    rgi_regionsO1=eb_prms.rgi_regionsO1)
    climate = climutils.Climate(args,glacier_table)

    # load in available AWS data
    if args.use_AWS:
        need_vars = climate.get_AWS(eb_prms.AWS_fn)
        climate.get_reanalysis(need_vars)
    else:
        climate.get_reanalysis(climate.all_vars)
    climate.check_ds()

    start = pd.to_datetime(args.startdate)
    end = pd.to_datetime(args.enddate)
    n_months = np.round((end-start)/pd.Timedelta(days=30))
    start_fmtd = start.month_name()+', '+str(start.year)
    print(f'Running {eb_prms.glac_name} Glacier at {args.elev} m a.s.l. for {n_months} months starting in {start_fmtd}')

    return climate

def run_model(climate,args,store_attrs=None):
    """
    Executes model functions in parallel or series and
    stores output data.

    Parameters
    ==========
    climate
        Class object with climate data from initialize_model
    args
        Command line arguments from get_args
    store_attrs : dict
        Dictionary of additional metadata to store in the .nc
    """
    # ===== RUN ENERGY BALANCE =====
    massbal = mb.massBalance(args,climate)
    massbal.main()

    # ===== END ENERGY BALANCE =====
    # Get final model run time
    end_time = time.time()
    time_elapsed = end_time-start_time
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'Total Time Elapsed: {time_elapsed:.1f} s')

    # Store metadata in netcdf and save result
    if args.store_data:
        massbal.output.add_vars()
        massbal.output.add_basic_attrs(args,time_elapsed,climate)
        massbal.output.add_attrs(store_attrs)
        out = massbal.output.get_output()
    else:
        print('Success: data was not saved')
        out = None
    
    return out

if __name__ == '__main__':
    args = get_args()
    for gn in args.glac_no:
        climate = initialize_model(gn,args)
        time_elapsed = time.time()-start_time
        print(f'Got climate in {time_elapsed:.1f} s')
        out = run_model(climate,args)
        if isinstance(out, xr.Dataset):
            # Get final mass balance
            print(f'Total Mass Loss: {out.melt.sum():.3f} m w.e.')