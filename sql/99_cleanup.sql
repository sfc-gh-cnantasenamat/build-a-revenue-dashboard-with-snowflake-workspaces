-- Teardown for the Revenue Pulse guide. NOT run by any script; run it yourself at the end.
-- First remove the published artifact from the dashboard's Share > Publish as artifact dialog (or CoWork).
-- Every guide object (schema, tables, stage, semantic view, agent) lives in REVENUE_PULSE_DB,
-- so dropping the database removes them all. The role and workspace file live outside it.
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS REVENUE_PULSE_DB;
DROP ROLE IF EXISTS DASHBOARD_DEMO_SALES_OPS;
-- Workspace file: cortex ws rm 'USER$.PUBLIC.DEFAULT$:/revenue_pulse/revenue_pulse.dash' --connection <your_connection>
