import pandas as pd
import numpy as np
import xarray as xr
import os, sys
import matplotlib.pyplot as plt
from objectives import seasonal_mass_balance

run_model = True

class HiddenPrints:
    """
    Class to hide prints when running SNICAR
    """
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self,exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
        return
    
# import model
import pygem_eb.input as eb_prms
eb_prms.startdate = pd.to_datetime('2000-04-20 00:30')
eb_prms.enddate = eb_prms.startdate + pd.Timedelta(hours=2)
eb_prms.debug = False
with HiddenPrints():
    import run_simulation_eb as sim
mb_fp = os.getcwd()+'/../MB_data/Gulkana/Input_Gulkana_Glaciological_Data.csv'

# model parameters
params = {
    'albedo_ice':[0.1,0.3],
    'k_ice':[0.5,2]
}

# read command line args
args = sim.get_args()
args.enddate = pd.to_datetime('2023-09-30 00:30')

# force some args
args.store_data = True
args.parallel = True

ds_list = []
for albedo_ice in params['albedo_ice']:
    for thermal_cond in params['k_ice']:
        eb_prms.output_name = f'{eb_prms.output_filepath}EB/a_{albedo_ice}_k_{thermal_cond}_'
        eb_prms.constant_conductivity = thermal_cond
        eb_prms.albedo_ice = albedo_ice

        print()
        print('Starting model run with a_ice = ',albedo_ice,'and k_ice = ',thermal_cond)

        if run_model and not os.path.exists(eb_prms.output_name+'.nc'):
            # with HiddenPrints():
            if True:
                # initialize the model
                climate = sim.initialize_model(args.glac_no[0],args)

                # run the model
                sim.run_model(climate,args,{'a_ice':str(albedo_ice),
                                                'k_ice':str(thermal_cond)})
        else:
            print('Run already exists')
            ds = xr.open_dataset(f'{eb_prms.output_filepath}EB/a_{albedo_ice}_k_{thermal_cond}.nc')
            ds = ds.assign_coords(time=ds.time.values + pd.Timedelta(days=365*10))
            ds_list.append(ds)
        
        # print('Finished: making plot')
        # seasonal_mass_balance(mb_fp,ds_list[0],0,'B')

# end_year = args.enddate.year if args.enddate.month > 7 else args.enddate.year-1
# years_model = np.arange(args.startdate.year+1,end_year+1)
# mb_df = pd.read_csv(mb_fp)
# for site in ['AB','B','D']:
#     years_site = np.unique(mb_df.loc[mb_df['site_name']==site]['Year'])
#     years = list(set(years_site)&set(years_model))
#     years = np.sort(np.array(years))
#     years = [2011]
#     print(site,years)
#     fig,ax = plot_multiyear_mb(ds_list,mb_df,years,site)
#     plt.savefig(f'multiyear_run_{site}.png',dpi=200)