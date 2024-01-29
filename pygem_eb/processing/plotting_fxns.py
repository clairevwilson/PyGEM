import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from sklearn.metrics import mean_squared_error

mpl.style.use('seaborn-v0_8')
colors = plt.rcParams['axes.prop_cycle'].by_key()['color'] 
glac_props = {'01.00570':{'name':'Gulkana',
                            'AWS_fn':'gulkana1725_hourly.csv'},
            '01.01104':{'name':'Lemon Creek',
                            'AWS_fn':'LemonCreek1285_hourly.csv'},
            '01.16195':{'name':'South',
                            'AWS_fn':'Preprocessed/south/south2280_hourly_2008_wNR.csv'},
            '08.00213':{'name':'Storglaciaren',
                            'AWS_fn':'Storglaciaren/SITES_MET_TRS_SGL_dates_15MIN.csv'},
            '11.03674':{'name':'Saint-Sorlin',
                            'AWS_fn':'Preprocessed/saintsorlin/saintsorlin_hourly.csv'},
            '16.02444':{'name':'Artesonraju',
                            'AWS_fn':'Preprocessed/artesonraju/Artesonraju_hourly.csv'}}

varprops = {'surftemp':{'label':'Surface temp','type':'Temperature','units':'C'},
            'airtemp':{'label':'Air temp','type':'Temperature','units':'C'},
           'melt':{'label':'Cum. Melt','type':'MB','units':'m w.e.'},
           'runoff':{'label':'Cum. Runoff','type':'MB','units':'m w.e.'},
           'accum':{'label':'Cum. Accumulation','type':'MB','units':'m w.e.'},
           'refreeze':{'label':'Cum. Refreeze','type':'MB','units':'m w.e.'},
           'meltenergy':{'label':'Melt Energy','type':'Flux','units':'W m$^{-2}$'},
           'SWin':{'label':'Shortwave In','type':'Flux','units':'W m$^{-2}$'},
           'SWout':{'label':'Shortwave Out','type':'Flux','units':'W m$^{-2}$'},
           'LWin':{'label':'Longwave In','type':'Flux','units':'W m$^{-2}$'},
           'LWout':{'label':'Longwave Out','type':'Flux','units':'W m$^{-2}$'},
           'SWnet':{'label':'Net Shortwave','type':'Flux','units':'W m$^{-2}$'},
           'LWnet':{'label':'Net Longwave','type':'Flux','units':'W m$^{-2}$'},
           'NetRad':{'label':'Net Radiation','type':'Flux','units':'W m$^{-2}$'},
           'sensible':{'label':'Sensible Heat','type':'Flux','units':'W m$^{-2}$'},
           'latent':{'label':'Latent Heat','type':'Flux','units':'W m$^{-2}$'},
           'rain':{'label':'Rain Energy','type':'Flux','units':'W m$^{-2}$'},
           'layertemp':{'label':'Layer temp','type':'Layers','units':'C'},
           'layerdensity':{'label':'Density','type':'Layers','units':'kg m$^{-3}$'},
           'layerwater':{'label':'Water Content','type':'Layers','units':'kg m$^{-2}$'},
           'layerBC':{'label':'BC Concentration','type':'Layers','units':'ppb'},
           'layerdust':{'label':'Dust Concentration','type':'Layers','units':'ppm'},
           'layergrainsize':{'label':'Grain size','type':'Layers','units':'um'},
           'layerheight':{'label':'Layer height','type':'Layers','units':'m'},
           'snowdepth':{'label':'Snow depth','type':'MB','units':'m'},
           'albedo':{'label':'Albedo','type':'Albedo','units':''},}
AWS_vars = {'temp':{'label':'Temperature','units':'C'},
             'wind':{'label':'Wind Speed','units':'m s$^{-1}$'},
             'rh':{'label':'Relative Humidity','units':'%'},
            'SWin':{'label':'Shortwave In','units':'W m$^{-2}$'},
             'LWin':{'label':'Longwave In','units':'W m$^{-2}$'},
             'sp':{'label':'Surface Pressure','units':'Pa'}}

def getds(file):
    ds = xr.open_dataset(file)
    start = pd.to_datetime(ds.indexes['time'].to_numpy()[0])
    end = pd.to_datetime(ds.indexes['time'].to_numpy()[-1])
    return ds,start,end

