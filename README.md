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

```
 
  Optimising... (solver=CBC, limit=300s)
  Solver status: Optimal

 Optimisation complete.
--------------------------------------------------
 Annual profit breakdown:
  2018: £83,439.11
  2019: £82,298.66
  2020: £102,227.79

 Profit by market:
  Market 1 (half-hourly)  : £-605,925.65
  Market 2 (half-hourly)  : £1,094,779.62
  Market 3 (daily)        : £-220,888.41
  Total profit (2018-2020): £267,965.56

 State of charge statistics (MWh):
  Min : 0.0000
  Max : 4.0000
  Mean: 1.9349
--------------------------------------------------
 Profit minus capex and operational costs: 
  Investment returns (2018-2020): £-247,034.44
--------------------------------------------------

```


### 5. Note on AI use

I used Claude Sonnet 4.6 as an assistant to identify a suitable Python library for the optimization problem and to help me define the data structure required for integration with the optimization model. It helped accelerate the code implementation of the data ingestion workflow.
