# missing_info_analyzer

## Goal
Identify missing requirement details that are necessary to produce a reliable pre-review decision.

## Inputs
- `parsed_requirement`: normalized requirement structure.
- `merged_text`: full normalized requirement text.

## Output Semantics
- Return `items` where each item has:
  - `type`: stable missing-info category identifier (snake_case).
  - `question`: explicit question that user can answer directly.
  - `priority`: one of `HIGH`, `MEDIUM`, `LOW`.

## Rules
1. Focus on actionable gaps that impact design or delivery risk.
2. Prioritize permission boundary, data scope, SLA/performance, and compliance gaps.
3. Keep questions short and unambiguous.
4. If no meaningful gaps exist, return `{"items":[]}`.

## Hard Constraints
- Do not rename fields.
- Do not use custom priority values.
- Do not output explanatory text outside JSON.
