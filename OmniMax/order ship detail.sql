
-- Query to investigate 34 orders in PBI but not SAS
-- Generated from comparison results

SELECT db.branch_name_short
    , fosd.actual_ship_date
    , fosd.line_promise_date
    , fosd.line_request_date
    , fosd.ship_line_count
    , fosd.company
    , fosd.cpu
    , fosd.market
    , fosd.order_quantity
    , fosd.ship_quantity
    , fosd.first_ship_date
    , fosd.first_ship_quantity
    , fosd.int_ext
    , fosd.line_status
    , fosd.* 
FROM gold.fact_order_ship_detail fosd
LEFT JOIN gold.dim_branches db ON db.branch_id = fosd.ship_branch_id
WHERE 
1= 1
and branch_name_short = 'C03| CLEVELAND'
and order_line_cmb IN (
    '6290220.50',
    '6296154.50',
    '6296248.50',
    '6296378.50',
    '6296382.50',
    '6296598.50',
    '6296616.50',
    '6296618.50',
    '6296619.50',
    '6296620.50',
    '6297312.50',
    '6297330.50',
    '6297387.50',
    '6297852.50',
    '6297853.50',
    '6297927.50',
    '6297953.50',
    '6297960.50',
    '6298312.50',
    '6298331.50',
    '6299747.50',
    '6299761.50',
    '6299988.50',
    '6300748.50',
    '6301616.50',
    '6302068.50',
    '6302260.50',
    '6302362.50',
    '6302384.50',
    '6302462.50',
    '6302512.50',
    '6302514.50',
    '6302839.50',
    '6303081.50'
);



SELECT db.branch_name_short
    , fosd.order_number
    , fosd.order_line_number
    , fosd.order_line_cmb
    , fosd.actual_ship_date
    , fosd.line_promise_date
    , fosd.line_request_date
    , fosd.ship_line_count
    , fosd.company
    , fosd.cpu
    , fosd.market
    , fosd.order_quantity
    , fosd.ship_quantity
    , fosd.first_ship_date
    , fosd.first_ship_quantity
    , fosd.int_ext
    , fosd.line_status
    , fosd.* 
FROM gold.fact_order_ship_detail fosd
LEFT JOIN gold.dim_branches db ON db.branch_id = fosd.ship_branch_id
WHERE 1=1
and order_line_cmb = '6296378.50'


SELECT db.branch_name_short
    , fosd.order_number
    , fosd.order_line_number
    , fosd.order_line_cmb
    , fosd.actual_ship_date
    , fosd.*
FROM gold.fact_order_ship_detail fosd
LEFT JOIN gold.dim_branches db ON db.branch_id = fosd.ship_branch_id
WHERE 1=1
and order_line_cmb = '6244026.13'



select sum(fosd.gross_sales_usd) as total_gross_sales
-- db.branch_name_short, fosd.* 
from gold.fact_sales_orders fosd
left join gold.dim_branches db on db.branch_id = fosd.branch_id
left join gold.dim_calendar dc on dc.date = fosd.header_booked_date
where 
1=1
and dc.fiscal_period = '2026-03'--    eader_booked_date = '2026-03-06'
and db.branch_name_short = 'C01| LANCASTER'
group by db.branch_name_short


