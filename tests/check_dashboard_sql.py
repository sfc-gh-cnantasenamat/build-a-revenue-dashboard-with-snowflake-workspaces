"""Run every .dash datasource against your account with concrete filter values and reconcile key numbers."""

import json
import re
import sys
from pathlib import Path

import snowflake.connector

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/demo.json").read_text())
DASH = json.loads((ROOT / "dashboards/revenue_pulse.dash").read_text())
TRUTH = json.loads((ROOT / "data/expected_results.json").read_text())

SCENARIOS = {
    "default_q3": {"MONTH": "MONTH BETWEEN '2026-07-01' AND '2026-09-01'"},
    "emea_enterprise_q3": {"MONTH": "MONTH BETWEEN '2026-07-01' AND '2026-09-01'",
                           "REGION": "REGION IN ('EMEA')", "SEGMENT": "SEGMENT IN ('Enterprise')"},
    "empty": {"MONTH": "MONTH BETWEEN '2030-01-01' AND '2030-03-01'"},
}


def render(sql, predicates):
    return re.sub(r"\{\{\s*filter\('(\w+)'\)\s*\}\}", lambda m: predicates.get(m.group(1), "TRUE"), sql)


def close(actual, expected, tolerance=0.01):
    return actual is not None and abs(float(actual) - expected) <= tolerance


def main():
    failures = []
    with snowflake.connector.connect(connection_name=CONFIG["connection"]) as connection:
        cursor = connection.cursor(snowflake.connector.DictCursor)
        account = cursor.execute("SELECT CURRENT_ACCOUNT_NAME() AS A").fetchone()["A"]
        assert account == CONFIG["expected_account"], account
        cursor.execute(f'USE WAREHOUSE {CONFIG["warehouse"]}')
        results = {}
        for scenario, predicates in SCENARIOS.items():
            for name, ds in DASH["datasources"].items():
                rows = cursor.execute(render(ds["sql"], predicates)).fetchall()
                declared = [c["name"] for c in ds["columns"]]
                if rows and list(rows[0]) != declared:
                    failures.append(f"{scenario}/{name}: columns {list(rows[0])} != {declared}")
                results[(scenario, name)] = rows
                print(f"{scenario:20} {name:22} {len(rows):3} rows")

    q3, py = TRUTH["current"], TRUTH["prior_year"]
    emea = TRUTH["region_segments"][0]
    checks = [
        ("Q3 net revenue", results[("default_q3", "ds-kpi-net-revenue")][0]["CURRENT_VALUE"], q3["net_revenue_cents"] / 100),
        ("PY net revenue", results[("default_q3", "ds-kpi-net-revenue")][0]["PRIOR_VALUE"], py["net_revenue_cents"] / 100),
        ("Q3 attainment %", results[("default_q3", "ds-kpi-attainment")][0]["CURRENT_VALUE"], 100 * q3["attainment"]),
        ("Q3 variance", results[("default_q3", "ds-kpi-variance")][0]["CURRENT_VALUE"], q3["variance_cents"] / 100),
        ("Q3 margin %", results[("default_q3", "ds-kpi-margin")][0]["CURRENT_VALUE"], 100 * q3["gross_margin"]),
        ("EMEA Ent variance", results[("emea_enterprise_q3", "ds-kpi-variance")][0]["CURRENT_VALUE"], emea["variance_cents"] / 100),
        ("Region variances sum", sum(float(r["VARIANCE"]) for r in results[("default_q3", "ds-by-region")]), q3["variance_cents"] / 100),
        ("Driver variances sum", sum(float(r["VARIANCE"]) for r in results[("default_q3", "ds-drivers")]), q3["variance_cents"] / 100),
        ("Account variances sum (EMEA Ent)", sum(float(r["VARIANCE"]) for r in results[("emea_enterprise_q3", "ds-accounts")]),
         emea["variance_cents"] / 100),
    ]
    for label, actual, expected in checks:
        tolerance = 6 if label.startswith("Account") else 0.01  # account table rounds each row to whole dollars
        status = "PASS" if close(actual, expected, tolerance) else "FAIL"
        print(f"{status} {label}: {actual} vs {expected:.2f}")
        if status == "FAIL":
            failures.append(label)
    if len(results[("default_q3", "ds-trend")]) != CONFIG["months"]:
        failures.append("trend should cover all months regardless of period filter")
    empty_kpi = results[("empty", "ds-kpi-attainment")]
    if empty_kpi and empty_kpi[0]["CURRENT_VALUE"] is not None:
        failures.append("empty period should yield null attainment, not zero")
    print("ALL CHECKS PASSED" if not failures else f"FAILURES: {failures}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