def simple_plot(ds,bin,time,vars,res='d',t='',
                skinny=True,save_fig=False,new_y=['None']):
    """
    Returns a simple timeseries plot of the variables as lumped in the input.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset object containing the model output
    bin : int
        Integer value of the bin index to plot
    vars : list-like
        List of strings where the variables to be plotted together are nested together
        e.g. [['airtemp','surftemp'],['SWnet','LWnet','sensible','latent']]
    time : list-like   
        Either len-2 list of start date, end date, or a list of datetimes
    res : str
        Abbreviated time resolution (e.g. '12h' or 'd')
    t : str
        Title for the figure
    skinny : Bool
        True or false, defines the height of each panel
    save_fig : Bool
        True or false, save the figure or not
    new_y : list-like
        List of variables in vars that should be plotted on a new y-axis
    """
    h = 1.5 if skinny else 3
    fig,axes = plt.subplots(len(vars),1,figsize=(7,h*len(vars)),sharex=True,layout='constrained')

    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq='h')
    ds = ds.sel(time=time,bin=bin)
    ds_mean = ds.resample(time=res).mean(dim='time',keep_attrs='units')
    ds_sum = ds.resample(time=res).sum(dim='time',keep_attrs='units')
    for i,v in enumerate(vars):
        ic = i-6 if i>5 else i
        if len(vars) > 1:
            axis = axes[i]
        else:
            axis = axes
        vararray = np.array(v)
        for var in vararray:
            if var in ['melt','runoff','accum','refreeze']:
                var_to_plot = ds_sum[var].cumsum()
            else:
                var_to_plot = ds_mean[var]

            if var in new_y:
                newaxis = axis.twinx()
                newaxis.plot(ds_mean.coords['time'],var_to_plot,color=colors[ic],label=var)
                newaxis.grid(False)
                units = 'C'
                newaxis.set_ylabel({varprops[var]['label']})
                newaxis.legend(bbox_to_anchor=(1.01,1.1),loc='upper left')
            else:
                axis.plot(ds_mean.coords['time'],var_to_plot,color=colors[ic],label=var)
                axis.set_ylabel(varprops[var]['label'])
            ic+=1
        axis.legend(bbox_to_anchor=(1.01,1),loc='upper left')
    date_form = mpl.dates.DateFormatter('%d %b')
    axis.xaxis.set_major_formatter(date_form)
    fig.suptitle(t)
    if save_fig:
        plt.savefig('/home/claire/research/Output/ebfluxcomparison.png',dpi=150)

def plot_stake_snowdepth(stake_df,ds_list,time,labels,bin=0,t='Snow Depth Comparison'):
    """
    Returns a comparison of snow depth from the output datasets to stake data

    Parameters
    ----------
    stake_df : pd.DataFrame
        DataFrame object containing stake MB data
    ds_list : list of xr.Datasets
        List of model output datasets to plot melt
    time : list-like   
        Either len-2 list of start date, end date, or a list of datetimes
    labels : list of str
        List of same length as ds_list containing labels to plot
    """
    fig,ax = plt.subplots(figsize=(4,6),sharex=True,layout='constrained')
    stake_df = stake_df.set_index(pd.to_datetime(stake_df['Date']))

    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq='h')
        days = pd.date_range(start,end,freq='d')
    stake_df = stake_df.loc[days]
    for i,ds in enumerate(ds_list):
        c = plt.cm.Dark2(i)
        ds = ds.sel(time=time,bin=bin)
        ax.plot(ds.coords['time'],ds.snowdepth.to_numpy()*100,label=labels[i],color=c)
    ax.plot(stake_df.index,stake_df['snow_depth'].to_numpy(),label='Stake',linestyle='--')
    date_form = mpl.dates.DateFormatter('%d %b')
    ax.xaxis.set_major_formatter(date_form)
    ax.legend()
    ax.set_ylabel('Snow Depth (cm)')
    fig.suptitle(t)

def plot_stake_ablation(stake_df,ds_list,time,labels,bin=0,t='Stake Comparison'):
    """
    Returns a comparison of melt from the output datasets to stake data

    Parameters
    ----------
    stake_df : pd.DataFrame
        DataFrame object containing stake MB data
    ds_list : list of xr.Datasets
        List of model output datasets to plot melt
    time : list-like   
        Either len-2 list of start date, end date, or a list of datetimes
    labels : list of str
        List of same length as ds_list containing labels to plot
    """
    fig,ax = plt.subplots(figsize=(4,6),sharex=True,layout='constrained')
    stake_df = stake_df.set_index(pd.to_datetime(stake_df['Date']))

    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq='h')
        days = pd.date_range(start,end,freq='d')
    stake_df = stake_df.loc[days]
    for i,ds in enumerate(ds_list):
        c = plt.cm.Dark2(i)
        ds = ds.sel(time=time,bin=bin)
        ax.plot(ds.coords['time'],ds.melt.cumsum(),label=labels[i],color=c)
    ax.plot(stake_df.index,np.cumsum(stake_df['melt'].to_numpy()),label='Stake',linestyle='--',c='black')
    date_form = mpl.dates.DateFormatter('%d %b')
    ax.xaxis.set_major_locator(mpl.dates.MonthLocator())
    ax.xaxis.set_major_formatter(date_form)
    ax.legend()
    ax.set_ylabel('Cumulative Melt (m w.e.)')
    fig.suptitle(t)

