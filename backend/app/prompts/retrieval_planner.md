# retrieval_planner

## Goal
Generate a retrieval plan that can fetch high-value evidence for capability/risk decisions.

## Inputs
- `requirement_text`: original requirement text.
- `parsed_requirement`: normalized structure produced by requirement parser.
- `business_domain`: optional domain hint.
- `module_hint`: optional module hint.

## Planning Rules
1. Build 3 to 5 concrete `queries` that cover:
   - capability feasibility,
   - API/implementation evidence,
   - constraints and risks.
2. Set `source_filters` conservatively using available hints.
3. Set `module_tags` using extracted business objects or module hint.

## Quality Rules
- Queries must be specific enough to retrieve implementation evidence.
- Do not output placeholder queries such as "search docs" or "general query".
- Avoid duplicates and highly overlapping queries.
- If no reliable filter is available, return an empty object for filters.
