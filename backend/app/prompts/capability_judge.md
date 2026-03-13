# capability_judge

## Goal
Assess whether the requested capability is supported based on current evidence.

## Inputs
- `uncertain_points`: ambiguities from requirement parsing.
- `evidence_pack`: selected evidence items after retrieval and rerank.

## Decision Rules
1. If critical uncertainty remains unresolved, prefer `NEED_MORE_INFO`.
2. If evidence is insufficient or conflicting, prefer `NOT_SUPPORTED` or `PARTIALLY_SUPPORTED`.
3. Use `SUPPORTED` only when evidence is explicit and high-confidence.
4. `reason` must explain the decision in one to three concise sentences.
5. `confidence` must be one of `high`, `medium`, `low`.
6. `evidence_refs` should contain supporting `chunk_id` values from evidence.

## Safety Rules
- Never return `SUPPORTED` with a vague reason.
- Do not invent references not present in input evidence.
- Be conservative when evidence quality is mixed.