def plot_stake_accumulation(stake_df,ds_list,time,labels,bin=0,t=''):
    """
    Returns a comparison of accumulation from the output datasets to stake data

    Parameters
    ----------
    stake_df : pd.DataFrame
        DataFrame object containing stake MB data
    ds_list : list of xr.Datasets
        List of model output datasets to plot melt
    time : list-like   
        Either len-2 list of start date, end date, or a list of datetimes
    labels : list of str
        List of same length as ds_list containing labels to plot
    """

    fig,ax = plt.subplots(figsize=(4,6),sharex=True,layout='constrained')
    stake_df = stake_df.set_index(pd.to_datetime(stake_df['Date']))

    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq='h')
        days = pd.date_range(start,end,freq='d')
    stake_df = stake_df.loc[days]
    for i,ds in enumerate(ds_list):
        c = plt.cm.Dark2(i)
        ds = ds.sel(time=time,bin=bin)
        ax.plot(ds.coords['time'],ds.accum,color=c,label=labels[i])
    snow_depth = stake_df['snow_depth'].to_numpy() / 100
    previous_depth = snow_depth[0]
    accum = []
    for depth in snow_depth:
        if depth > previous_depth:
            accum.append((depth - previous_depth)/100)
        else:
            accum.append(0)
    ax.plot(stake_df.index,accum,label='Stake',linestyle='--')

    date_form = mpl.dates.DateFormatter('%d %b')
    ax.xaxis.set_major_formatter(date_form)
    ax.legend()
    ax.set_ylabel('Accumulation (m w.e.)')
    fig.suptitle(t)
        
def compare_runs(ds_list,time,labels,var,res='d',t=''):
    """
    Returns a comparison of different model runs

    Parameters
    ----------
    ds_list : list of xr.Datasets
        List of model output datasets to plot melt
    labels : list of str
        List of same length as ds_list containing labels to plot
    time : list-like   
        Either len-2 list of start date, end date, or a list of datetimes
    var : str
        Variable to plot as named in ds
    res : str
        Abbreviated time resolution to plot (e.g. '12h' or 'd')
    t : str
        Title of plot
    """
    fig,ax = plt.subplots(figsize=(6,3))
    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq=res)
    for i,ds in enumerate(ds_list):
        c = plt.cm.Dark2(i)
        if var in ['melt','runoff','refreeze','accum','MB']:
            ds_resampled = ds.resample(time=res).sum()
            ax.plot(time,ds_resampled[var].sel(time=time).cumsum(),label=labels[i],color=c)
        elif 'layer' in var:
            ds_resampled = ds.resample(time=res).mean()
            ax.plot(time,ds_resampled[var].sel(time=time,layer=0),label=labels[i],color=c)
        else:
            ds_resampled = ds.resample(time=res).mean()
            ax.plot(time,ds_resampled[var].sel(time=time),label=labels[i],color=c)
    date_form = mpl.dates.DateFormatter('%d %b')
    ax.xaxis.set_major_formatter(date_form)
    ax.set_ylabel(var)
    ax.legend()
    fig.suptitle(t)
    plt.show()
    return

def panel_MB_compare(ds_list,time,labels,units,stake_df,rows=2,t=''):
    """
    Returns a comparison of different model runs

    Parameters
    ----------
    ds_list : list of xr.Datasets
        List of model output datasets to plot melt
    labels : list of str
        List of same length as ds_list containing labels to plot
    time : list-like   
        Either len-2 list of start date, end date, or a list of datetimes
    var : str
        List of vars to plot as named in ds
    t : str
        Title of plot
    """
    w = 2 # width of each plot
    n = int(np.ceil(len(ds_list)/2))
    n = 2 if n == 1 else n

    # Initialize plots
    fig,ax = plt.subplots(rows,int(n/rows),sharex=True,sharey=True,
                              figsize=(w*n/rows,6),layout='constrained')
    for j in range(rows):
        ax[j,0].set_ylabel('Cumulative Melt (m w.e.)')
    ax = ax.flatten()
    
    # Initialize time and comparison dataset
    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq='d')
    stake_df = stake_df.set_index(pd.to_datetime(stake_df['Date']))
    stake_df = stake_df.loc[time]
    daily_cum_melt_DATA = np.cumsum(stake_df['melt'].to_numpy())

    c_iter = iter(plt.cm.Dark2(np.linspace(0,1,8)))
    date_form = mpl.dates.DateFormatter('%d %b')
    plot_idx = 0
    for i,ds in enumerate(ds_list):
        # get variable and value for labeling
        var,val = labels[i].split('=')

        # get RMSE
        daily_melt_MODEL = ds.resample(time='d').sum().sel(bin=0,time=time)
        daily_cum_melt_MODEL = daily_melt_MODEL['melt'].cumsum().to_numpy()
        # melt_mse = mean_squared_error(daily_cum_melt_DATA,daily_cum_melt_MODEL)
        # melt_rmse = np.mean(melt_mse)
        diff = daily_cum_melt_MODEL[-1] - daily_cum_melt_DATA[-1]
        label = f'{val}{units[i]}: {diff:.3f} m w.e.'

        # get color (loops itself)
        try:
            c = next(c_iter)
        except:
            c_iter = iter([plt.cm.Dark2(i) for i in range(8)])
            c = next(c_iter)

        # plot stake_df once per plot
        if i % 2 == 0:
            ax[plot_idx].plot(stake_df.index,daily_cum_melt_DATA,label='Stake',linestyle='--')

        # plot daily melt
        ax[plot_idx].plot(time,daily_cum_melt_MODEL,label=label,color=c,linewidth=0.8)
        ax[plot_idx].set_title(var)
        ax[plot_idx].xaxis.set_major_locator(mpl.dates.MonthLocator())
        ax[plot_idx].xaxis.set_major_formatter(date_form)
        ax[plot_idx].legend(fontsize=8)

        if i % 2 != 0:
            plot_idx += 1
    fig.autofmt_xdate()
    fig.suptitle(t)
    plt.show()
    return

