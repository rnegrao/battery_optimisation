### 1. Summary

The aim is to optimize battery charge and discharge decisions across three electricity markets to maximize revenue respecting battery constraints and the available stored energy. 

The approach consists of defining a profit function based on the momentaneous power imported or exported for each market, together with the momentaneous battery state of charge (soc). 

Subsequently the optimization process then determines the optimal values of these variables considering the given electricity price for each market, as well as the rules to sell and buy energy for each market.   

### 2. List of dependencies:
    
Python: math, numpy, pandas, pulp
    
solver = "CBC"

### 3. Output 

a) battery_logs.csv: Output file with collums containing the battery charging and discharging information for each half-hourly 


b) annual_profit_breakdown.csv: Output file with the total annual profit over the time period


### 4. Program output
````
 
  Optimising... (solver=CBC, limit=300s)
  Solver status: Optimal

 Optimisation complete.
--------------------------------------------------
 Annual profit breakdown:
  2018: £144,971.99
  2019: £151,387.94
  2020: £294,344.51

 Profit by market:
  Market 1 (half-hourly)  : £-706,840.66
  Market 2 (half-hourly)  : £797,825.03
  Market 3 (daily)        : £499,720.07
  Total profit (2018-2020): £590,704.44

 State of charge statistics (MWh):
  Min : -0.0000
  Max : 4.0000
  Mean: 1.7327
--------------------------------------------------
 Profit minus capex and operational costs: 
  Investment returns (2018-2020): £75,704.44
--------------------------------------------------
´´´
