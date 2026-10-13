# Manual Test in Dify

## Verify Reranking

1. Create a Knowledge and upload [`reranking-test-corpus.txt`](./reranking-test-corpus.txt).
2. Use `=== CHUNK ===` as the custom delimiter and verify that four chunks are created.
3. Complete indexing, then open the Knowledge retrieval testing page.
4. Set `Top K` to `4` and disable the score threshold.
5. Run the following query with reranking disabled, then enable reranking and select **OpenAI LLM Reranker** to run it again:

   `What is the cheapest plan that includes both SSO and audit logs?`

With reranking enabled, the expected order begins with:

1. **Team plan**: includes both features and is the cheapest qualifying plan at $49.
2. **Enterprise plan**: includes both features but costs $199.

The Starter and Legacy plans should appear below both qualifying plans. Their relative order is not important. All four chunks should appear at most once.

## Compare Score Calculation Modes

Keep the score threshold disabled and run this unrelated query with each `Score Calculation` setting:

`How do I bake sourdough bread?`

- With `From final rank`, the results receive position-based scores (`1.0`, `0.5`, approximately `0.333`, and `0.25`) even though none of the plans answers the query.
- With `LLM-estimated relevance (6 levels)`, all results should receive low scores such as `0.0` or `0.2`; the first result should not automatically receive `1.0`.
- With `LLM-estimated relevance (continuous)`, all results should also receive low scores, but intermediate values such as `0.05` or `0.13` are allowed. Scores must be finite numbers between `0.0` and `1.0`, inclusive.

Exact scores may vary because they are estimated by the selected LLM. Continuous mode permits intermediate values but does not require them; returning only reference-point values is also valid.

### Evaluate Continuous Thresholds

1. Register the same API model twice, once with each estimated relevance mode. Keep all other settings identical.
2. Repeat the plan query from the first section with the score threshold disabled and record the order and scores.
3. Set a threshold between two observed continuous scores, then repeat the query. Verify that returned scores meet the threshold (a score equal to the threshold is retained).
4. Repeat both the plan query and the unrelated query several times with each mode. Compare whether relevant documents are retained, unrelated documents are rejected, and decisions remain stable.
5. Set `Top K` to `1` and run the unrelated query again. Both estimated relevance modes should still assign a low score rather than automatically returning `1.0`.
6. To exercise overlapping windows with the four-chunk corpus, set `Window Size` to `2` and `Step Size` to `1`. Verify descending scores and no duplicate chunks. If inspecting Responses API requests, confirm that previously assigned `existing_score` values are returned unchanged, including their decimal precision.

Finer values do not guarantee better ranking or calibrated probabilities. Choose a threshold using representative queries rather than relying on exact scores from one run.
