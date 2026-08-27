# Graphify on AiChart (read-only clone, --mode deep --code-only)

Command: `graphify . --mode deep --wiki --no-viz --code-only` in `/tmp/refs/AiChart`.

Result: 53851 nodes, 116434 edges.

EXTRACTED edges used as port rules (not INFERRED, not source copies):

- `validateEntryCoherence()` contained in `entrySemantics.ts` [EXTRACTED]
- `buildGates()` imports and calls `validateEntryCoherence()` [EXTRACTED]
  → fill-rule coherence is a gate, not a prompt suggestion.
- Recommendation card fields: direction, plan_type, execution state, fill/entry,
  invalidation, activation rule, similar cases.
- Vision: Deep must see the chart; numbers-only is a weaker/non-tradeable path.

This project's own graph lives in `graphify-out/` after `/graphify .`.
Navigate that wiki instead of re-reading the tree.
