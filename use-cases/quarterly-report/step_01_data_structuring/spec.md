# Step 1: Data Structuring

## Objective
You will be provided with raw quarterly business data. Organise it into a clean, consistently formatted structure that the analysis step can work from directly. Do not perform any analysis or calculate any derived metrics — only structure and validate what is given.

## Guidelines
- Preserve all values exactly as provided. Do not round, estimate, or fill in missing values.
- If a value is marked `null` or absent, carry it forward as null and include any note that accompanies it.
- Organise the output into clearly labelled sections: Revenue by Product Line, Revenue by Region, Operating Expenses by Department, Headcount, and Customer Metrics.
- For each section, present both the current quarter value and the prior year quarter value side by side.
- Validate that total revenue implied by product lines and total revenue implied by regions are consistent with each other. If they do not match, flag the discrepancy explicitly with a note — do not silently correct it.
- State the report period (current quarter and comparison quarter) at the top of the output.
- Do not include any personally identifiable information. All figures must be aggregated.