def panel_temp_compare(ds_list,time,labels,temp_df,rows=2,t=''):
    """
    Returns a comparison of different model runs

    Parameters
    ----------
    ds_list : list of xr.Datasets
        List of model output datasets to plot melt
    labels : list of str
        List of same length as ds_list containing labels to plot
    time : list-like   
        Either len-2 list of start date, end date, or a list of datetimes
    t : str
        Title of plot
    """
    w = 2 # width of each plot
    n = int(np.ceil(len(ds_list)/2))
    n = 2 if n == 1 else n

    # Initialize plots
    fig,ax = plt.subplots(rows,int(n/rows),sharex=True,figsize=(w*n/rows,6),layout='constrained')
    ax = ax.flatten()

    # Initialize time and comparison dataset
    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq='h')
    temp_df = temp_df.set_index(pd.to_datetime(temp_df['Datetime']))
    temp_df = temp_df.drop(columns='Datetime')
    height_DATA = 3.5 - np.array([.1,.4,.8,1.2,1.6,2,2.4,2.8,3.2,3.49])

    c_iter = iter(plt.cm.Dark2(np.linspace(0,1,8)))
    date_form = mpl.dates.DateFormatter('%d %b')
    plot_idx = 0
    for i,ds in enumerate(ds_list):
        # get variable and value for labeling
        var,val = labels[i].split('=')

        # Need to interpolate data for comparison to model depths -- loop through timesteps
        all_MODEL = np.array([])
        all_DATA = np.array([])
        all_TIME = np.array([])
        plot_MODEL = np.array([])
        plot_DATA = np.array([])
        for hour in time:
            # Extract layer heights
            lheight = ds.sel(time=hour,bin=0)['layerheight'].to_numpy()
            # Index snow bins
            density = ds.sel(time=hour,bin=0)['layerdensity'].to_numpy()
            density[np.where(np.isnan(density))[0]] = 1e5
            full_bins = np.where(density < 700)[0]
            if len(full_bins) < 1:
                break
            lheight = lheight[full_bins]
            icedepth = np.sum(lheight) + lheight[-1] / 2

            # Get property and absolute depth
            temp_MODEL = ds.sel(time=hour,bin=0)['layertemp'].to_numpy()[full_bins]
            ldepth = np.array([np.sum(lheight[:i+1])-(lheight[i]/2) for i in range(len(lheight))])
            height_above_ice = icedepth - ldepth

            # Interpolate temperature data to model heights
            temp_at_iButtons = temp_df.loc[hour].to_numpy().astype(float)
            temp_DATA = np.interp(height_above_ice,height_DATA,temp_at_iButtons)
            all_MODEL = np.append(all_MODEL,temp_MODEL)
            all_DATA = np.append(all_DATA,temp_DATA)
            all_TIME = np.append(all_TIME,hour)

            # Extract mean snow column temperature to plot
            temp_no_above_0 = temp_df.mask(temp_df>=0.2,None).loc[hour].to_numpy().astype(float)
            plot_MODEL = np.append(plot_MODEL,np.average(temp_MODEL,weights=lheight))
            plot_DATA = np.append(plot_DATA,np.mean(temp_no_above_0))
        temp_mse = mean_squared_error(all_DATA,all_MODEL)
        temp_rmse = np.mean(temp_mse)
        label = f'{val}: {temp_rmse:.3f}'

        # get color (loops itself)
        try:
            c = next(c_iter)
        except:
            c_iter = iter([plt.cm.Dark2(i) for i in range(8)])
            c = next(c_iter)

        # plot temp_df once per plot
        if i % 2 == 0:
            ax[plot_idx].plot(all_TIME,plot_DATA,label='iButtons',linestyle='--')

        # plot daily melt
        time = pd.date_range(time[0],end,freq='h')
        ax[plot_idx].plot(all_TIME,plot_MODEL,label=label,color=c,linewidth=0.8)
        ax[plot_idx].set_title(var)
        ax[plot_idx].xaxis.set_major_formatter(date_form)
        ax[plot_idx].set_ylabel('Average Snow Temperature (C)')
        ax[plot_idx].legend()

        if i % 2 != 0:
            plot_idx += 1
    fig.suptitle(t)
    plt.show()
    return

