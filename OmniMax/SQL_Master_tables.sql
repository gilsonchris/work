--MASTER COLLECTION OF GOLD TABLES in views I understand

--- Branches ---
select source, branch_id, branch_code, branch_name, branch_name_short, operating_unit_name, operating_unit_code, operating_unit_id, address1, address2, city, state, country, zip 
from gold.dim_branches
order by branch_name asc




--- Calendar (all)
select * from gold.dim_calendar
where [date] >= '2025-08-01'



--- Customers ---
SELECT site_use_city, customer_key, customer_rollup_name, category_code, active_status, primary_salesrep_id, company, country, credit_limit, credit_rating, cust_orig_reference, operating_unit_name, party_number, primary_flag, site_addr_attribute_category, site_addr_attribute1, site_addr_attribute2, site_addr_attribute3, site_addr_attribute4, site_addr_attribute5, site_addr_attribute6, site_addr_attribute7, site_addr_attribute9, site_addr_attribute10, site_addr_attribute11, site_addr_attribute12, site_use_addr1, site_use_addr2, site_use_addr3, site_use_addr4, site_use_buy_office, site_use_city, site_use_code, site_use_county, site_use_cust_id, site_use_cust_market, site_use_cust_name, site_use_cust_num, site_use_customer_class, site_use_id, site_use_inside_salesrep_name, site_use_location_id, site_use_market, site_use_orig_sys_addr_ref, site_use_orig_sys_ref, site_use_party_name, site_use_postal_code, site_use_price_list, site_use_price_list_name, site_use_salesrep_name, site_use_site_number, site_use_state, site_use_store_number, site_use_territory_manager, source, terms_code, terms_desc, region,  cust_attribute_category, cust_attribute1, cust_attribute2, cust_attribute3, cust_attribute4, cust_attribute5, site_use_create_date, account_status, last_update_date
FROM gold.dim_customers
WHERE 1 = 1
  --AND customer_rollup_name COLLATE Latin1_General_CI_AS LIKE '%Lowe%'   --case insensitive, accent sensitive
    AND site_use_postal_code = '28712'
	AND customer_rollup_name is not null
ORDER BY credit_limit DESC, customer_rollup_name ASC



---Items
select top (100) source, item_key, item_description, sales_family, sales_class, inventory_family, inventory_class, purchasing_category, branch_id, branch_name, commodity, item_status,length, width, height, dimension_uom_code, primary_uom_code, item_id, item_number, bom_item_type, pick_components_flag, replenish_to_order_flag, auto_created_config_flag, stock_enabled_flag, item_type, inv_planning_code, planner_code, planning_make_buy_code, mrp_planning_code, item_revision, upc_code, quantity_per_box, metal_weight_per_piece, nominal_guage, alloy, finish, temper, top_color_code, top_coat_primer, bottom_color_code, item_type_attr, bottom_coat_primer, perf_pattern, picking_order, ac_buy, shade_code, attribute13, [non-warranty], invoice_uom, rebate_category, pricing_family, pricing_class, pricing_subclass, fab_pricing_family, fab_pricing_class, safety_stock, preprocessing_lead_time, processing_lead_time, postprocessing_lead_time, fixed_lot_multiplier, creation_date, rise_flag, npd_flag, npd_category, lead_time, matl_pallet, npd_startdate, npd_enddate
from [gold].[dim_items]



---Order Reasons
select top (10) order_line_id, header_org_id, line_org_id, order_number, order_line_number, old_sch_ship_date, new_sch_ship_date, sch_ship_last_chg_date, sch_ship_dt_change_comments, sch_ship_dt_reason_desc, sch_ship_dt_reason_cat, old_request_date, new_request_date, request_last_chg_date, reqdt_change_comments, reqdt_reason_descr, reqdt_reason_cat, old_promise_date, new_promise_date, promise_last_chg_date, prodt_change_comments, prodt_reason_descr, prodt_reason_cat, cancel_reason_code1, cancel_reason_desc1, cancel_reason_code2, cancel_reason_desc2, cancel_reason_code3, cancel_reason_desc3, cancel_reason_code4, cancel_reason_desc4
from [gold].[fact_order_reasons]


--- Salesperson ---
SELECT s.[salesrep_id],s.[salesrep_name], s.[source]   ,s.[emp_id]      ,s.[creation_date]      ,s.[start_date_active]      ,s.[end_date_active]      ,s.[last_update_date]      ,s.[resource_id]
      ,SUM(o.backlog_amount_usd) as backlog_amount_usd_ex
FROM [gold].[dim_salesperson] s
LEFT JOIN gold.fact_sales_orders o
    ON s.salesrep_id = o.salesrep_original
    AND o.backlog_amount_usd IS NOT NULL
GROUP BY s.[salesrep_id], s.[salesrep_name], s.[source], s.[emp_id], 
         s.[creation_date], s.[start_date_active], s.[end_date_active], 
         s.[last_update_date], s.[resource_id]
