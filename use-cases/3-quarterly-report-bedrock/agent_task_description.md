# Pipeline: Quarterly Business Report (Bedrock / Chained Outputs)

## Overview
This pipeline produces a polished quarterly business report for **Acme Corp** from raw financial and operational data provided by the user. It structures the input data, analyses performance against the prior year, drafts a narrative executive summary, and assembles everything into a single formatted markdown report ready for review or distribution.

## Audience
Senior leadership and board members. The tone should be professional, precise, and data-driven. Assume familiarity with business metrics but not with the underlying data systems.

## Chained Output Pattern
Each step in this pipeline receives **only the output of the immediately preceding step** as its input. To ensure every step has all the context it needs, each step must relay the full output of the previous step within its own output.

The chain works as follows:
- **Step 1** receives the raw input data and outputs structured tables.
- **Step 2** receives step 1's output, produces analysis, and appends step 1's output verbatim in a `## Relayed Input` section.
- **Step 3** receives step 2's output, produces the narrative, and appends step 2's full output verbatim in a `## Relayed Input` section (which itself contains step 1's data).
- **Step 4** receives only step 3's output, which contains the narrative plus the full chain of relayed data needed to assemble the final report.