def build_RMSEs(ds_list,stake_df,time,labels,fn='sensitivity.npy'):
    # get stake data into right format
    stake_df = stake_df.set_index(pd.to_datetime(stake_df['Date']))
    stake_df = stake_df.loc[time[0]:time[1]]
    daily_cum_melt_DATA = np.cumsum(stake_df['melt'].to_numpy())
    sens_out = {}
    for i,ds in enumerate(ds_list):
        daily_melt_MODEL = ds.resample(time='d').sum().sel(bin=0)
        daily_cum_melt_MODEL = daily_melt_MODEL['melt'].cumsum().to_numpy()
        melt_mse = mean_squared_error(daily_cum_melt_DATA,daily_cum_melt_MODEL)
        melt_rmse = np.mean(melt_mse)
        sens_out[labels[i]] = melt_rmse
    np.save(fn,sens_out)

def plot_iButtons(ds,bin,dates,path=None):
    if not path:
        path = '/home/claire/research/MB_data/Gulkana/field_data/iButton_2023_all.csv'
    df = pd.read_csv(path,index_col=0)
    df = df.set_index(pd.to_datetime(df.index)- pd.Timedelta(hours=8))
    df = df[pd.to_datetime('04-18-2023 00:00'):]
    depth_0 = 3.5 - np.array([.1,.4,.8,1.2,1.6,2,2.4,2.8,3.2,3.5])

    fig,axes = plt.subplots(1,len(dates),sharey=True,sharex=True,figsize=(8,4)) #,sharex=True,sharey='row'
    for i,date in enumerate(dates):
        # Extract layer heights
        lheight = ds.sel(time=date,bin=bin)['layerheight'].to_numpy()
        # Index snow bins
        density = ds.sel(time=date,bin=bin)['layerdensity'].to_numpy()
        density[np.where(np.isnan(density))[0]] = 1e5
        full_bins = np.where(density < 700)
        
        # full_bins = np.array([not y for y in np.isnan(lheight)])
        lheight = lheight[full_bins]
        icedepth = np.sum(lheight) + lheight[-1] / 2
        # Get property and absolute depth
        lprop = ds.sel(time=date,bin=bin)['layertemp'].to_numpy()[full_bins]
        ldepth = np.array([np.sum(lheight[:i+1])-(lheight[i]/2) for i in range(len(lheight))])
        height_above_ice = icedepth - ldepth
        # Plot output data
        axes[i].plot(lprop,height_above_ice,label='Model')

        # Plot iButton data
        snowdepth = ds.sel(time=date,bin=bin)['snowdepth'].to_numpy()
        tempdata = df.loc[date].to_numpy()
        idx = np.where(depth_0 < snowdepth)
        axes[i].plot(tempdata[idx],depth_0[idx],label='iButton')

        axes[i].set_title(str(date)[:10])
    axes[0].legend()
    fig.supxlabel('Temperature (C)')
    axes[0].set_ylabel('Depth (m)')
    return

def stacked_eb_barplot(ds,time,res='d',t='',savefig=False):
    """
    Returns a barplot where energy fluxes are stacked

    Parameters
    ----------
    ds : xr.Dataset
        Dataset object containing the model output
    time : list-like   
        Either len-2 list of [start date, end date], or a list of datetimes
    res : str
        Abbreviated time resolution to plot (e.g. '12h' or 'd')
    t : str
        Title of plot
    """
    fig,ax = plt.subplots(figsize=(10,5))
    vars = ['SWnet','all_but_shortwave'] #'SWnet','LWnet'
    ds['all_but_shortwave'] = ds['LWnet'] + ds['latent']+ ds['sensible']+ ds['ground']+ ds['rain']

    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq='h')
    ds = ds.sel(time=time)
    ds = ds.resample(time=res).mean(dim='time')
    bottom=0
    for i,var in enumerate(np.array(vars)):
        vardata = ds[var].to_numpy().T[0]
        if i==0:
            ax.bar(ds.coords['time'],vardata,label='Net Shortwave')
        else:
            bottom = ds[vars[i-1]].to_numpy().T[0]+bottom
            bottom[np.where(bottom<0)] = 0
            ax.bar(ds.coords['time'],vardata,bottom=bottom,label='All Other Fluxes')
    # ax.plot(ds.coords['time'],ds['meltenergy'],label='melt energy',color='black',linewidth=.6,alpha=0.7)
    date_form = mpl.dates.DateFormatter('%d %b %Y')
    ax.xaxis.set_major_formatter(date_form)
    ax.set_ylabel('Fluxes (W/m2)')
    ax.legend(loc='upper left')
    fig.suptitle(t)
    if savefig:
        plt.savefig(savefig,dpi=300)
    plt.show()

