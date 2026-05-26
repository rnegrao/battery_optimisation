import math
import numpy as np
import pandas as pd
import pulp
from datetime import datetime, timedelta

def load_data():

    '''LOAD data from excel files

    Parameters:
        None

    Returns:
        d_ff_merged : DataFrame
            Data frame with
            DATE   – half-hourly timestamp 
            Market 1 Price [£/MWh]  (half-hourly)
            Market 2 Price [£/MWh]  (half-hourly)
            Market 1 Price [£/MWh]  (daily; same value repeated for every HH in a day)

    Save raw_data_output.csv with the merged data for cheking
    '''
    
    df_Half_hourly_data = pd.read_excel("Second Round Technical Question - Attachment 2.xlsx",
                                    dtype={"DATE": str, "Market 1 Price [£/MWh]": float, "Market 2 Price [£/MWh]": float},
                                    sheet_name="Half-hourly data",
                                    usecols=["DATE", "Market 1 Price [£/MWh]", "Market 2 Price [£/MWh]"])
    df_Daily_data = pd.read_excel("Second Round Technical Question - Attachment 2.xlsx",
                                    dtype={"DATE": str, "Market 3 Price [£/MWh]": float},
                                    sheet_name="Daily data")    

    '''Merging dataframes filling the NAN with previous values'''
    df_hh = df_Half_hourly_data
    df_dd = df_Daily_data
    df_hh_merged = pd.merge_ordered(df_hh, df_dd, on='DATE', how='left', fill_method='ffill')
    df_hh_merged.to_csv('raw_data_output.csv', index=False , sep=' ')
    
    return df_hh_merged

'''BATTERY SYSTEM PARAMETERS'''
max_storage_volume = 4.0 #MWh
min_storage_volume = 0.0 #MWh
max_charging_rate = 2.0  #MW
max_discharge_rate = 2.0 #MW
battery_charging_efficiency = 0.95  #0.05 (energy losses)
battery_discharge_efficiency = 0.95 #0.05 (energy losses)
duration_time_hh = 0.5 #h    
duration_time_day = 24 #h
energy_stored_ini = 1.0 #MWh (initial energy state)

