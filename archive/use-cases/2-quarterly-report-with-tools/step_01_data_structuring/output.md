# Output: Step 1

## Format
Produce six separate outputs — five CSV files (one per data section) and one
short text note for validation.  Save each one individually before moving on.

---

## Outputs

### revenue_by_product_line  (CSV)
One row per product line plus a Total row.
Columns: Metric, Current Quarter, Prior Year Quarter, Notes

### revenue_by_region  (CSV)
One row per region plus a Total row.
Columns: Metric, Current Quarter, Prior Year Quarter, Notes

### operating_expenses_by_department  (CSV)
One row per department plus a Total row.
Columns: Metric, Current Quarter, Prior Year Quarter, Notes

### headcount  (CSV)
Rows: total employees start of quarter, total employees end of quarter,
new hires, departures.
Columns: Metric, Current Quarter, Prior Year Quarter, Notes

### customer_metrics  (CSV)
Rows: active customers, new customers acquired, churned customers,
net revenue retention.
Columns: Metric, Current Quarter, Prior Year Quarter, Notes

### validation_notes  (text)
State the report period (current quarter vs comparison quarter).
Note any discrepancies (e.g. revenue totals that do not reconcile across
product lines and regions).  If there are none, write "No discrepancies found."

---

## Example CSV

```
Metric,Current Quarter,Prior Year Quarter,Notes
Product Line A,$4200000,$3800000,
Product Line B,$1750000,$1600000,
Total,$5950000,$5400000,
```