def plot_avgs(ds,time,title=False):
    """
    Plots heat fluxes, surface/air temperature, and mass balance terms, averaged monthly and then interannually.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset object containing the model output
    time : list-like   
        Either len-2 list of [start date, end date], or a list of datetimes
    """
    nyr = pd.to_datetime(time[0]).year - pd.to_datetime(np.array(time)[-1]).year
    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq='h')
    months = np.arange(1,13)

    fig,axes = plt.subplots(3,3,sharex=True,sharey='row',figsize=(12,6))
    varnames_idx = ['SWnet','LWnet','sensible','latent','rain','meltenergy','surftemp','melt','runoff','refreeze','accum']
    varnames = ['SWnet','LWnet','sensible','latent','rain','meltenergy','surftemp','melt','runoff','refreeze','accum']
    heat = ['SWnet','LWnet','sensible','latent','rain','meltenergy']
    temp = ['surftemp']
    mb = ['melt','runoff','refreeze','accum','MB']

    airtemp = np.zeros((3,12))
    for b in range(len(ds.coords['bin'])):
        climateds = xr.open_dataset('/home/claire/research/Output/EB/climateds.nc').isel(bin=b).to_pandas()
        monthly = climateds['bin_temp'].resample('M').mean()
        monthly_avg = np.mean(monthly[:(nyr*12)].values.reshape((nyr,12)),axis=0)
        airtemp[b,:] = monthly_avg

    for bin_no in range(len(ds.coords['bin'])):
        df = ds[varnames_idx].isel(bin=bin_no).to_pandas()
        df['melt'] = df['melt'] * -1
        
        for var in varnames:
            if var in ['melt','runoff','refreeze','accum','MB']:
                monthly = df[var].resample('M').sum()
            else:
                monthly = df[var].resample('M').mean()
            monthly_avg = np.mean(monthly[:(nyr*12)].values.reshape((nyr,12)),axis=0)
            run_start_month = pd.Timestamp(ds.coords['time'].values[0]).month
            if run_start_month > 1:
                monthly_avg_jan = np.append(monthly_avg[13-run_start_month:],monthly_avg[:13-run_start_month],)
            else:
                monthly_avg_jan = monthly_avg

            axis = np.piecewise(var,[var in heat, var in temp, var in mb],[0,1,2])
            lw = 1 if var in ['meltenergy','surftemp'] else 0.5
            axes[int(axis),bin_no].plot(months,monthly_avg_jan,label=var,linewidth=lw)
        axes[1,bin_no].plot(months,airtemp[bin_no,:],linewidth=0.5,label='air temp')
        axes[1,bin_no].axhline(0,lw=0.3,color='gray')
        axes[bin_no,2].set_xticks(months)
    axes[0,0].set_ylabel('Energy Flux ($W / m^2$)')
    axes[1,0].set_ylabel('Temperature (C)')
    axes[2,0].set_ylabel('Mass balance (m w.e.)')

    binname = ['Lower','Middle','Upper']
    for i in range(3):
        axes[0,i].set_title(binname[i])
    axes[0,0].legend(loc='upper right',bbox_to_anchor=(1.25, 1.0))
    axes[1,0].legend()
    axes[2,0].legend()
    if not title:
        fig.suptitle(f'Gulkana Glacier (ERA5-Hourly)\nMonthly Averages Over {nyr}-yr Run')
    else:
        fig.suptitle(title)
    fig.supxlabel('Months')
    #plt.gcf().autofmt_xdate()
    plt.show()
    return

def plot_yrs(file,bin,nyr):
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    fig,axes = plt.subplots(3,nyr,sharey='row',sharex='col',figsize=(14,8))

    ds = xr.open_dataset(file)
    varnames_idx = ['SWin','SWout','LWin','LWout','sensible','latent','rain','meltenergy','surftemp','melt','runoff','refreeze','accum','snowdepth']
    varnames = ['SWnet','LWnet','sensible','latent','rain','meltenergy','melt','runoff','refreeze','accum','snowdepth']
    heat = ['SWnet','LWnet','sensible','latent','rain','meltenergy']
    temp = ['snowdepth']
    mb = ['melt','runoff','refreeze','accum','MB']

    df = ds[varnames_idx].isel(bin=bin).to_pandas()
    df['SWnet'] = df['SWin'] + df['SWout']
    df['LWnet'] = df['LWin'] + df['LWout']
    df['MB'] = df['accum']+df['refreeze']-df['melt']

    # Loop through variables to get monthly averages and plot them
    for var in varnames:
        if var in ['melt','runoff','refreeze','accum','MB']:
            monthly = df[var].resample('M').sum()
        else:
            monthly = df[var].resample('M').mean()
        monthly_avg = monthly[:(nyr*12)].values.reshape((nyr,12))
        
        axis = np.piecewise(var,[var in heat, var in temp, var in mb],[0,1,2])
        for yr in range(nyr):
            axes[int(axis),yr].plot(months,monthly_avg[yr,:],label=var)
            axes[int(axis),yr].set_xlabel(str(pd.to_datetime(ds.coords['time'].values[0]).year+yr))
            axes[int(axis),yr].set_ylabel(var)
            axes[int(axis),0].legend()
            axes[1,0].set_xlim(0,6)
    return

