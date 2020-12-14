#Module for definening functions
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
def hej():
    print('hej')

    
def annuity(n,r):
    """Calculate the annuity factor for an asset with lifetime n years and
    discount rate of r, e.g. annuity(20,0.05)*20 = 1.6"""

    if r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n

def plotdispatch(a,b,network,colors,title="None",dispstor=False):
    """plots dispatch with the option to include storage technologies"""
    #Plot load
    plt.plot(network.loads_t.p['load'][a:b], color=colors['demand'], label='demand')
    
       
    #Plot generators
    for i in network.generators.index:
        if network.generators.bus[i] == 'electricity bus':
            plt.plot(network.generators_t.p[i][a:b], color=colors[i], label=i)
    
    #Dispatch and storage
    if dispstor == True:
        if not network.links.empty: #Plot link contributions
            for i in network.links.index:
                if network.links.bus0[i] == 'electricity bus' or network.links.bus1[i] == 'electricity bus': #only swiss
                    if i == 'batterylink1' or i == 'hydrogenlink1':
                        plt.plot(network.links_t.p0[i][a:b], label=i) #plots negative if storing energy
                    else:
                        plt.plot(network.links_t.p1[i][a:b], label=i)
        if not network.storage_units.empty: #Plot stor_units contribution
            for i in network.storage_units.index:
                plt.plot(network.storage_units_t.p[i][a:b], label=i)
    
    plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.ylabel('Dispatch (MW)')
    
    if title=="None":
        plt.title('Dispatch throught the hours {} to {}'.format(a,b))
    else:
        plt.title(title)
    
    plt.show()
    
def hydrosoc(a,b,network,title="None"):
    """Plot storage SOC through the time period a to b"""
    
    plt.plot(network.storage_units_t.state_of_charge['hydrores'][a:b]/1000, color='tab:blue', label='Hydro reservoirs')
    plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.ylabel('SOC (GWh)')
    if title=="None":
        plt.title('State-of-charge through the hours {} to {}'.format(a,b))
    else:
        plt.title(title)
    
    plt.show()

def elecmix(network,colors,title="None"):
    """Plot elecmix of network"""
    sizes = []
    colours=[]
    labels=[]
    for i in network.generators.index:
        if network.generators.bus[i] == 'electricity bus':
            sizes.append(network.generators_t.p[i].sum())
            colours.append(colors[i])
            labels.append(i)
            
    for i in network.storage_units.index:
        if network.storage_units.bus[i] == 'electricity bus':
            sizes.append(network.storage_units_t.p[i].sum())
            colours.append(colors[i])
            labels.append(i)
    
    #for i in network.links.index:
    #    if network.links.bus1[i] == "electricity bus":
    #        sizes.append(-network.links_t.p1[i].sum()) #minus b/c (positive if branch is withdrawing power from bus1).
    #        colours.append(colors[i])
    #        labels.append(i)
    
    plt.pie(sizes, 
            colors=colours, 
            labels=labels,
            autopct='%1.1f%%',
            wedgeprops={'linewidth':0})
    plt.axis('equal')

    if title == 'None':
        plt.title('Electricity mix', y=1.07)
    else:
        plt.title(title)
    plt.show()
   
    
def cfplot(CF_wind,CF_solar,df_ror,timescale):
    """plots CF in days"""
    CF_wind.index = pd.to_datetime(CF_wind.index)  
    CF_wind=CF_wind.resample(timescale).mean()
    
    CF_solar.index = pd.to_datetime(CF_solar.index)  
    
    
    CF_ror=df_ror/df_ror.max()
    CF_ror.index=CF_solar.index #reindex ror while we're at it
    CF_ror=CF_ror.resample(timescale).mean()
    CF_solar=CF_solar.resample(timescale).mean()
    
    CF_ror.plot(color="blue",label="Run-of-river",lw='0.5')
    CF_wind.plot(color="purple",label="onshore wind",lw='0.5')
    CF_solar.plot(color="orange",label="solar",lw='0.5')
    
    
    #Implement duration curve
    #df=df.sort_values(['CHE'])
    #df=df.reset_index(drop=True)
    #df.reset_index().plot(kind='line', x='index', y='CHE',color=color)
    
    #CF_ror=CF_ror.sort_values(['Inflow [GWh]'], ascending=False)
    #CF_ror.index=pd.to_datetime(CF_solar.index) 
    #CF_ror.plot(color="blue",label="Run-of-river",lw='0.5',ls='-',alpha=0.5)
    
    plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.xlabel('time')
    plt.ylabel('CF')
    plt.title("Capacity factor through a year")
    plt.grid(alpha=0.2)
    plt.show()
    
    
