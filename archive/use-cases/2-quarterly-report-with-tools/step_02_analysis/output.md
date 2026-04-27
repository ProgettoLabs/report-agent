# Output: Step 2

## Format
Produce six separate outputs — four CSV files for the derived metric tables
and two text outputs for the list-based findings.  Save each one individually.

---

## Outputs

### financial_summary  (CSV)
Columns: Metric, Current Quarter, Prior Year Quarter, YoY Change
Rows: total revenue, total operating expenses, operating profit,
operating margin.

### revenue_by_segment  (CSV)
Columns: Segment, Current Quarter, Prior Year Quarter, YoY Change
One row per product line and per region.

### expenses_by_department  (CSV)
Columns: Department, Current Quarter, Prior Year Quarter, YoY Change
One row per department.

### customer_metrics  (CSV)
Columns: Metric, Value
Rows: customer growth rate, quarterly churn rate, net revenue retention.

### growth_highlights  (text)
Plain text.  List the top two and bottom two growth areas by year-on-year
percentage change, with the percentage shown for each.

### flagged_items  (text)
Plain text.  List any metric where the year-on-year change exceeds 20% in
either direction, with the actual percentage.  If none qualify, write
"No flagged items this quarter."

---

## Example CSV

```
Metric,Current Quarter,Prior Year Quarter,YoY Change
Total revenue,$5950000,$5400000,+10.2%
Total operating expenses,$2610000,$2330000,+12.0%
Operating profit,$3340000,$3070000,+8.8%
Operating margin,56.1%,56.9%,-0.8 pp
```