def plot_AWS(df,vars,time,t=''):
    """
    Plots heatmap of AWS data in the specified time period

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing AWS data as input to the model
    vars : list
        List of variable names to plot
    time : list-like   
        Either len-2 list of [start date, end date], or a list of datetimes
    t : str
        Title of plot
    """
    df = df.set_index(pd.to_datetime(df.index))
    start = pd.to_datetime(time[0])
    end = pd.to_datetime(time[-1])
    df = df.loc[start:end+pd.Timedelta(hours=23)]
    days = df.resample('d').mean().index
    hours = np.arange(0,24)

    fig,axs = plt.subplots(len(vars),sharex=True,layout='constrained')
    for i,var in enumerate(vars):
        vardata = df[var].to_numpy().reshape((len(days),24))
        if var in ['SWin','LWin']:
            vardata = vardata * 3600
        pc = axs[i].pcolormesh(days,hours,vardata.T, cmap='RdBu_r')
        ticks = np.linspace(np.ceil(np.min(vardata)),np.floor(np.max(vardata)),3)
        if ticks[1]%1 > 0:
            ticks =  np.linspace(np.ceil(np.min(vardata)),np.floor(np.max(vardata))+1,3)
        clb = fig.colorbar(pc,ax=axs[i],ticks=ticks.astype(int),aspect=10,pad=0.02)
        clb.ax.set_title(AWS_vars[var]['units'])
        axs[i].set_title(AWS_vars[var]['label'])
        axs[i].set_ylabel('Hour')
        yticks = mpl.ticker.MultipleLocator(6)
        axs[i].yaxis.set_major_locator(yticks)
    date_form = mpl.dates.DateFormatter('%d %b')
    axs[i].xaxis.set_major_formatter(date_form)
    fig.suptitle(t)
    plt.show()

def compare_AWS(df_list,vars,time,labels=None,t='',res='d',y=''):
    fig,axs = plt.subplots(sharex=True,layout='constrained')
    linestyles = ['-','--','-.',':']
    for i,df in enumerate(df_list):
        df = df.set_index(pd.to_datetime(df.index))
        df[['SWout','LWout']] = df[['SWout','LWout']] * -1
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[-1])
        df = df.loc[start:end+pd.Timedelta(hours=23)]
        df = df.resample(res).mean()

        for var in vars:
            vardata = df[var].to_numpy()
            if not np.all(np.isnan(vardata)):
                axs.plot(df.index,vardata,label=var+': '+labels[i],linestyle=linestyles[i])
    date_form = mpl.dates.DateFormatter('%d %b')
    axs.legend()
    axs.set_ylabel(y)
    axs.xaxis.set_major_formatter(date_form)
    fig.suptitle(t)
    plt.show()

def plot_avg_layers(file,bin,nyr):
    """
    Plots layer temperature, density, water content and layer height averaged first across all layers,
    then averaged between years. 
    """
    ds = xr.open_dataset(file)
    fig,axes = plt.subplots(2,2,sharex=True,figsize=(8,6)) #,sharex=True,sharey='row',figsize=(12,5)
    idxs = [[0,0],[0,1],[1,0],[1,1]]
    days =  np.arange(365)
    for ax,var in enumerate(['layertemp','layerdensity','layerwater','snowdepth']):
        snow = ds[var].sel(bin=bin).to_pandas()
        loop = True
        i=19
        while loop:
            if np.isnan(snow.iloc[i]).all and var not in ['snowdepth']:
                snow.drop(i,axis=1)
            i -=1
            if i == 0:
                break

        if var in ['layertemp','layerdensity']:
            snow = snow.mean(axis=1)
        elif var in ['snowdepth']:
            pass
        else:
            snow = snow.sum(axis=1)
        if var in ['layerwater']:
            snow = snow/1000 # to m w.e.
        snowdaily = snow.resample('d').mean()
        snowdaily = np.mean(snow[:nyr*365].values.reshape((nyr,365)),axis=0)

        idx = idxs[ax]
        axes[idx[0],idx[1]].plot(days,snowdaily,label=var)
        axes[idx[0],idx[1]].set_title(var+'   '+ds[var].attrs['units'])
    axes[1,0].set_title('water content    m w .e')
    plt.gcf().autofmt_xdate()
    # plt.savefig('/home/claire/research/Output/EB/subsurfplot.png')
    plt.show()
    return

