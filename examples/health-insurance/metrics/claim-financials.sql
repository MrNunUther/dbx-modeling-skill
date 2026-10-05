-- Re-authored teaching artifact; see adaptation-log.csv and NOTICE.
-- NOT EXECUTED. Substitute reviewed __CATALOG__ offline before authorized use.
CREATE VIEW `__CATALOG__`.`metrics`.`claim_financials`
WITH METRICS LANGUAGE YAML AS $$
version: 1.1
comment: "Submitted-version financial totals without cross-source join fan-out."
source: "`__CATALOG__`.`claim`.`header`"
fields:
  - name: service_month
    expr: DATE_TRUNC('MONTH', service_date)
  - name: currency_code
    expr: currency_code
measures:
  - name: submission_count
    expr: COUNT(1)
  - name: total_billed_amount
    expr: SUM(billed_amount)
  - name: total_paid_amount
    expr: SUM(paid_amount)
  - name: paid_to_billed_ratio
    expr: SUM(paid_amount) / NULLIF(SUM(billed_amount), 0)
$$;