def optimization_model(df: pd.DataFrame,
                    max_storage_volume: float       = max_storage_volume,
                    min_storage_volume: float       = min_storage_volume,
                    energy_stored_ini: float        = energy_stored_ini,
                    max_charging_rate: float        = max_charging_rate,
                    max_discharge_rate: float       = max_discharge_rate,
                    battery_charging_efficiency: float           = battery_charging_efficiency,
                    battery_discharge_efficiency: float          = battery_discharge_efficiency,
                    solver_name: str      = "CBC",
                    time_limit_s: int     = 300
                       ):

    '''Define and optimize the model
    
    Parameters:
        df                        : DataFrame with columns [datetime, market1, market2, market3]
        max_storage_volume        : Maximum state-of-charge (MWh)
        min_storage_volume        : Minimum state-of-charge (MWh)
        energy_stored_ini         : Initial state-of-charge (MWh)
        max_charging_rate:        : Max charge rate (MW)
        max_discharge_rate        : Max discharge rate (MW)
        battery_charging_efficiency          : Charging efficiency 
        battery_discharge_efficiency         : Discharging efficiency 
        solver_name   : PuLP solver to use ('CBC')
        time_limit_s  : Solver time limit in seconds

    Returns:
        dictionary with keys:
            profit,
            data (DataFrame)
        
    '''
    
    '''Data ingestion'''
    df = df.copy().sort_values("DATE").reset_index(drop=True)
    df["day"] = pd.to_datetime(df["DATE"]).dt.normalize()
    
    '''Define half-hourly and daily time slots lists'''
    T = len(df)
    slots = list(range(T))
    '''Daily mapping: day index -> list of HH slot indices'''
    dates = df["day"].unique()
    D = len(dates)
    days  = list(range(D))
    
    '''Create the data strucutures required to be populated with parameters linking day -> day index -> hour index '''    
    date_to_day = {d: i for i, d in enumerate(dates)} 
    day_slots: dict[int, list[int]] = {i: [] for i in range(D)}
    for t, row in df.iterrows():
        day_slots[date_to_day[row["day"]]].append(t)

    price1 = df["Market 1 Price [£/MWh]"].values
    price2 = df["Market 2 Price [£/MWh]"].values
    ''' Market 3 daily price (take first value of each day)'''
    price3 = np.array([df.loc[df["day"] == d, "Market 3 Price [£/MWh]"].iloc[0] for d in dates])

    '''Create the model: Judging the input prices the power is defined to give maximum gains'''
    model = pulp.LpProblem("BatteryOptimisation", pulp.LpMaximize)
    p1_c = pulp.LpVariable.dicts("p1_charge",    slots, lowBound=0)
    p1_d = pulp.LpVariable.dicts("p1_discharge", slots, lowBound=0)
    p2_c = pulp.LpVariable.dicts("p2_charge",    slots, lowBound=0)
    p2_d = pulp.LpVariable.dicts("p2_discharge", slots, lowBound=0)
    
    p3_c  = pulp.LpVariable.dicts("p3_charge",    days, lowBound=0)
    p3_d  = pulp.LpVariable.dicts("p3_discharge", days, lowBound=0)
    '''Define battery energy constrains to be considered in the daily strategy'''
    soc   = pulp.LpVariable.dicts("soc", slots, lowBound = min_storage_volume, upBound = max_storage_volume)

    '''Define model: Revenue from discharge minus charge'''
    revenue_hh = pulp.lpSum(
        (price1[t] * p1_d[t] + price2[t] * p2_d[t] ) * duration_time_hh
        - (price1[t] * p1_c[t] + price2[t] * p2_c[t] ) * duration_time_hh
        for t in slots
        )
    revenue_day = pulp.lpSum(
        ( price3[d] * p3_d[d] - price3[d] * p3_c[d] ) * duration_time_day
        for d in days
        )

    model += revenue_hh + revenue_day

    '''Define model constrains at each time slot: model += constraint'''  
    for t in slots:
        d = date_to_day[df.loc[t, "day"]]

        ''' Total charge power <= max_charging_rate'''
        model += (p1_c[t] + p2_c[t] + p3_c[d] <= max_charging_rate,
                 f"max_charge_{t}")

        ''' Total discharge power <= max_discharge_rate'''
        model += (p1_d[t] + p2_d[t] + p3_d[d] <= max_discharge_rate,
                 f"max_discharge_{t}")

        '''Charge power evolution MW'''
        total_charge_power    = p1_c[t] + p2_c[t] + p3_c[d]
        total_discharge_power = p1_d[t] + p2_d[t] + p3_d[d]
        
        if t == 0:
            '''in MWh '''
            model += (soc[t] == energy_stored_ini
                     + battery_charging_efficiency * total_charge_power * duration_time_hh
                     - (1 / battery_discharge_efficiency) * total_discharge_power * duration_time_hh,
                     f"soc_init_{t}")
        else:
            '''in MWh'''
            '''soc[t] = soc[t-1] + charging_efficiency * p_charge * dt 
                                 - (1/discharging_efficiency) * p_discharge * dt '''
            model += (soc[t] == soc[t - 1]
                     + battery_charging_efficiency * total_charge_power * duration_time_hh
                     - (1 / battery_discharge_efficiency) * total_discharge_power * duration_time_hh,
                     f"soc_evol_{t}")

    '''Run optimization routine'''   
    print(f"  Optimising... (solver={solver_name}, limit={time_limit_s}s)")
    model.solve(pulp.PULP_CBC_CMD(msg=1, timeLimit = time_limit_s))
    status = pulp.LpStatus[model.status]
    print(f"  Solver status: {status}")

    '''Extract the results for each time slots'''
    data_rows = []
    for t in slots:
        d = date_to_day[df.loc[t, "day"]]
        row = {
            "datetime":        df.loc[t, "DATE"],
            "date":            df.loc[t, "day"],
            "price_m1":        price1[t],
            "price_m2":        price2[t],
            "price_m3":        price3[d],
            "p1_charge_mw":    p1_c[t].varValue,
            "p1_discharge_mw": p1_d[t].varValue,
            "p2_charge_mw":    p2_c[t].varValue,
            "p2_discharge_mw": p2_d[t].varValue,
            "p3_charge_mw":    p3_c[d].varValue,
            "p3_discharge_mw": p3_d[d].varValue,
            "soc_mwh":         soc[t].varValue
        }
        '''Revenue per slot'''
        row["revenue_m1"] = (row["p1_discharge_mw"] - row["p1_charge_mw"]) * price1[t] * duration_time_hh
        row["revenue_m2"] = (row["p2_discharge_mw"] - row["p2_charge_mw"]) * price2[t] * duration_time_hh
        '''Market 3 revenue is attributed once per slot'''
        row["revenue_m3"] = (row["p3_discharge_mw"] - row["p3_charge_mw"]) * price3[d] * duration_time_hh

        row["total_revenue"] = row["revenue_m1"] + row["revenue_m2"] + row["revenue_m3"]

        '''Battery charging discharging per slot'''
        row["p_charge"] = ( row["p1_charge_mw"] + row["p2_charge_mw"] + row["p3_charge_mw"] )
        row["p_discharge"] = ( row["p1_discharge_mw"] + row["p2_discharge_mw"] + row["p3_discharge_mw"] )        
    
        '''append row to the dataframe'''
        data_rows.append(row)

    data_frame = pd.DataFrame(data_rows)
    total_profit = data_frame["total_revenue"].sum()

    print("\n Optimisation complete.")

    return {
        "profit"    :   total_profit,
        "data"      :   data_frame
    }