def intanvar(a,b,network,df_elec,df_onshorewind,df_solar,df_ror,df_hydrores,co2):
    """Create dataframe with the interanual variabilty of optimal capacities of the different renewable energy generators"""
    
    years=np.arange(a,b+1)
    years=[1991,1994,1997,1999,2003,2006,2009,2011,2013,2015]
    df_optcap = pd.DataFrame(columns=network.generators.p_nom_opt.index,index=years) #Create empty df with index
    for i in years:
        #network = pypsa.Network()
        hours = pd.date_range('{}-01-01T00:00Z'.format(i),'{}-12-31T23:00Z'.format(i), freq='H')
        network.set_snapshots(hours) #fucks with snapsshots?

        # add load to the bus
        df_elec.index=network.snapshots #Convert electricity demand index to be the same as "hours"
        network.loads_t['p_set'].load=df_elec['CHE'] #Set new demand load

        #Define capacity factors for that year
        CF_wind = df_onshorewind['CHE'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
        network.generators_t.p_max_pu['onshorewind']=CF_wind

        CF_solar = df_solar['CHE'][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
        network.generators_t.p_max_pu['solar']=CF_solar
        
        df_ror.index=network.snapshots #Set index to same timestamp as hours
        network.generators_t.p_max_pu['ror']=(df_ror/df_ror.max())["Inflow [GWh]"]
        
        df_hydrores.index=network.snapshots #Set index to same timestamp as hours
        network.storage_units_t.inflow['hydrores']=df_hydrores["Inflow [GWh]"]

        #set co2 limit
        network.global_constraints.constant=co2 #Set Co2 contraint 
        
        #Solve network
        network.lopf(network.snapshots, 
                     solver_name='gurobi')

        #Add to dataframe
        df_optcap.loc[i] = network.generators.p_nom_opt.values
        
    return(years,df_optcap)

def intanvarplot(df_optcap,network,colors,years):
    """Plots interannualvariabilty of the different renewable energy generators"""
    
    for i,name  in enumerate(df_optcap.columns):
        plt.plot(df_optcap.index,df_optcap[name],label=name,color=colors[name],ls='--')
        plt.plot(df_optcap.index,[df_optcap[name].mean()]*len(years),label='{}-mean'.format(name),color=colors[name],lw=1.5)
    plt.legend(fancybox=True, shadow=True, loc='upper left')
    plt.xlabel('years')
    plt.ylabel('Optimum installed capicity (MW)')
    plt.title("Optimal capacity through the years")
    
def plotstorage(a,b,network,title="None"):
    """Plot storage dispacities thrugh the time period a to b"""
    
    plt.plot(network.storage_units_t.p['hydrores'][a:b], color='tab:blue', label='hydrores')
    plt.plot(network.storage_units_t.p['PHS'][a:b], color='blue', label='Pumped Hydro Storage')
    plt.plot(network.links_t.p0['batterylink1'][a:b], color='orange', label='battery charge')
    plt.plot(network.links_t.p1['batterylink2'][a:b], color='orange', label='battery discharge')
    plt.plot(network.links_t.p0['hydrogenlink1'][a:b], color='purple', label='hydrogen charge')
    plt.plot(network.links_t.p1['hydrogenlink2'][a:b], color='purple', label='hydrogen discharge')
    
    plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.ylabel('Charge (-) / Discharge (+) (MW)')
    plt.grid(alpha=0.2)
    if title=="None":
        plt.title('Storage power throught the hours {} to {}'.format(a,b))
    else:
        plt.title(title)
    
    plt.show()

def plotsoc(a,b,network,hydrores=False,title="None"):
    """Plot storage SOC through the time period a to b"""
        
    plt.plot(network.storage_units_t.state_of_charge['PHS'][a:b]/1000, color='blue', label='Pumped Hydro Storage')
    plt.plot(network.stores_t.e.Battery[a:b]/1000, color='orange', label='Battery')
    plt.plot(network.stores_t.e.Hydrogen[a:b]/1000, color='purple', label='Hydrogen')
    if hydrores == True:
        plt.plot(network.storage_units_t.state_of_charge['hydrores'][a:b]/1000, color='tab:blue', label='hydrores')
        
    plt.legend(fancybox=True, shadow=True, loc='upper left')
    plt.ylabel('SOC (GWh)')
    plt.grid(alpha=0.2)
        
    if title=="None":
        plt.title('State-of-charge through the hours {} to {}'.format(a,b))
    else:
        plt.title(title)
    
    plt.show()

def addcountry(network,country,df_elec,df_onshorewind,df_solar,df_ror,df_hydrores):
    """Add another country"""    
    
    # add load to the bus
    network.add("Load",
                "load {}".format(country), 
                bus="electricity bus {}".format(country), 
                p_set=df_elec[country])

    # Add onshore wind generator
    CF_wind = df_onshorewind[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
    capital_cost_onshorewind = annuity(30,0.07)*910000*(1+0.033) # in €/MW
    network.add("Generator",
                "onshorewind {}".format(country),
                bus="electricity bus {}".format(country),
                p_nom_extendable=True,
                carrier="onshorewind",
                #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
                capital_cost = capital_cost_onshorewind,
                marginal_cost = 0,
                p_max_pu = CF_wind)   
    
    # Add solar PV generator
    CF_solar = df_solar[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
    capital_cost_solar = annuity(25,0.07)*425000*(1+0.03) # in €/MW
    network.add("Generator",
                "solar {}".format(country),
                bus="electricity bus {}".format(country),
                p_nom_extendable=True,
                carrier="solar",
                #p_nom_max=1000, # maximum capacity can be limited due to environmental constraints
                capital_cost = capital_cost_solar,
                marginal_cost = 0,
                p_max_pu = CF_solar)
    
    # Add OCGT (Open Cycle Gas Turbine) generator
    capital_cost_OCGT = annuity(25,0.07)*560000*(1+0.033) # in €/MW
    fuel_cost = 21.6 # in €/MWh_th
    efficiency = 0.39
    marginal_cost_OCGT = fuel_cost/efficiency # in €/MWh_el
    network.add("Generator",
                "OCGT {}".format(country),
                bus="electricity bus {}".format(country),
                p_nom_extendable=True,
                carrier="gas",
                #p_nom_max=1000,
                capital_cost = capital_cost_OCGT,
                marginal_cost = marginal_cost_OCGT)
    
def addstor(network,country):
    """Add another country hydrogen and electric storage"""    
    if country == 'CHE':
            country =""
    else:
            country = " {}".format(country)
        
    #Add battery storage
    network.add("Bus","battery bus{}".format(country),carrier='DC')

    capital_cost_battery = annuity(15,0.07)*144600*(1+0.00) # in €/MW
    network.add("Store",
                "Battery{}".format(country),
                bus="battery bus{}".format(country),
                e_nom_extendable=True,
                capital_cost = capital_cost_battery
               )
    #dispatch link - inverter
    capital_cost_batterylink1 = annuity(20,0.07)*310000*(1+0.03) # in €/MW
    network.add("Link",
                "batterylink1{}".format(country),
                bus0="battery bus{}".format(country),
                bus1="electricity bus{}".format(country),
                capital_cost=capital_cost_batterylink1,
                p_nom_extendable=True,
                efficiency=0.87
               )                    
    #store link - inverter
    capital_cost_batterylink2=annuity(20,0.07)*310000*(1+0.03) # in €/MW
    network.add("Link",
                "batterylink2{}".format(country),
                bus1="battery bus{}".format(country),
                bus0="electricity bus{}".format(country),
                p_nom_extendable=True,
                capital_cost=capital_cost_batterylink2,
                efficiency=0.87
                )

    #Add hydrogen storage
    network.add("Bus","hydrogen bus{}".format(country),carrier='hydrogen')

    capital_cost_hydrogen = annuity(20,0.07)*8400*(1+0.00) # in €/MW
    network.add("Store",
                "Hydrogen{}".format(country),
                bus="hydrogen bus{}".format(country),
                e_nom_extendable=True,
                capital_cost = capital_cost_hydrogen
               )
    #dispatch link - fuel cell
    capital_cost_hydrogenlink1 = annuity(20,0.07)*339000*(1+0.03) # in €/MW
    network.add("Link",
                "hydrogenlink1{}".format(country),
                bus0="hydrogen bus{}".format(country),
                bus1="electricity bus{}".format(country),
                capital_cost=capital_cost_hydrogenlink1,
                p_nom_extendable=True,
                efficiency=0.58
               )                    
    #store link - electrolysis
    capital_cost_hydrogenlink2=annuity(18,0.07)*350000*(1+0.04) # in €/MW
    network.add("Link",
                "hydrogenlink2{}".format(country),
                bus1="hydrogen bus{}".format(country),
                bus0="electricity bus{}".format(country),
                p_nom_extendable=True,
                capital_cost=capital_cost_hydrogenlink2,
                efficiency=0.8
                )
    
def plotheat(a,b,network,colors,title="None",dispstor=False):
    """plots dispatch with the option to include storage technologies"""
    #Plot load
    plt.plot(network.loads_t.p['heatload'][a:b], color=colors['demand'], label='demand')
    
    #Plot generators
    for i in network.generators.index:
        if network.generators.bus[i] == 'heating bus':
            plt.plot(network.generators_t.p[i][a:b], color=colors[i], label=i)
    
   #Dispatch and storage
    if dispstor == True:
        if not network.links.empty: #Plot link contributions
            for i in network.links.index:
                if network.links.bus1[i] == "heating bus":
                    plt.plot(-network.links_t.p1[i][a:b], label=i, color=colors[i]) #minus b/c (positive if branch is withdrawing power from bus1).
        if not network.storage_units.empty: #Plot stor_units contribution
            for i in network.storage_units.index:
                if network.storage_units.bus[i] == "heating bus":
                    plt.plot(network.storage_units_t.p[i][a:b], label=i, color=colors[i])
    
    plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.ylabel('Heat (MW)')
    
    if title=="None":
        plt.title('Heating throught the hours {} to {}'.format(a,b))
    else:
        plt.title(title)
    
    plt.show()
    
def heatmix(network,colors,title="None"):
    """Plot heatmix of network"""
    sizes = []
    colours=[]
    labels=[]
    for i in network.generators.index:
        if network.generators.bus[i] == 'heating bus':
            sizes.append(network.generators_t.p[i].sum())
            colours.append(colors[i])
            labels.append(i)
    for i in network.links.index:
        if network.links.bus1[i] == "heating bus":
            sizes.append(-network.links_t.p1[i].sum()) #minus b/c (positive if branch is withdrawing power from bus1).
            colours.append(colors[i])
            labels.append(i)
    
    plt.pie(sizes, 
            colors=colours, 
            labels=labels,
            autopct='%1.1f%%',
            wedgeprops={'linewidth':0})
    plt.axis('equal')

    if title == 'None':
        plt.title('Heat mix', y=1.07)
    else:
        plt.title(title)
    plt.show()

def addiheat(network,df_heat):
         #add load to the bus
    network.add("Load",
                "heatload I", 
                bus="heating bus I", 
                p_set=df_heat['CHE']*0.15)

    # Add Gas boiler (centralised assumed)
    capital_cost_gasboiler = annuity(20,0.07)*175000*(1+0.015) # in €/MW #individual price
    fuel_cost = 21.6 # in €/MWh_th
    efficiency = 0.9
    marginal_cost_gasboiler = fuel_cost/efficiency # in €/MWh_el
    network.add("Generator",
                "gasboiler I",
                bus="heating bus I",
                p_nom_extendable=True,
                carrier="gas",
                capital_cost = capital_cost_gasboiler,
                marginal_cost = marginal_cost_gasboiler)

    # Add Resistive heater, as link
    capital_cost_resistive = annuity(20,0.07)*100000*(1+0.02) # in €/MW
    #marginal_cost_resistive = fuel_cost/efficiency # in €/MWh_el
    network.add("Link",
                "resistive I",
                bus0="electricity bus",
                bus1="heating bus I",
                p_nom_extendable=True,
                efficiency=0.9,
                capital_cost=capital_cost_resistive)

    # Add heatpump, as link
    capital_cost_heatpump = annuity(20,0.07)*1400000*(1+0.035) # in €/MW individual prize
    #marginal_cost_resistive = fuel_cost/efficiency # in €/MWh_el
    network.add("Link",
                "heat pump I",
                bus0="electricity bus",
                bus1="heating bus I",
                p_nom_extendable=True,
                efficiency=3, #efficiency/ COP assumed to be 3 bc schwitzerland is cold.
                capital_cost=capital_cost_heatpump)

def addheatstor(network,country):
    """Add heat storage to a country in the form of ITES and CTES"""
    if country == 'CHE':
        country =""
    else:
        country = " {}".format(country)
    
    edensity = 46.8 #kWh_th/m^3
    ## Links are assumed to be free for scaling
    #Add ITES
    network.add("Bus","ITES bus{}".format(country),carrier='heat') #
    capital_cost_ITES = annuity(20,0.07)*860000/edensity*(1+0.01) # in €/MW
    tau = 3 #timeconstant
    network.add("Store",
                "ITES{}".format(country),
                bus="ITES bus{}".format(country),
                e_nom_extendable=True,
                capital_cost = capital_cost_ITES,
                standing_loss = 1-np.exp(-1/(24*tau))
               )
    #dispatch link 
    network.add("Link",
                "ITESlink1{}".format(country),
                bus0="ITES bus{}".format(country),
                bus1="heating bus I{}".format(country),
                p_nom_extendable=True,
                efficiency=0.9
               )
    #store link 
    network.add("Link",
                "ITESlink2{}".format(country),
                bus0="heating bus I{}".format(country),
                bus1="ITES bus{}".format(country),
                p_nom_extendable=True,
                efficiency=0.9
               )
    #Add CTES
    network.add("Bus","CTES bus{}".format(country),carrier='heat')
    capital_cost_CTES = annuity(40,0.07)*30000/edensity*(1+0.01) # in €/MW
    tau = 180   #timeconstant
    network.add("Store",
                "CTES{}".format(country),
                bus="CTES bus{}".format(country),
                e_nom_extendable=True,
                capital_cost = capital_cost_CTES,
                standing_loss = 1-np.exp(-1/(24*tau))
               )
    #dispatch link 
    network.add("Link",
                "CTESlink1{}".format(country),
                bus0="CTES bus{}".format(country),
                bus1="heating bus{}".format(country),
                p_nom_extendable=True,
                efficiency=0.9
               )
    #store link 
    network.add("Link",
                "CTESlink2{}".format(country),
                bus0="heating bus{}".format(country),
                bus1="CTES bus{}".format(country),
                p_nom_extendable=True,
                efficiency=0.9
               )
    
    
def plotheatstorage(a,b,network,title="None"):
    """Plot storage dispacities thrugh the time period a to b"""
    
    
    plt.plot(network.links_t.p0['ITESlink1'][a:b], color='orange', label='ITES charge')
    plt.plot(network.links_t.p1['ITESlink2'][a:b], color='orange', label='ITES discharge')
    plt.plot(network.links_t.p0['CTESlink1'][a:b], color='purple', label='CTES charge')
    plt.plot(network.links_t.p1['CTESlink2'][a:b], color='purple', label='CTES discharge')
    
    plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.ylabel('Charge (-) / Discharge (+) (MW)')
    
    if title=="None":
        plt.title('Stored heat throught the hours {} to {}'.format(a,b))
    else:
        plt.title(title)
    
    plt.show()

def plotheatsoc(a,b,network,title="None",percent=False):
    """Plot storage SOC through the time period a to b"""
    if percent==False:
        plt.plot(network.stores_t.e.ITES[a:b]/1000, color='orange', label='ITES')
        plt.plot(network.stores_t.e.CTES[a:b]/1000, color='purple', label='CTES')
        plt.legend(fancybox=True, shadow=True, loc='upper right')
        plt.ylabel('SOC (GWh)')
        #plt.yscale('log')
    if percent==True:
        plt.plot(network.stores_t.e.ITES[a:b]/network.stores.e_nom_opt.ITES*100, color='orange', label='ITES')
        plt.plot(network.stores_t.e.CTES[a:b]/network.stores.e_nom_opt.CTES*100, color='purple', label='CTES')
        plt.legend(fancybox=True, shadow=True, loc='upper right')
        plt.ylabel('SOC (%)')
        
    if title=="None":
        plt.title('State-of-charge through the hours {} to {}'.format(a,b))
    else:
        plt.title(title)
    
    plt.show()
    
def marginalprice(a,b,network,title="None"):
    plt.plot(network.buses_t.marginal_price['electricity bus'][a:b])
    #plt.legend(fancybox=True, shadow=True, loc='upper right')
    plt.ylabel('Marginal Price (€)')
    if title=="None":
        plt.title('Marginal price through the hours {} to {}'.format(a,b))
    else:
        plt.title(title)
        