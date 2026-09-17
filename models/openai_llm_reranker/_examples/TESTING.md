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
- With `LLM-estimated relevance`, all results should receive low scores such as `0.0` or `0.2`; the first result should not automatically receive `1.0`. Exact scores may vary because they are estimated by the selected LLM.