def print_summary(result: dict):
    
    table = result["data"].copy().sort_values("datetime").reset_index(drop=True)
    table["year"] = pd.to_datetime(table["datetime"]).dt.year

    capex = 500000.0
    operational_costs_per_year = 5000.0
    
    ''' Annual breakdown '''
    '''Sum the total_revenue grouped by year'''
    annual = table.groupby("year")["total_revenue"].sum()
    print("-" *50)
    print(" Annual profit breakdown:")
    data_row = []
    n_year = 0
    for yr, profit in annual.items():
        row = {"Year"  : yr,
               "Profit": profit}
        data_row.append(row)
        print(f"  {yr}: £{profit:,.2f}")
        n_year += 1
        
    data_frame = pd.DataFrame(data_row)
    data_frame.to_csv("annual_profit_breakdown.csv", index=False , sep=' ')
    print()
    
    ''' Market breakdown (full period) '''
    m1_rev = table["revenue_m1"].sum()
    m2_rev = table["revenue_m2"].sum()
    m3_rev = table["revenue_m3"].sum()
    print(" Profit by market:")
    print(f"  Market 1 (half-hourly)  : £{m1_rev:,.2f}")
    print(f"  Market 2 (half-hourly)  : £{m2_rev:,.2f}")
    print(f"  Market 3 (daily)        : £{m3_rev:,.2f}")
    print(f"  Total profit (2018-2020): £{m1_rev+m2_rev+m3_rev:,.2f}")
    print()
    
    print(" State of charge statistics (MWh):")
    print(f"  Min : {table['soc_mwh'].min():.4f}")
    print(f"  Max : {table['soc_mwh'].max():.4f}")
    print(f"  Mean: {table['soc_mwh'].mean():.4f}")
    print("-" *50)

    ''' Profit minus capex and operational costs '''
    total = m1_rev + m2_rev + m3_rev - capex - n_year*operational_costs_per_year
    print(" Profit minus capex and operational costs: ")
    print(f"  Investment returns (2018-2020): £{ total:,.2f}")
    print("-" *50)
    
if __name__ == "__main__":

    '''Load data'''
    df_hh = load_data()
    '''Call optimisation model'''
    result = optimization_model(df_hh,
                    max_storage_volume,
                    min_storage_volume,
                    energy_stored_ini,
                    max_charging_rate,
                    max_discharge_rate,
                    battery_charging_efficiency,
                    battery_discharge_efficiency,"CBC",
                    300)
    '''Print data'''
    print_summary(result)
    '''Save data'''
    result["data"].to_csv("battery_logs.csv", index=False , sep=' ')

    
