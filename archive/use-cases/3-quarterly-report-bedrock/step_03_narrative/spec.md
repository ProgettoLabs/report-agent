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
