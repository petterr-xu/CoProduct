# impact_analyzer

## Goal
Identify impacted system modules and explain why each module is affected.

## Inputs
- `parsed_requirement`: normalized requirement fields.
- `module_hint`: optional module hint from request.

## Output Semantics
- Return `items` where each item has:
  - `module`: impacted module identifier/name.
  - `reason`: concrete reason tied to requirement scope/behavior.

## Rules
1. List only modules with direct impact.
2. Prefer canonical/internal module names when available.
3. Keep reason concise but specific (avoid generic text).
4. If impact cannot be identified, return `{"items":[]}`.

## Hard Constraints
- Do not output module-free items.
- Do not output prose outside JSON.
