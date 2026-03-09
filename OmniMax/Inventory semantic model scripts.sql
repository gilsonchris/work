---		Calendar (arranged view)	---
 SELECT[date],[current_date],[curr_period_flag], [curr_fiscal_year],[curr_fiscal_period],[curr_fiscal_month_num],[curr_fiscal_day],[holiday],[mtd_flag],[ytd_flag],[fiscal_month_num],[fiscal_year],[fiscal_period],[fiscal_days_in_period],[fiscal_week_flag],[fiscal_month_short],[fiscal_qtr],[fiscal_day],[period_startdate],[period_enddate],[year_startdate],[year_enddate],[prior_period_startdate],[prior_period_enddate],[prior_year_startdate],[prior_year_enddate],[curr_period_flag],[curr_day_flag],[fiscal_date],[fiscal_year_qtr],[fiscal_year_mon],[fiscal_year_mon_day],[fiscal_year_qtr_idx],[fiscal_year_mon_idx],[fiscal_year_mon_day_idx],[fiscal_week_of_period],[curr_year_flag],[curr_period_flag_desc],[fisc_year_offset],[end_of_week],[end_of_month],[fiscal_cal_date],[fiscal_cal_date_roll],[fisc_month_offset],[fisc_day_offset]
 FROM [gold].[dim_calendar]
 where curr_period_flag = 1
order by date desc

---   Branches    ---
select source, branch_id, branch_code, branch_name, branch_name_short, operating_unit_name, operating_unit_code, operating_unit_id, address1, address2, city, state, country, zip 
from gold.dim_branches
order by branch_name asc

---    Items	---
select * from [gold].[dim_items]
where item_status IN ('active')

---    On Hand	---
select * from  [gold].[fact_inventory_onhand]

--Lot Number = unique ID assigned to a specific batch of material (aluminum coil or a batch of screws)
--Subinventory Code = CONS: Consigned (Supplier-owned metal), hasn't been paid for. RAW: Raw Materials (OmniMax-owned coils). STAG: Staging area (Ready for production). FG: Finished Goods (Ready to ship).
--Locator_Code helps forklift drivers find exactly what they need
--Owning_TP_Type = Trading partner = who legally owns the inventory at this exact second. 1 = supplier/consigned, 2 = organization owned (OMX)

select distinct inventory_group from  [gold].[fact_inventory_onhand] --Coil, FG (finished goods), and RM (Raw materials)
select distinct ownership from  [gold].[fact_inventory_onhand] --Owned, Consigned

select distinct
	owning_tp_type, 
	ownership 
from  [gold].[fact_inventory_onhand] --Coil, FG (finished goods), and RM (Raw materials)


---Consigment
select * from gold.fact_consignment

select distinct late_future from gold.fact_consignment

select distinct consign_aging from gold.fact_consignment


---    On Hand	---
select * from  [gold].[fact_inventory_onhand]


---Daily Inventory Summary
select * from gold.fact_daily_inventory_sum
order by report_date asc

select distinct cost_group from gold.fact_daily_inventory_sum order by cost_group asc

select c.fiscal_period, f.inventory_branch , SUM(total_cost) as total_cost
from gold.fact_daily_inventory_sum f
join gold.dim_calendar c on f.report_date = c.date
WHERE c.fiscal_period = '2025-05'
group by c.fiscal_period, f.inventory_branch
order by c.fiscal_period desc


SELECT 
    c.fiscal_period 
    ,f.*
FROM gold.fact_daily_inventory_sum f
JOIN gold.dim_calendar c 
    ON f.report_date = c.date
WHERE c.fiscal_period = '2025-05'
ORDER BY f.total_cost ASC


--- Consignment Current Period PO Receipts Lancaster & TCH 
SELECT 
    SUM(f.transaction_pounds) AS Trx_Lbs_Lancaster_TCH_Current_Period
FROM gold.fact_consignment f
JOIN gold.dim_calendar c 
    ON f.transaction_date = c.date
WHERE f.branch_id = 242 
    AND f.subinventory_code = 'TCH' 
    AND c.curr_period_flag = 1 
    AND f.transaction_type_name = 'PO Receipt';



--- Lot Numbers with PO Receipt Transaction Pounds in SAS but not in Fabric
SELECT f.*
FROM gold.fact_consignment f
WHERE f.lot_number IN ('25J941248A','25J941248E','25J940878A','25J943729A','25J943779A','25J943779B','25J943779C','25J943779D')
AND f.transaction_type_name = 'PO Receipt'
ORDER BY 
    f.lot_number ASC,  f.transaction_date asc


--- Consignment Lot Detail for a specific lot, all transaction types
SELECT 
    f.*
FROM gold.fact_consignment f
WHERE f.lot_number = '25J941248A'
--AND f.transaction_type_name = 'PO Receipt'
ORDER BY 
    transaction_date asc;


	--- Lot Numbers with PO Receipt Transaction Pounds in SAS but not in Fabric
SELECT SUM(f.received_pounds)
FROM gold.fact_consignment f
WHERE f.lot_number IN ('25J941248A','25J941248E','25J940878A','25J943729A','25J943779A','25J943779B','25J943779C','25J943779D')
ORDER BY 
    f.lot_number ASC,  f.transaction_date asc


--- Consignment bucketing discrepency
SELECT * FROM gold.fact_consignment 
WHERE subinventory_code = 'TCH' ;

SELECT sum(transaction_pounds) as total_trx_lbs
FROM gold.fact_consignment 
WHERE subinventory_code = 'TCH'


