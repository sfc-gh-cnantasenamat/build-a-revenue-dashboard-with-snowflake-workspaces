CREATE OR REPLACE SEMANTIC VIEW REVENUE_PULSE_DB.DASHBOARD_DEMO.REVENUE_SEMANTIC_VIEW
  TABLES (
    revenue AS REVENUE_PULSE_DB.DASHBOARD_DEMO.REVENUE_MONTHLY PRIMARY KEY (REVENUE_ID)
      COMMENT = 'Monthly revenue, target, and cost per customer and product. Synthetic.',
    customers AS REVENUE_PULSE_DB.DASHBOARD_DEMO.CUSTOMERS PRIMARY KEY (CUSTOMER_ID)
      WITH SYNONYMS = ('accounts', 'clients') COMMENT = 'Customer accounts with sales region and segment',
    products AS REVENUE_PULSE_DB.DASHBOARD_DEMO.PRODUCTS PRIMARY KEY (PRODUCT_ID)
      WITH SYNONYMS = ('product lines') COMMENT = 'Product lines'
  )
  RELATIONSHIPS (
    revenue_to_customers AS revenue (CUSTOMER_ID) REFERENCES customers,
    revenue_to_products AS revenue (PRODUCT_ID) REFERENCES products
  )
  FACTS (
    revenue.gross_revenue_usd AS GROSS_REVENUE_CENTS / 100 COMMENT = 'List revenue before discounts and refunds, USD',
    revenue.discount_usd AS DISCOUNT_CENTS / 100 COMMENT = 'Discounts granted, USD',
    revenue.refund_usd AS REFUND_CENTS / 100 COMMENT = 'Refunds and service credits, USD',
    revenue.cost_usd AS COST_CENTS / 100 COMMENT = 'Cost of revenue, USD',
    revenue.target_usd AS TARGET_CENTS / 100 COMMENT = 'Revenue target, USD',
    revenue.net_revenue_usd AS (GROSS_REVENUE_CENTS - DISCOUNT_CENTS - REFUND_CENTS) / 100
      COMMENT = 'Gross revenue minus discounts and refunds, USD'
  )
  DIMENSIONS (
    revenue.month AS MONTH WITH SYNONYMS = ('period', 'date') COMMENT = 'First day of the revenue month',
    revenue.quarter AS DATE_TRUNC('QUARTER', MONTH) COMMENT = 'First day of the calendar quarter',
    revenue.year AS YEAR(MONTH) COMMENT = 'Calendar year',
    revenue.recorded_driver AS RECORDED_DRIVER
      COMMENT = 'Driver recorded by sales ops: NORMAL_TRADING, RECORDED_CONTRACT_DOWNSIZE, RECORDED_DISCOUNT_AND_SERVICE_CREDIT, RECORDED_RENEWAL_DELAY',
    customers.customer_id AS CUSTOMER_ID COMMENT = 'Customer identifier',
    customers.customer_name AS CUSTOMER_NAME WITH SYNONYMS = ('account name') COMMENT = 'Customer account name',
    customers.region AS REGION WITH SYNONYMS = ('geo', 'territory') COMMENT = 'Sales region: Americas, EMEA, APAC',
    customers.segment AS SEGMENT COMMENT = 'Customer segment: Enterprise, Mid-market, SMB',
    products.product_name AS PRODUCT_NAME WITH SYNONYMS = ('product') COMMENT = 'Product line name'
  )
  METRICS (
    revenue.net_revenue AS SUM(revenue.net_revenue_usd) WITH SYNONYMS = ('revenue', 'sales')
      COMMENT = 'Net revenue in USD: gross minus discounts and refunds',
    revenue.gross_revenue AS SUM(revenue.gross_revenue_usd) COMMENT = 'Gross revenue in USD',
    revenue.total_discounts AS SUM(revenue.discount_usd) COMMENT = 'Total discounts in USD',
    revenue.total_refunds AS SUM(revenue.refund_usd) COMMENT = 'Total refunds and service credits in USD',
    revenue.revenue_target AS SUM(revenue.target_usd) WITH SYNONYMS = ('quota', 'plan')
      COMMENT = 'Revenue target in USD',
    revenue.target_variance AS SUM(revenue.net_revenue_usd) - SUM(revenue.target_usd)
      WITH SYNONYMS = ('gap', 'shortfall') COMMENT = 'Net revenue minus target in USD; negative means behind target',
    revenue.target_attainment AS DIV0NULL(SUM(revenue.net_revenue_usd), SUM(revenue.target_usd))
      COMMENT = 'Net revenue divided by target, as a ratio (0.92 = 92%)',
    revenue.gross_profit AS SUM(revenue.net_revenue_usd) - SUM(revenue.cost_usd) COMMENT = 'Net revenue minus cost in USD',
    revenue.gross_margin AS DIV0NULL(SUM(revenue.net_revenue_usd) - SUM(revenue.cost_usd), SUM(revenue.net_revenue_usd))
      COMMENT = 'Gross profit divided by net revenue, as a ratio; null when net revenue is zero'
  )
  COMMENT = 'Revenue Pulse: synthetic B2B revenue vs target by month, region, segment, account, and product. Data through 2026-09-30.'
  AI_SQL_GENERATION 'Data is monthly and complete through September 2026. Last quarter or Q3 means months 2026-07-01 through 2026-09-01. Ratios are 0-1; present as percentages. Year-over-year compares the same months one year earlier.';
