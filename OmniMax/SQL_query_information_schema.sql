--- column characteristics and data types
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'gold'
  AND TABLE_NAME = 'fact_sales_orders'   --dim_customers --'dim_calendar'
  order by COLUMN_NAME ASC


---alphabetical column names
SELECT 
    ',[' + COLUMN_NAME + ']'
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'gold' 
  AND TABLE_NAME = 'fact_sales_orders'
ORDER BY COLUMN_NAME
--delete first comman when pasting



---search for table names
SELECT * FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE '%items%'
