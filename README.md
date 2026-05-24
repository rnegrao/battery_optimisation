### 1. Summary

The aim is to optimize battery charge and discharge decisions across three electricity markets to maximize revenue respecting battery constraints and the available stored energy. 

The approach consists of defining a profit function based on the momentaneous power imported or exported for each market, together with the momentaneous battery state of charge (soc). 

Subsequently the optimization process then determines the optimal values of these variables considering the given electricity price for each market, as well as the rules to sell and buy energy for each market.   

### 2. List of dependencies:
    
Python: math, numpy, pandas, pulp
    
solver = "CBC"

### 3. Output 

a. battery_logs.csv: Output file with collums containing the battery charging and discharging information for each half-hourly 


b. annual_profit_breakdown.csv: Output file with the total annual profit
 
