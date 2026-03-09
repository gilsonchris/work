select db.branch_name_short
,FORMAT(SUM(fdis.total_pounds), 'N0') as Jan_2024_EOM_Pounds 
,FORMAT(SUM(fdis.total_cost), 'N0') as Jan_2024_EOM_Value
from gold.fact_daily_inventory_sum fdis
left join gold.dim_calendar dc on dc.date = fdis.report_date
left join gold.dim_branches db on db.branch_id = fdis.branch_id
where 1 = 1
and dc.fiscal_period = '2024-01'
and dc.fiscal_day = 19
and db.operating_unit_code IN ('EEP', 'ECI')
group by db.branch_name_short
order by branch_name_short asc 

----------------------------------------------------

select dc.fiscal_period, MAX(dc.date) as max_date
from gold.dim_calendar dc
where dc.fiscal_year >= 2024
group by dc.fiscal_period
order by dc.fiscal_period asc