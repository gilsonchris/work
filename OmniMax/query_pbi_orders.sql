-- Query to investigate 34 orders in PBI but not in SAS
-- Generated from: C:\Users\Chris Gilson\OneDrive\Documents\Dupuis Analytics\OmniMax\SAS vs PBI_result.xlsx

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
WHERE order_line_cmb IN (
    '6290220.5',
    '6296154.5',
    '6296248.5',
    '6296378.5',
    '6296382.5',
    '6296598.5',
    '6296616.5',
    '6296618.5',
    '6296619.5',
    '6296620.5',
    '6297312.5',
    '6297330.5',
    '6297387.5',
    '6297852.5',
    '6297853.5',
    '6297927.5',
    '6297953.5',
    '6297960.5',
    '6298312.5',
    '6298331.5',
    '6299747.5',
    '6299761.5',
    '6299988.5',
    '6300748.5',
    '6301616.5',
    '6302068.5',
    '6302260.5',
    '6302362.5',
    '6302384.5',
    '6302462.5',
    '6302512.5',
    '6302514.5',
    '6302839.5',
    '6303081.5'
);
