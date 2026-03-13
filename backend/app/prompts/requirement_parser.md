# requirement_parser

## Goal
Parse a raw business requirement into a normalized requirement structure for downstream analysis.

## Inputs
- `merged_text`: full normalized requirement text, may include background and attachment content.

## Extraction Rules
1. `goal`: one short sentence of what the business wants to achieve.
2. `actors`: explicit user/role groups mentioned in the requirement.
3. `business_objects`: business entities or processes in scope.
4. `data_objects`: key data entities touched by this requirement.
5. `constraints`: explicit constraints (permission, compliance, SLA, technical limits).
6. `expected_output`: expected deliverable (for example export file, approval result).
7. `uncertain_points`: unresolved ambiguities that block implementation confidence.

## Quality Rules
- Prefer precise, domain-specific phrases over generic wording.
- Do not hallucinate entities that are not supported by input text.
- Keep values concise and deduplicated.
- If a field cannot be inferred, return empty string or empty array (schema-valid).