def plot_layers(ds,vars,dates):
    fig,axes = plt.subplots(len(vars),len(dates),sharey=True,sharex=True,figsize=(8,4)) #,sharex=True,sharey='row'
    for i,var in enumerate(vars):
        for j,date in enumerate(dates):
            for bin in ds.coords['bin'].values:
                lheight = ds.sel(time=date,bin=bin)['layerheight'].to_numpy()
                full_bins = np.array([not y for y in np.isnan(lheight)])
                bins = np.where(ds.sel(time=date,bin=bin)['layerdensity']<600)[0]
                lheight = lheight[bins]
                lprop = ds.sel(time=date,bin=bin)[var].to_numpy()[bins]
                ldepth = -1*np.array([np.sum(lheight[:i+1])-(lheight[i]/2) for i in range(len(lheight))])
                if len(vars) > 1:
                    axes[i,j].plot(lprop,ldepth,label='bin '+str(bin))
                    axes[i,j].set_xlabel(var)
                    axes[0,j].set_title(str(date)[:10])
                    axes[i,0].legend()
                    axes[i,0].set_ylabel('Depth (m)')
                else:
                    axes[j].plot(lprop,ldepth,label='bin '+str(bin))
                    axes[j].set_xlabel(var)
                    axes[j].set_title(str(date)[:10])
                    axes[0].legend()
                    axes[0].set_ylabel('Depth (m)')
        
    # fig.supxlabel(varprops[var]['label'])
    return

def plot_single_layer(ds,layer,vars,time,cumMB=False,t='',vline=None):
    if len(time) == 2:
        start = pd.to_datetime(time[0])
        end = pd.to_datetime(time[1])
        time = pd.date_range(start,end,freq='h')
    fig,axes = plt.subplots(len(vars),sharex=True,figsize=(8,1.2*len(vars)),layout='constrained')
    for i,var in enumerate(vars):
        if vline:
            axes[i].axvline(vline,c='r',linewidth=0.6)
        for bin in ds.coords['bin'].values:
            if 'layer' in var:
                lprop = ds.sel(time=time,bin=bin,layer=layer)[var].to_numpy()
                axes[i].plot(time,lprop,label='bin '+str(bin))
            else:
                if var in ['melt','runoff','accum','refreeze'] and cumMB:
                    lprop = ds.sel(time=time,bin=bin)[var].cumsum().to_numpy()
                else:
                    lprop = ds.sel(time=time,bin=bin)[var].to_numpy()
                axes[i].plot(time,lprop,label='bin '+str(bin))
            axes[i].legend()
            axes[i].set_title(varprops[var]['label'])
            if 'Cum.' in varprops[var]['label'] and not cumMB:
                axes[i].set_title(varprops[var]['label'][5:])
            axes[i].set_ylabel(varprops[var]['units'])
    date_form = mpl.dates.DateFormatter('%d %b')
    axes[i].xaxis.set_major_formatter(date_form)
    fig.suptitle(t)
    return

def plot_monthly_layer_avgs(file,var,dates_to_plot):
    ds = xr.open_dataset(file)
    fig,axes = plt.subplots(1,len(dates_to_plot),sharey=True,sharex=True,figsize=(8,4)) #,sharex=True,sharey='row'
    df = ds['snowdepth'].to_pandas()
    snowdepth_monthly = df.resample('M').mean()
    # for each month, find average snow depth
    # interpolate the variable of interest at new depths, with max depth being the average snow depth of the month
    # take mean of resampled variables
    # plot new depths vs. monthly means
    ax=0
    for month in range(12):
        snowdepth = snowdepth_monthly.iloc[month]
        for bin_no in [0,1,2]:
            var_data = ds[var].isel(bin=bin_no).to_numpy()
            depth_data = ds['layerheight'].isel(bin=bin_no).to_numpy()
            new_depths = np.linspace(0,snowdepth.iloc[bin_no],20)

            zeros = np.zeros((len(ds.coords['time'].values),20))
            var_interp = zeros.copy()
            for i,t in enumerate(ds.coords['time'].values):
                var_interp[i,:] = np.interp(new_depths,depth_data[i,:],var_data[i,:])
            da = xr.DataArray(data=var_interp,
                    coords=dict(
                        time=(['time'],ds.coords['time'].values),
                        depth=(['depth'],new_depths)
                        ))
            da_monthly = da.resample(time='M').mean()
            if month in months_to_plot:
                axes[ax].plot(da.isel(time=month).data,-1*da.coords['depth'].values,label='Bin '+str(bin_no))
        if month in months_to_plot: 
            axes[ax].set_xlabel(var)
            axes[0].set_ylabel('Depth (m)')
            month_dict = {'0':'Jan','1':'Feb','2':'Mar','3':'Apr','4':'May','5':'Jun',
                        '6':'Jul','7':'Aug','8':'Sept','9':'Oct','10':'Nov','11':'Dec'}
            axes[ax].set_title(month_dict[str(month)])
            axes[ax].axhline(-snowdepth[0],color=colors[0],linestyle='--')
            axes[ax].axhline(-snowdepth[1],color=colors[1],linestyle='--')
            axes[ax].axhline(-snowdepth[2],color=colors[2],linestyle='--')
            ax += 1
    axes[len(months_to_plot)-1].legend()
    return