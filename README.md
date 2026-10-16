# Revenue Pulse: build a revenue dashboard with Snowflake Workspaces and CoWork

Companion code for the Snowflake developer guide *Build a Revenue Dashboard with Snowflake Workspaces and CoWork*. You build a native Workspaces dashboard on a revenue semantic view, publish it to a sales-ops role as an artifact, and ask follow-up "why" questions in Snowflake CoWork. All data is synthetic.

Everything runs in Snowsight. You don't need Python, a CLI, or a local clone.

## Run

1. In Snowsight, open **Projects > Workspaces**, create a SQL file in **My Workspace**, and set the role to `ACCOUNTADMIN` and the warehouse to `COMPUTE_WH`.
2. Paste and run [`sql/00_bootstrap.sql`](sql/00_bootstrap.sql). It creates `REVENUE_PULSE_DB`, an API integration, and a Git repository object over this repo.
3. Run the remaining scripts straight from the repository:

```sql
EXECUTE IMMEDIATE FROM @REVENUE_PULSE_DB.DASHBOARD_DEMO.REVENUE_PULSE_REPO/branches/main/sql/01_setup.sql;
EXECUTE IMMEDIATE FROM @REVENUE_PULSE_DB.DASHBOARD_DEMO.REVENUE_PULSE_REPO/branches/main/sql/02_semantic_view.sql;
EXECUTE IMMEDIATE FROM @REVENUE_PULSE_DB.DASHBOARD_DEMO.REVENUE_PULSE_REPO/branches/main/sql/03_agent.sql;
EXECUTE IMMEDIATE FROM @REVENUE_PULSE_DB.DASHBOARD_DEMO.REVENUE_PULSE_REPO/branches/main/sql/04_viewer_role.sql;
```

4. In **Workspaces**, select **+ > Git workspace**, paste this repo's URL, choose the `REVENUE_PULSE_GIT_API` integration (the dialog may preselect another one) and **Public repository**, then open `dashboards/revenue_pulse.dash` and set its warehouse to `COMPUTE_WH`.
5. Choose **Share > Publish as artifact** with the `DASHBOARD_DEMO_SALES_OPS` role. See the guide for the full walkthrough.

If your warehouse isn't `COMPUTE_WH`, replace it in `sql/03_agent.sql` and `sql/04_viewer_role.sql` in your own copy of the files before running them.

## Layout

```
sql/00_bootstrap.sql         database, API integration, Git repository object
sql/01_setup.sql             tables, stage, and data load from data/
sql/02_semantic_view.sql     semantic view
sql/03_agent.sql             Revenue Advisor Cortex agent
sql/04_viewer_role.sql       least-privilege viewer role
sql/99_cleanup.sql           teardown; never run automatically
data/                        committed synthetic CSVs and expected_results.json
dashboards/revenue_pulse.dash  the native Workspaces dashboard
docs/demo-script.md          five-minute walkthrough
```

Maintainer only (not needed to follow the guide): `scripts/generate_data.py` and `scripts/build_dashboard.py` regenerate `data/` and `dashboards/` from `config/demo.json`, and `tests/test_data.py` tests the generator.

## Clean up

Remove every role from the dashboard's **Share** dialog, delete the artifact in CoWork, and delete the Git workspace (**...** next to its name > **Delete**). Then run `sql/99_cleanup.sql`, which drops `REVENUE_PULSE_DB`, the viewer role, and the API integration.
