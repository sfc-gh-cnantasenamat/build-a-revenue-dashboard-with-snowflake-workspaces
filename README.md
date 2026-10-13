# Revenue Pulse: build a revenue dashboard with Snowflake Workspaces and CoWork

Companion code for the Snowflake developer guide *Build a Revenue Dashboard with Snowflake Workspaces and CoWork*. You build a native Workspaces dashboard on a revenue semantic view, publish it to a sales-ops role, and ask follow-up "why" questions in Snowflake CoWork. All data is synthetic.

## Configure

Edit `config/demo.json`: set `connection`, `expected_organization`, `expected_account`, `database`, and `warehouse`. The SQL files and agent specs use `REVENUE_PULSE_DB` and `COMPUTE_WH`; replace them if your names differ. `sql/01_setup.sql` creates the dedicated `REVENUE_PULSE_DB` database, which holds every guide object.

## Run

```bash
python3 scripts/generate_data.py
python3 -m unittest discover -s tests -v
python3 scripts/deploy.py
cortex agent-studio agent-deploy --file-path REVENUE_ADVISOR.agent.yaml \
  --fqn REVENUE_PULSE_DB.DASHBOARD_DEMO.REVENUE_ADVISOR --connection <your_connection>
python3 scripts/build_dashboard.py
python3 tests/check_dashboard_sql.py
cortex ws cp dashboards/revenue_pulse.dash 'USER$.PUBLIC.DEFAULT$:/revenue_pulse/' --connection <your_connection>
```

Then run `sql/03_viewer_role.sql`, open the dashboard in Workspaces, and choose **Share > Publish as artifact** with the `DASHBOARD_DEMO_SALES_OPS` role. See the guide for the full walkthrough.

## Layout

```
config/demo.json             account, names, seed, dates
scripts/generate_data.py     deterministic data generator (integer cents)
scripts/deploy.py            creates objects and loads CSVs; refuses unexpected accounts
scripts/build_dashboard.py   generates dashboards/revenue_pulse.dash
sql/01_setup.sql             schema, tables, stage (IF NOT EXISTS)
sql/02_semantic_view.sql     semantic view
sql/03_viewer_role.sql       least-privilege viewer role
sql/99_cleanup.sql           teardown (drop database and role); never run automatically
cortex_project/              agent spec and project file for agent-deploy
tests/test_data.py           data generator unit tests
tests/check_dashboard_sql.py runs every dashboard query and reconciles totals
docs/demo-script.md          five-minute walkthrough
```

## Clean up

Remove the published artifact first, then run `sql/99_cleanup.sql`. It drops `REVENUE_PULSE_DB`, which removes the schema, tables, stage, semantic view, and agent. It also drops the viewer role. Remove the workspace file with the `cortex ws rm` command noted in that file.
