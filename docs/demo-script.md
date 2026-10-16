# Five-minute demo script

Setup: be signed in to Snowsight with the dashboard open, and have CoWork open in a second tab. Start with no filters other than the default Q3 2026 period.

## 1. The starting point (30 s)

"Our analyst already has a revenue semantic view and an agent called Revenue Advisor that sales uses in CoWork. What's missing is a shared source of truth the team sees every morning."

Show `REVENUE_SEMANTIC_VIEW` in the catalog briefly: metrics like net revenue, target attainment, and gross margin, plus dimensions like region, segment, and recorded driver.

## 2. The dashboard in Workspaces (90 s)

Open `dashboards/revenue_pulse.dash` in the Git-synced workspace.

- The KPI row reads: net revenue **$6.9M**, barely up (0.8%) on last year, and attainment is only **86.3%**, which is **$1.09M behind target**.
- Trend: revenue tracked target for 21 months, then fell below it in July.
- Region bar and heatmap: **EMEA Enterprise is at 58%**, the worst cell. APAC is behind in every segment (65–88%); the Americas is ahead only because Enterprise is at 117%.
- Drivers chart: what sales ops recorded. Renewal delay is the largest, then contract downsizes, then discounts and credits.

"Every tile is a query on the same semantic view the agent uses, so the dashboard and the agent can't disagree."

## 3. Interactivity (45 s)

Set **Region = EMEA**. All tiles re-query: net revenue $1.8M, attainment 70%, variance −$779.1K, and the trend shows the July drop clearly. Add **Segment = Enterprise** and point to the account table: account 05 has zero revenue, and accounts 01 to 04 are well under target. Clear the filters.

## 4. Publish (45 s)

Choose **Share > Publish as artifact**. Point out the note that viewers run the dashboard under their own privileges. Add **DASHBOARD_DEMO_SALES_OPS** with **Can view**, then select **Publish**. The toast says "Published as an artifact and to CoWork", and the button becomes **Publish changes** for later edits.

## 5. CoWork: see it, then ask why (90 s)

In CoWork, open **Artifacts**, select the **All** tab, and then open **Revenue Pulse**, which shows the same dashboard and filters. In the chat below it, ask:

> Why is EMEA Enterprise behind target in Q3 2026? Quantify the drivers.

Expected answer, verified against SQL: a $778.7K shortfall at 58% attainment. The answer breaks it into renewal delay (−$348.7K), contract downsize (−$258.7K), and discount and service credit (−$182.0K), offset by normal trading (+$10.7K), with an account named for each. The parts sum to the total. It labels these as recorded reasons, not inferred causes. CoWork answers this from the dashboard's own data, opening a chat with the dashboard docked beside it.

For deeper questions, open the Revenue Advisor agent in CoWork. It queries the semantic view directly and gives the same breakdown.

Follow-up if there's time: *"Which accounts contributed most?"* The answer is account 05, then 01 and 02, which together make up about 78% of the gap.

## Close

"The analyst built it once on governed definitions, published it to a role, and the sales team gets a daily view they can question directly."
