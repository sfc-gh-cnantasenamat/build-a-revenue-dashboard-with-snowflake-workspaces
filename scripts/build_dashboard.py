"""Build dashboards/revenue_pulse.dash (native Dashboards 2.0 spec v2)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/demo.json").read_text())
FQ = f'{CONFIG["database"]}.{CONFIG["schema"]}'
SV = f'{FQ}.{CONFIG["semantic_view"]}'
FILTERS = ("MONTH", "REGION", "SEGMENT", "PRODUCT_NAME")
NUM, TXT, DATE = "NUMBER", "VARCHAR", "DATE"


def base(extra_dims="", shift_year=False, metrics="revenue.net_revenue, revenue.revenue_target, "
         "revenue.gross_profit, revenue.total_discounts, revenue.total_refunds"):
    month = "DATEADD(YEAR, 1, MONTH) AS MONTH" if shift_year else "MONTH"
    return (f"SELECT {month}, * EXCLUDE (MONTH) FROM SEMANTIC_VIEW(\n        {SV}\n"
            f"        DIMENSIONS revenue.month, customers.region, customers.segment, products.product_name{extra_dims}\n"
            f"        METRICS {metrics})")


def where(ids=FILTERS):
    return "WHERE " + "\n    AND ".join(f"{{{{ filter('{i}') }}}}" for i in ids)


def datasource(sql, columns, ids=FILTERS):
    return {"type": "sql", "columns": [{"name": n, "type": t} for n, t in columns], "sql": sql,
            "filter_bindings": [{"filter_id": i} for i in ids]}


def scorecard(title, label, decimals=1, increases_better=True, compare=True):
    return {"title": title, "type": "chart", "spec": {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json", "data": {"name": "values"},
        "usermeta": {"snowflake": {"chartType": "scorecard", "scorecardConfig": {
            "format": "decimal", "decimals": decimals, "abbreviate": True,
            "deltaColorMode": "increasesBetter" if increases_better else "decreasesBetter",
            "comparisonMode": "manual", "comparisonEnabled": compare,
            "prevColumn": "PRIOR_VALUE", "currentColumn": "CURRENT_VALUE",
            "displayFormat": "change", "sparklineEnabled": False,
            "labelEnabled": True, "labelField": "", "labelText": label}}}}}


def kpi_sql(expression):
    """Current period vs the same months one year earlier, both under identical filters."""
    agg = ("SUM(NET_REVENUE) AS NET, SUM(REVENUE_TARGET) AS TGT, SUM(GROSS_PROFIT) AS GP")
    return (f"WITH cur AS (\n    SELECT {agg} FROM ({base()})\n    {where()}\n),\n"
            f"py AS (\n    SELECT {agg} FROM ({base(shift_year=True)})\n    {where()}\n)\n"
            f"SELECT {expression.format(t='cur')} AS CURRENT_VALUE, {expression.format(t='py')} AS PRIOR_VALUE\n"
            f"FROM cur CROSS JOIN py")


KPI_COLUMNS = [("CURRENT_VALUE", NUM), ("PRIOR_VALUE", NUM)]
tiles, datasources, layout = [], {}, {}


def add(tile_id, tile, position, ds=None):
    tile = {"tile_id": tile_id, **tile}
    if ds:
        datasources[f"ds-{tile_id}"] = ds
        tile["datasources"] = [f"ds-{tile_id}"]
    tiles.append(tile)
    layout[tile_id] = dict(zip("xywh", position))


add("header", {"type": "text", "text": (
    "# Revenue Pulse\n**Synthetic demo data** for a fictional B2B software company, complete through "
    f"**{CONFIG['reporting_cutoff']}**. Source: semantic view `{SV}`.\n\n"
    "Net revenue = gross revenue minus discounts and refunds. Attainment = net revenue / target. "
    "Year-over-year compares the same filtered months one year earlier. Default view: Q3 2026.")}, (0, 0, 12, 2))

add("kpi-net-revenue", scorecard("Net Revenue", "USD, vs same period last year"), (0, 2, 3, 2),
    datasource(kpi_sql("{t}.NET"), KPI_COLUMNS))
add("kpi-attainment", scorecard("Target Attainment", "% of target, vs last year"), (3, 2, 3, 2),
    datasource(kpi_sql("100 * DIV0NULL({t}.NET, {t}.TGT)"), KPI_COLUMNS))
add("kpi-variance", scorecard("Variance to Target", "USD, net revenue minus target", decimals=0, compare=False), (6, 2, 3, 2),
    datasource(kpi_sql("{t}.NET - {t}.TGT"), KPI_COLUMNS))
add("kpi-margin", scorecard("Gross Margin", "% of net revenue, vs last year"), (9, 2, 3, 2),
    datasource(kpi_sql("100 * DIV0NULL({t}.GP, {t}.NET)"), KPI_COLUMNS))

# Trend ignores the date filter on purpose so the selected period is seen in 24-month context.
trend_ids = FILTERS[1:]
add("trend", {"title": "Monthly Net Revenue vs Target (all 24 months)", "type": "chart", "spec": {
    "transform": [{"fold": ["NET_REVENUE", "REVENUE_TARGET"], "as": ["SERIES", "VALUE"]},
                  {"calculate": "datum.SERIES === 'NET_REVENUE' ? 'Net revenue' : 'Target'", "as": "SERIES_LABEL"}],
    "mark": {"type": "line", "point": True, "interpolate": "monotone"},
    "encoding": {"x": {"field": "MONTH", "type": "temporal", "title": "Month"},
                 "y": {"field": "VALUE", "type": "quantitative", "title": "USD", "axis": {"format": "$,.2s"}},
                 "color": {"field": "SERIES_LABEL", "type": "nominal", "title": None},
                 "strokeDash": {"field": "SERIES_LABEL", "type": "nominal", "legend": None},
                 "tooltip": [{"field": "MONTH", "type": "temporal", "format": "%b %Y"},
                             {"field": "SERIES_LABEL", "title": "Series"},
                             {"field": "VALUE", "type": "quantitative", "format": "$,.0f"}]}}},
    (0, 4, 12, 4),
    datasource(f"SELECT MONTH, SUM(NET_REVENUE) AS NET_REVENUE, SUM(REVENUE_TARGET) AS REVENUE_TARGET\n"
               f"FROM ({base()})\n{where(trend_ids)}\nGROUP BY MONTH\nORDER BY MONTH",
               [("MONTH", DATE), ("NET_REVENUE", NUM), ("REVENUE_TARGET", NUM)], trend_ids))

add("by-region", {"title": "Variance to Target by Region", "type": "chart", "spec": {
    "mark": {"type": "bar", "cornerRadiusEnd": 3},
    "encoding": {"y": {"field": "REGION", "type": "nominal", "sort": "x", "title": None},
                 "x": {"field": "VARIANCE", "type": "quantitative", "title": "USD vs target", "axis": {"format": "$,.2s"}},
                 "color": {"condition": {"test": "datum.VARIANCE < 0", "value": "#d3132f"}, "value": "#0e9c73"},
                 "tooltip": [{"field": "REGION"}, {"field": "NET_REVENUE", "type": "quantitative", "format": "$,.0f", "title": "Net revenue"},
                             {"field": "REVENUE_TARGET", "type": "quantitative", "format": "$,.0f", "title": "Target"},
                             {"field": "VARIANCE", "type": "quantitative", "format": "$,.0f", "title": "Variance"},
                             {"field": "ATTAINMENT", "type": "quantitative", "format": ".1%", "title": "Attainment"}]}}},
    (0, 8, 6, 4),
    datasource(f"SELECT REGION, SUM(NET_REVENUE) AS NET_REVENUE, SUM(REVENUE_TARGET) AS REVENUE_TARGET,\n"
               f"    SUM(NET_REVENUE) - SUM(REVENUE_TARGET) AS VARIANCE,\n"
               f"    DIV0NULL(SUM(NET_REVENUE), SUM(REVENUE_TARGET)) AS ATTAINMENT\n"
               f"FROM ({base()})\n{where()}\nGROUP BY REGION\nORDER BY VARIANCE",
               [("REGION", TXT), ("NET_REVENUE", NUM), ("REVENUE_TARGET", NUM), ("VARIANCE", NUM), ("ATTAINMENT", NUM)]))

add("heatmap", {"title": "Target Attainment: Region x Segment", "type": "chart", "spec": {
    "layer": [
        {"mark": {"type": "rect", "stroke": "white", "strokeWidth": 2},
         "encoding": {"color": {"field": "ATTAINMENT", "type": "quantitative", "title": "Attainment",
                                "scale": {"domain": [0.5, 1, 1.1], "range": ["#d3132f", "#f5f5f5", "#0e9c73"]},
                                "legend": {"format": ".0%"}}}},
        {"mark": {"type": "text", "fontWeight": "bold"},
         "encoding": {"text": {"field": "ATTAINMENT", "type": "quantitative", "format": ".0%"}}}],
    "encoding": {"x": {"field": "SEGMENT", "type": "nominal", "title": None, "sort": ["Enterprise", "Mid-market", "SMB"]},
                 "y": {"field": "REGION", "type": "nominal", "title": None},
                 "tooltip": [{"field": "REGION"}, {"field": "SEGMENT"},
                             {"field": "ATTAINMENT", "type": "quantitative", "format": ".1%"},
                             {"field": "VARIANCE", "type": "quantitative", "format": "$,.0f"}]}}},
    (6, 8, 6, 4),
    datasource(f"SELECT REGION, SEGMENT, DIV0NULL(SUM(NET_REVENUE), SUM(REVENUE_TARGET)) AS ATTAINMENT,\n"
               f"    SUM(NET_REVENUE) - SUM(REVENUE_TARGET) AS VARIANCE\n"
               f"FROM ({base()})\n{where()}\nGROUP BY REGION, SEGMENT",
               [("REGION", TXT), ("SEGMENT", TXT), ("ATTAINMENT", NUM), ("VARIANCE", NUM)]))

driver_dims = ", revenue.recorded_driver"
add("drivers", {"title": "What Sales Ops Recorded: Variance by Driver", "type": "chart", "spec": {
    "transform": [{"calculate": "replace(replace(datum.RECORDED_DRIVER, 'RECORDED_', ''), /_/g, ' ')", "as": "DRIVER"}],
    "mark": {"type": "bar", "cornerRadiusEnd": 3},
    "encoding": {"y": {"field": "DRIVER", "type": "nominal", "sort": "x", "title": None},
                 "x": {"field": "VARIANCE", "type": "quantitative", "title": "USD vs target", "axis": {"format": "$,.2s"}},
                 "color": {"condition": {"test": "datum.VARIANCE < 0", "value": "#d3132f"}, "value": "#0e9c73"},
                 "tooltip": [{"field": "DRIVER"}, {"field": "VARIANCE", "type": "quantitative", "format": "$,.0f"},
                             {"field": "DISCOUNTS", "type": "quantitative", "format": "$,.0f"},
                             {"field": "REFUNDS", "type": "quantitative", "format": "$,.0f"},
                             {"field": "ACCOUNTS", "type": "quantitative", "title": "Accounts"}]}}},
    (0, 12, 6, 4),
    datasource(f"SELECT RECORDED_DRIVER, SUM(NET_REVENUE) - SUM(REVENUE_TARGET) AS VARIANCE,\n"
               f"    SUM(TOTAL_DISCOUNTS) AS DISCOUNTS, SUM(TOTAL_REFUNDS) AS REFUNDS, COUNT(DISTINCT CUSTOMER_NAME) AS ACCOUNTS\n"
               f"FROM ({base(driver_dims + ', customers.customer_name')})\n{where()}\nGROUP BY RECORDED_DRIVER\nORDER BY VARIANCE",
               [("RECORDED_DRIVER", TXT), ("VARIANCE", NUM), ("DISCOUNTS", NUM), ("REFUNDS", NUM), ("ACCOUNTS", NUM)]))

add("ask", {"type": "text", "text": (
    "### Ask Revenue Advisor\nUse the chat box below this dashboard. Try:\n"
    "- *Why is EMEA Enterprise behind target in Q3 2026? Quantify the drivers.*\n"
    "- *Which accounts contributed most to the Q3 shortfall?*\n"
    "- *Will the renewal-delayed revenue recover in Q4?*\n"
    "- *How much of the gap is associated with discounts and refunds?*\n\n"
    "Drivers come from the `RECORDED_DRIVER` field logged by sales ops. They are recorded reasons, not inferred causes.")},
    (6, 12, 6, 4))

add("accounts", {"title": "Account Detail (sorted by variance)", "type": "table", "spec": {"columns": [
    {"field": "CUSTOMER_NAME", "label": "Account"}, {"field": "REGION", "label": "Region"},
    {"field": "SEGMENT", "label": "Segment"}, {"field": "NET_REVENUE", "label": "Net revenue (USD)"},
    {"field": "REVENUE_TARGET", "label": "Target (USD)"}, {"field": "VARIANCE", "label": "Variance (USD)"},
    {"field": "ATTAINMENT_PCT", "label": "Attainment %"}, {"field": "GROSS_MARGIN_PCT", "label": "Gross margin %"},
    {"field": "TOP_DRIVER", "label": "Recorded driver"}]}},
    (0, 16, 12, 6),
    datasource(f"SELECT CUSTOMER_NAME, REGION, SEGMENT, ROUND(SUM(NET_REVENUE), 0) AS NET_REVENUE,\n"
               f"    ROUND(SUM(REVENUE_TARGET), 0) AS REVENUE_TARGET,\n"
               f"    ROUND(SUM(NET_REVENUE) - SUM(REVENUE_TARGET), 0) AS VARIANCE,\n"
               f"    ROUND(100 * DIV0NULL(SUM(NET_REVENUE), SUM(REVENUE_TARGET)), 1) AS ATTAINMENT_PCT,\n"
               f"    ROUND(100 * DIV0NULL(SUM(GROSS_PROFIT), SUM(NET_REVENUE)), 1) AS GROSS_MARGIN_PCT,\n"
               f"    MAX_BY(RECORDED_DRIVER, ABS(REVENUE_TARGET - NET_REVENUE)) AS TOP_DRIVER\n"
               f"FROM ({base(driver_dims + ', customers.customer_name')})\n{where()}\n"
               f"GROUP BY CUSTOMER_NAME, REGION, SEGMENT\nORDER BY VARIANCE\nLIMIT 100",
               [("CUSTOMER_NAME", TXT), ("REGION", TXT), ("SEGMENT", TXT), ("NET_REVENUE", NUM),
                ("REVENUE_TARGET", NUM), ("VARIANCE", NUM), ("ATTAINMENT_PCT", NUM),
                ("GROSS_MARGIN_PCT", NUM), ("TOP_DRIVER", TXT)]))


def options(table, column):
    return {"source": "column", "table": f"{FQ}.{table}", "column": column}


dash = {
    "spec_version": 2, "spec_revision": 4, "version": 2, "title": "Revenue Pulse",
    "tabs": [{"order": 0, "tab_id": "default", "title": "Overview", "tiles": tiles}],
    "filters": {
        "MONTH": {"label": "Period", "mode": "range", "valueType": "DATE",
                  "default_values": ["2026-07-01", "2026-09-01"]},
        "REGION": {"label": "Region", "mode": "multi_select", "valueType": "STRING", "options": options("CUSTOMERS", "REGION")},
        "SEGMENT": {"label": "Segment", "mode": "multi_select", "valueType": "STRING", "options": options("CUSTOMERS", "SEGMENT")},
        "PRODUCT_NAME": {"label": "Product", "mode": "multi_select", "valueType": "STRING",
                         "options": options("PRODUCTS", "PRODUCT_NAME")}},
    "layout": {"default": {"meta": {"default": True}, "positions": layout}},
    "datasources": datasources,
}

if __name__ == "__main__":
    out = ROOT / "dashboards/revenue_pulse.dash"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(dash, indent=2) + "\n")
    print(f"Wrote {out} with {len(tiles)} tiles and {len(datasources)} datasources")
