# risk_analyzer

## Goal
Extract implementation and delivery risks implied by the requirement context.

## Inputs
- `merged_text`: full normalized requirement text.

## Output Semantics
- Return `items` where each item has:
  - `type`: risk category identifier.
  - `description`: concise risk statement with context.
  - `level`: one of `HIGH`, `MEDIUM`, `LOW`.

## Rules
1. Cover security/privacy, performance/capacity, reliability, and governance risks when relevant.
2. Keep each risk atomic (one core concern per item).
3. Avoid duplicates and generic "needs discussion" statements.
4. If no substantial risks are found, return `{"items":[]}`.

## Hard Constraints
- Use schema field names exactly.
- Use only allowed enum values for `level`.
- Do not output any non-JSON text.
