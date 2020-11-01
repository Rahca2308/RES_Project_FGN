#Module for definening functions
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
def hej2():
    print('hej')

    
def annuity(n,r):
    """Calculate the annuity factor for an asset with lifetime n years and
    discount rate of r, e.g. annuity(20,0.05)*20 = 1.6"""

    if r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n
    
def cfplot(CF_wind,CF_solar):
    CF_wind.index = pd.to_datetime(CF_wind.index)  
    CF_wind=CF_wind.resample('D').mean()
    
    CF_solar.index = pd.to_datetime(CF_solar.index)  
    CF_solar=CF_solar.resample('D').mean()
    
    CF_wind.plot(color="blue",label="onshore wind",lw='0.5')
    CF_solar.plot(color="orange",label="solar",lw='0.5')
    
    #Implement duration curve
    #df=df.sort_values(['CHE'])
    #df=df.reset_index(drop=True)
    #df.reset_index().plot(kind='line', x='index', y='CHE',color=color)
    
    plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.xlabel('time')
    plt.ylabel('CF')
    plt.title("Capacity factor through a year")
    
    
    
def intanvar(a,b,network,df_elec,df_onshorewind,df_solar,df_ror,df_hydrores,co2):
    years=np.arange(a,b+1)
    years=[1991,1994,1997,1999,2003,2006,2009,2011,2013]
    df_optcap = pd.DataFrame(columns=network.generators.p_nom_opt.index,index=years)
    for i in years:
        #network = pypsa.Network()
        hours = pd.date_range('{}-01-01T00:00Z'.format(i),'{}-12-31T23:00Z'.format(i), freq='H')
        network.set_snapshots(hours) #fucks with snapsshots?

        # add load to the bus
        df_elec.index=network.snapshots #Convert electricity demand index to be the same as "hours"
        network.loads_t['p_set'].load=df_elec #Set new demand load

        #Define capacity factors for that year
        CF_wind = df_onshorewind['CHE'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
        network.generators_t.p_max_pu['onshorewind']=CF_wind

        CF_solar = df_solar['CHE'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
        network.generators_t.p_max_pu['solar']=CF_solar
        
        df_ror.index=network.snapshots #Set index to same timestamp as hours
        network.generators_t.p_max_pu['ror']=df_ror
        
        df_hydrores.index=network.snapshots #Set index to same timestamp as hours
        network.generators_t.p_max_pu['hydrores']=df_hydrores

        #set co2 limit
        network.global_constraints.constant=co2 #Set Co2 contraint 
        
        #Solve network
        network.lopf(network.snapshots, 
                     solver_name='gurobi')

        #Add to list
        df_optcap.loc[i] = network.generators.p_nom_opt.values
        
    return(years,df_optcap)

def intanvarplot(df_optcap,network,colors,years):
    for i,name  in enumerate(df_optcap.columns):
        plt.plot(df_optcap.index,df_optcap[name],label=name,color=colors[i],ls='--')
        plt.plot(df_optcap.index,[df_optcap[name].mean()]*len(years),label='{}-mean'.format(name),color=colors[i],lw=1.5)
    plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.xlabel('years')
    plt.ylabel('Optimum installed capicity (MW)')
    plt.title("Optimal capacity through the years")
    
def plotstorage(a,b,network,title="None"):
    plt.plot(network.storage_units_t.p['PHS'][a:b], color='blue', label='Pumped Hydro Storage')
    plt.plot(network.links_t.p0['batterylink1'][a:b], color='purple', label='battery charge')
    plt.plot(network.links_t.p1['batterylink2'][a:b], color='orange', label='battery discharge')
    plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.ylabel('Discharge (-) / Charge (+) (MW)')
    
    if title=="None":
        plt.title('Storage power throught the hours {} to {}'.format(a,b))
    else:
        plt.title(title)
    
    plt.show()