ORDER BY backlog_amount_usd_ex DESC


--- AP Checks ---
select * from gold.fact_ap_checks
where 1= 1 
and [vendor_name] like '%MAX RESI%'  --1068087
and check_date >=  '2025-1-01' and check_date <= '2025-08-31'
order by check_date asc

---Sales Orders
select top (10) header_booked_date, line_promise_date, line_schedule_ship_date, branch_id as branch_order_id, line_ship_branch_id as branch_ship_id,  bill_to_key as customer_bill_to, ship_to_key as customer_ship_to, salesrep_original as salesperson_order, item_key, order_line_id, order_line_number, order_number, backlog_amount_usd, gross_material_margin_usd, gross_sales_usd, header_status, backlog_cost_usd, make_buy, metal_weight_per_piece, order_pounds, order_quantity, order_uom, primary_uom, ordered_date, standard_cost_amount_usd, total_charges, unit_selling_price, unit_std_cost, usd_to_cad_conv, market, market_group, int_ext, territory_manager, add_cust_comments, bill_to_customer_number, bill_to_market, bill_to_party_name, bill_to_site_loc_id, bill_to_site_use_id, cancel_reason_code1, cancel_reason_code2, cancel_reason_code3, cancel_reason_code4, cancel_reason_desc1, cancel_reason_desc2, cancel_reason_desc3, cancel_reason_desc4, cancelled_quantity, change_date, change_reason, creation_date, cust_job_name, customer_item_number, customer_job_name, customer_po_number, deliver_to_key, edi_price, fiscal_period, fiscal_quarter, fiscal_year, fob_point_code, freight_carrier_code, hold_code, inside_sales_rep, item_cost_key, item_id, item_number, line_request_date, line_ship_priority_code, line_status, old_line_schedule_ship_date, order_branch_name, order_ship_priority_code, order_source, order_type, orig_currency_code, party_cust_number, project_type, request_date, revenue_charges, ship_from_branch_name, ship_to_cust_number, ship_to_site_loc_id, ship_to_site_number, source
from [gold].[fact_sales_orders]
where ship_to_key IN ('D-34671-73199','S-34671-83703','S-34671-187249') --Brevard Lowe's
order by header_booked_date desc




---Sales Orders
select * from [gold].[fact_sales_orders]
where order_number = 1015090
order by header_booked_date desc

--row count
SELECT COUNT(*) AS Row_Count
FROM [gold].[fact_sales_orders];

--column count
SELECT COUNT(*) AS ColumnCount
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'gold'
  AND TABLE_NAME = 'fact_sales_orders';

 ---Sales Summary
select * from [gold].[fact_sales_summary]
where 1 = 1
and market = 'Retail'
and plan_top_customer = 'All Other'
and fiscal_period = '2025-11'
order by fiscal_period_date desc


--- Calendar (all)
select * from gold.dim_calendar
where curr_period_flag = 1
order by date desc

select *from  [gold].[fact_sales_summary]

select distinct amount_type from  [gold].[fact_sales_summary]


--- Calendar (arranged view)
 SELECT[date],[current_date],[curr_fiscal_year],[curr_fiscal_period],[curr_fiscal_month_num],[curr_fiscal_day],[holiday],[mtd_flag],[ytd_flag],[fiscal_month_num],[fiscal_year],[fiscal_period],[fiscal_days_in_period],[fiscal_week_flag],[fiscal_month_short],[fiscal_qtr],[fiscal_day],[period_startdate],[period_enddate],[year_startdate],[year_enddate],[prior_period_startdate],[prior_period_enddate],[prior_year_startdate],[prior_year_enddate],[curr_period_flag],[curr_day_flag],[fiscal_date],[fiscal_year_qtr],[fiscal_year_mon],[fiscal_year_mon_day],[fiscal_year_qtr_idx],[fiscal_year_mon_idx],[fiscal_year_mon_day_idx],[fiscal_week_of_period],[curr_year_flag],[curr_period_flag_desc],[fisc_year_offset],[end_of_week],[end_of_month],[fiscal_cal_date],[fiscal_cal_date_roll],[fisc_month_offset],[fisc_day_offset]
 FROM [gold].[dim_calendar]
 where curr_period_flag = 1
order by date desc

---Sales Orders
select header_booked_date, line_promise_date, branch_id, aging_desc, cpu_ship, int_ext, backlog_amount_usd, order_number, order_line_number, order_line_cmb, order_type
--select sum(backlog_amount_usd)
from [gold].[fact_sales_orders]
where 1=1  
and branch_id = 242
and aging_desc = 'On Time'
and cpu_ship = 'Ship'
and int_ext = 'EXT'
and header_status = 'BOOKED'
and backlog_amount_usd <> 0 
and line_promise_date = '12-09-25'
order by header_booked_date desc

select *from  [gold].[fact_sales_summary]
order by fiscal_period_date desc


