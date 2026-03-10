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
order by branch_name_short asc ;

----------------------------------------------------

select dc.fiscal_period, MAX(dc.date) as max_date
from gold.dim_calendar dc
where dc.fiscal_year >= 2024
group by dc.fiscal_period
order by dc.fiscal_period asc

----------------------------------------------------

select * from gold.dim_calendar
WHERE fiscal_period_roll = 'Current'
order by date asc

----------------------------------------------------

select order_line_cmb, actual_ship_date, line_promise_date, ship_quantity, first_ship_quantity, otif_stp_test, otif_fill_test, otif_flag, otif_ship_lines from gold.fact_order_ship_detail
where order_line_cmb in  ('6288895.02','6274618.02', '6255383.01')
order by order_line_cmb ASC

SELECT * from gold.fact_order_ship_detail
WHERE actual_ship_date = '2026-03-09'

select distinct branch_name_short, branch_group from gold.dim_branches
order by branch_name_short asc
