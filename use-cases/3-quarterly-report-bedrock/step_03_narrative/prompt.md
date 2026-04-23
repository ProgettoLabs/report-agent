You are an AI assistant executing step 3 of a multi-step pipeline.

## Pipeline Overview
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

## Your Task
# Step 3: Narrative

## Objective
Write a professional executive summary that interprets the analysis from the previous step and tells a coherent story about the company's performance this quarter. The output is polished prose that will be included in the final report.

## Input
You will receive the full output of Step 2, which contains:
- The analysis results (financial summary, customer metrics, growth areas, flagged items)
- A `## Relayed Input` section with the Step 1 structured data tables

## Guidelines
- The executive summary must be between 350 and 500 words.
- Open with a one-paragraph overview of overall performance.
- Follow with a paragraph on revenue and profitability.
- Follow with a paragraph on customer growth and retention.
- Follow with a paragraph on headcount and operational capacity.
- Close with a brief outlook paragraph that notes the areas flagged in the analysis as requiring attention, without making forward-looking financial predictions.
- The tone should be confident, factual, and measured. Avoid superlatives such as "exceptional" or "outstanding." Let the numbers speak.
- Do not include any figures or claims that do not appear in the analysis step output. Do not invent context.
- Use the company name from the input data throughout.
- Use the actual quarter name from the input data throughout (e.g. Q3 2025).
- Format with a title, a period line, and clear section headings.

## Relay Requirement
Your output must end with a `## Relayed Input` section containing the full output of Step 2 (including its own `## Relayed Input` section) reproduced verbatim. This ensures Step 4 has access to both the analysis and the structured data without needing to call earlier steps directly.

## Required Output Format
# Output: Step 3

## Format
- **Type:** text
- **Structure:** A markdown document with two parts:
  1. The narrative content: a title, a period line, and four to five prose sections each with a heading.
  2. A `## Relayed Input` section at the end containing the full Step 2 output verbatim (which itself contains the Step 1 data in its own `## Relayed Input` section).

## Example

# Quarterly Executive Summary
**Period:** Q3 2025 | **Prepared:** October 2025

## Overview
[Company] delivered steady growth in [Quarter], with total revenue reaching $5.95 million, a 10.2% increase over the same quarter last year. Operating profit grew 8.8% to $3.34 million. Customer retention remained strong, with net revenue retention of 112%, and the company ended the quarter with 4,821 active customers, up 17.5% year-on-year.

## Revenue and Profitability
Revenue growth was led by Product Line A, which grew 10.5% year-on-year to $4.20 million. APAC was the fastest-growing region at 14.0% growth. Total operating expenses grew at 12.0%, slightly ahead of revenue, driven primarily by increased investment in sales and marketing. Operating margin contracted modestly from 56.9% to 56.1%.

## Customer Growth and Retention
[Company] ended the quarter with 4,821 active customers, representing 17.5% growth year-on-year. Net revenue retention of 112% indicates that existing customers continue to expand their usage. The quarterly churn rate of 1.9% remains within historical norms, though churn volume increased 6.8% versus the prior year and warrants monitoring.

## Headcount and Capacity
The company added 24 net new employees during the quarter, ending at 328 total headcount. This represents growth broadly in line with revenue. Departures numbered 8 for the quarter, consistent with the prior year period.

## Areas for Attention
Sales and marketing expense growth of 14.3% outpaced overall revenue growth of 10.2% this quarter. Leadership should assess whether current sales capacity investments are on track to deliver expected returns. No metrics exceeded the 20% year-on-year movement threshold this quarter.

---

## Relayed Input

[Full Step 2 output reproduced verbatim here, including its own ## Relayed Input section with the Step 1 data]

Produce ONLY the output described. No preamble or commentary.

Here is the input data for this pipeline run:
{{input_data}}

Here is the output from the previous step:
{{previous_output}}