--- Calendar (arranged view)
 SELECT[date],[current_date],[curr_period_flag], [curr_fiscal_year],[curr_fiscal_period],[curr_fiscal_month_num],[curr_fiscal_day],[holiday],[mtd_flag],[ytd_flag],[fiscal_month_num],[fiscal_year],[fiscal_period],[fiscal_days_in_period],[fiscal_week_flag],[fiscal_month_short],[fiscal_qtr],[fiscal_day],[period_startdate],[period_enddate],[year_startdate],[year_enddate],[prior_period_startdate],[prior_period_enddate],[prior_year_startdate],[prior_year_enddate],[curr_period_flag],[curr_day_flag],[fiscal_date],[fiscal_year_qtr],[fiscal_year_mon],[fiscal_year_mon_day],[fiscal_year_qtr_idx],[fiscal_year_mon_idx],[fiscal_year_mon_day_idx],[fiscal_week_of_period],[curr_year_flag],[curr_period_flag_desc],[fisc_year_offset],[end_of_week],[end_of_month],[fiscal_cal_date],[fiscal_cal_date_roll],[fisc_month_offset],[fisc_day_offset]
 FROM [gold].[dim_calendar]
 where curr_period_flag = 1
order by date desc



---Sales Summary
select * from [gold].[fact_sales_summary]
where 1 = 1
and market = 'Retail'
and plan_top_customer = 'All Other'
and inventory_family = 'ALUM'
and fiscal_period like '%12'
and amount_type = 'Gross Sales'
and plan_branch_id = 'A/O'
order by fiscal_period_date desc

---Sales Summary
select * from [gold].[fact_sales_summary]
order by fiscal_period_date asc


---Sales Summary
select SUM(current_day) AS total_NO_deductions from [gold].[fact_sales_summary]
where 1 = 1
and market = 'Retail'
and fiscal_period_date = '2026-01-01'
and amount_type IN  ('Gross Sales')
and inventory_family = 'ALUM'


SELECT 
    fiscal_period_date,
    plan_top_customer,
    amount_type,
    SUM(current_day) AS total_sales
FROM [gold].[fact_sales_summary]
WHERE market = 'Retail'
  AND fiscal_period_date = '2026-01-01'
  AND amount_type IN ('Gross Sales', 'Est Deductions')
  AND inventory_family = 'ALUM'
GROUP BY 
    fiscal_period_date, 
    plan_top_customer, 
    amount_type
ORDER BY 
    fiscal_period_date DESC, 
    plan_top_customer DESC, 
    amount_type DESC;

SELECT 
    c.fiscal_year_mon,
    SUM(t.trx_value) AS Total_Consignment_Value
FROM [gold].[fact_inventory_transactions] t
JOIN [gold].[dim_calendar] c ON t.trx_date = c.[date]
WHERE t.transaction_type = 'Consignment Receipt'
GROUP BY c.fiscal_year_mon
ORDER BY c.fiscal_year_mon DESC;


-- Sales Summary Estimated Net Sales
select
	 SUM(current_day) as Day_Sales
	,SUM(current_year) as MTD_Sales
	,SUM(prior_year) as Prior_year
from  [gold].[fact_sales_summary]
where 1 = 1
and fiscal_period = '2026-01'
and amount_type in ('Gross Sales', 'Est Deductions')

select count(*) as row_count
from gold.fact_consignment as f
left join gold.dim_items as di on di.item_key = f.item_key
where di.item_key IS NULL


--Consignmet Summary validatio
select sum(fc.received_pounds) from gold.fact_consignment fc
left join gold.dim_calendar dc on fc.transaction_date = dc.date
left join gold.dim_branches db on db.branch_id = fc.branch_id
where 1 =1 
and fc.transaction_type_name = 'Subinventory Transfer' 
and fc.subinventory_code = 'DUF'
and db.branch_name_short = 'C14| WACO'
and dc.curr_period_flag = 1


select distinct fiscal_period, fiscal_days_in_period from gold.dim_calendar
where fiscal_period >= '2024-01'
order by fiscal_period asc

select SUM(total_cost) from gold.fact_daily_inventory_sum
where report_date = '2026-01-21'



--- Calendar (trimmed)
select [date] as calendar_date, fiscal_period, fiscal_year, fiscal_qtr, fiscal_month_num, fiscal_day, fiscal_days_in_period
      ,fiscal_date, fiscal_year_qtr, fiscal_year_mon, fiscal_year_mon_day, fiscal_year_qtr_idx, fiscal_year_mon_idx, fiscal_year_mon_day_idx
from gold.dim_calendar
where date >= '2024-01-01'
order by calendar_date asc


select  fiscal_period, max(date) as calendar_date, MAX(fiscal_date) as max_fiscal_date from gold.dim_calendar
where date >= '2024-01-01'
group by fiscal_period
order by fiscal_period asc

SELECT * from gold.dim_branches
where branch_id = 242
