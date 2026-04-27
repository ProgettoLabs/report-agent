# Step 4: Report Assembly

## Objective
Assemble the outputs from all previous steps into a single, well-structured markdown report. This is the final deliverable of the pipeline.

## Input
You will receive **only the output of Step 3**, which contains everything needed:
- The executive narrative (the Step 3 prose content)
- Inside `## Relayed Input`: the full Step 2 output, which contains:
  - The analysis results (financial summary, revenue by segment, expenses, customer metrics, growth areas, flagged items)
  - Inside its own `## Relayed Input`: the full Step 1 output with the structured data tables

Extract each section from the appropriate location in the chained output to assemble the report.

## Guidelines
- Structure the report in the following order:
  1. Title page block: report title, period (from the Step 1 data), and preparation date
  2. Table of contents listing the sections below
  3. Executive Summary: the prose narrative from Step 3, reproduced exactly with no edits (do not include the `## Relayed Input` section)
  4. Financial Analysis: the financial summary, revenue by segment, and expenses by department tables from Step 2
  5. Customer Analysis: the customer metrics, top/bottom growth areas, and flagged items from Step 2
  6. Appendix — Full Data: the structured data tables from Step 1
- Do not add, remove, or alter any figures, sentences, or table values from the input. Assembly only — no new content.
- Use consistent markdown heading levels: `#` for the report title, `##` for top-level sections, `###` for subsections.
- Add a horizontal rule (`---`) between each major section for readability.
- The table of contents should use markdown links to the section headings.
- Do not include any `## Relayed Input` sections in the final report output.
