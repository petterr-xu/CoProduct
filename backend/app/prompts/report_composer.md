# report_composer

## Goal
Compose a final pre-review report object for frontend rendering and persistence.

## Inputs
- `parsed_requirement`
- `capability_judgement`
- `evidence_pack`
- `missing_info_items`
- `risk_items`
- `impact_items`

## Composition Rules
1. `summary`: concise executive summary, include capability conclusion and confidence.
2. `capabilityJudgement`: preserve judgement semantics, do not invent enum values.
3. `structuredDraft`: map directly from parsed requirement with schema-compatible fields.
4. `evidence`: include only selected evidence items.
5. `missingInfoItems`: pass through actionable missing-info list.
6. `riskItems`: pass through risk list with valid levels.
7. `impactItems`: pass through impacted modules with reasons.
8. `nextSteps`: 2 to 5 actionable follow-up steps.

## Quality Rules
- Keep content factual and evidence-aligned.
- Avoid contradictions across sections.
- If a section has no content, use empty list/object values that match schema.

## Hard Constraints
- Return one JSON object only.
- Field names must match schema exactly.
