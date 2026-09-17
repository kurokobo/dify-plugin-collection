# 🔀 OpenAI LLM Reranker - Use OpenAI LLMs for Reranking

- **Plugin ID** : kurokobo/openai_llm_reranker
- **Author** : kurokobo
- **Type** : model
- **Repository** : <https://github.com/kurokobo/dify-plugin-collection>
- **Marketplace** : <https://marketplace.dify.ai/plugins/kurokobo/openai_llm_reranker>

## ✨ Overview

A Dify rerank model plugin that uses an OpenAI or Azure OpenAI large language model to reorder search results by relevance.

The plugin applies RankGPT-style listwise reranking through the Responses API. It supports long candidate lists, validates model output, and provides predictable fallback behavior for Dify environments where a dedicated rerank model is unavailable.

The selected model must support both the Responses API and Structured Outputs with JSON Schema. For more reliable results, choose a model with strong instruction-following and document-comparison capabilities.

## ✅ Highlights

- **Purpose-built for OpenAI and Azure OpenAI**: Supports the standard OpenAI endpoint, custom OpenAI base URLs, Azure OpenAI resource endpoints, and versionless Azure `/openai/v1` endpoints.
- **Validated results**: Checks that every candidate is returned exactly once and retries malformed or incomplete model output.
- **Predictable failure handling**: Preserves the current candidate order when valid ranking output cannot be obtained. It does not return a partial result or fail the entire retrieval.
- **Long candidate list support**: Uses overlapping windows so every candidate participates in reranking, even when all candidates cannot fit in one request.
- **Optional estimated relevance**: Scores are derived from the final rank by default, but the LLM can instead estimate absolute relevance on a six-level scale. This makes `score_threshold` useful even when none of the candidates is relevant.
- **Privacy-conscious requests**: Sets `store` to `false`, hashes Dify user identifiers before sending them as safety identifiers, and instructs the model to treat document content as untrusted data.

## ⚙️ Setup Instructions

After installing the plugin:

1. Go to the `Model Provider` section on the Dify `Settings` page.
2. Find **OpenAI LLM Reranker** and add a rerank model.
3. Enter a configuration name, the exact OpenAI model or Azure OpenAI deployment name, and the credentials described below.

Saving the model configuration validates the credentials, endpoint, selected model or deployment, and required API capabilities. This validation sends a small request and consumes a small number of API tokens.

> [!CAUTION]
> The selected LLM determines the ranking in both score modes and also determines estimated relevance when enabled. Even with the same model and input, rankings and scores may change between runs, so reproducibility is not guaranteed. LLM-estimated relevance scores do not guarantee the probability that a document is relevant to the query.

### Model configuration

| Field | Description |
| --- | --- |
| `Configuration Name` | A name used to identify this configuration in Dify, such as `gpt-5.6-sol-reciprocal-rank` or `gpt-5.6-sol-relevance`. It does not need to match the API model name. |
| `Service` | Select `OpenAI` or `Azure OpenAI`. |
| `API Model or Deployment Name` | Enter the exact OpenAI model name or Azure OpenAI deployment name used by the API. The selected model must support Structured Outputs on the Responses API. |
| `API Key` | Enter the API key for the selected service. |
| `OpenAI API Base URL` | Optional. Leave empty to use the standard OpenAI endpoint. |
| `Azure OpenAI Endpoint` | Enter either a resource endpoint such as `https://RESOURCE.openai.azure.com` or a versionless endpoint ending in `/openai/v1`. |
| `Azure API Version` | Used with resource endpoints. It is ignored for versionless `/openai/v1` endpoints. |
| `Window Size` | Maximum documents ranked in one request. Default: `20`. |
| `Step Size` | Positions moved toward the head after each request. Default: `10`; must be smaller than the window size. |
| `Maximum Characters per Document` | Documents are truncated to this length before ranking, while the original text is returned to Dify. Default: `4000`. |
| `Score Calculation` | `From final rank` derives scores from the generated order. `LLM-estimated relevance` estimates each document's usefulness on a six-level scale from `0.0` to `1.0`, allowing relevance-based threshold filtering. |

You can register the same API model more than once with different configuration names and settings. For example, create `gpt-5.6-sol-reciprocal-rank` with `From final rank` and `gpt-5.6-sol-relevance` with `LLM-estimated relevance`, then select the appropriate configuration in Dify without editing the provider settings.

## 🔍 How It Works

The model compares multiple candidate documents together and reorders them from most relevant to least relevant. This is known as listwise reranking.

For a long candidate list, overlapping windows are processed from the tail toward the head. With the defaults, the plugin ranks 20 documents at a time and moves 10 positions per request. Overlap lets documents from adjacent windows be compared indirectly and allows a relevant document near the bottom of the initial retrieval result to move upward.

### Scores

With `From final rank`, the plugin returns the reciprocal of each document's rank. The first result receives `1.0`, the second `0.5`, the third approximately `0.333`, and so on. These values express position, not absolute relevance, and should not be compared across separate searches.

With `LLM-estimated relevance`, the model assigns each document one of `0.0`, `0.2`, `0.4`, `0.6`, `0.8`, or `1.0`. All documents may receive the same low score, including `0.0`, when none appears useful for the query. Final results are ordered by score, with the listwise ranking used to break ties. This mode makes `score_threshold` more useful for filtering unrelated results, including when only one candidate is retrieved.

Previously estimated scores from overlapping windows are reused to improve consistency between windows. Because the scores are generated by an LLM, they may change between runs even with the same input and should not be compared directly across separate searches.

### Failure handling

Invalid model output is retried once. If it remains invalid, the plugin preserves the current order. In LLM-estimated relevance mode, previously obtained scores are retained and documents that could not be scored receive `0.0`; the plugin does not replace them with a potentially misleading reciprocal-rank `1.0`. Invalid output during configuration validation prevents the model configuration from being saved.

## 📚 Algorithm Rationale

The core design follows established zero-shot listwise reranking work, particularly RankGPT. Sliding-window reranking applies the same comparison to candidate lists that would be too large or costly to send in one request.

The design is a reasonable alternative when a dedicated rerank model is unavailable, but it does not guarantee the speed, cost, score calibration, or ranking quality of a purpose-trained reranker. Quality depends on the selected LLM, the documents, the initial retrieval order, and the window settings. Evaluate it with representative production data before deployment.

## ⚠️ Limitations and Security

- More candidates, longer documents, and smaller step sizes increase API cost and latency.
- Sliding windows do not guarantee the same order as ranking every candidate in one request.
- Input position can influence an LLM's judgment; overlapping windows reduce but do not eliminate this effect.
- Documents are untrusted input. The system instruction tells the model not to follow document instructions, but prompt injection can still manipulate ranking decisions.
- Output validation does not guarantee ranking correctness or prevent prompt injection.

## 📜 Privacy Policy

See [PRIVACY.md](./PRIVACY.md) for details about the data sent outside Dify and its destinations.

## ▶️ Manual Test

The [`_examples`](./_examples) directory contains a small knowledge-base corpus and step-by-step instructions for comparing retrieval with and without this reranker in Dify.

## Related Links

- **Research**: Sun et al., [Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents](https://arxiv.org/abs/2304.09542), 2023
- **Research**: Ma et al., [Zero-Shot Listwise Document Reranking with a Large Language Model](https://arxiv.org/abs/2305.02156), 2023
- **Research**: Qin et al., [Large Language Models are Effective Text Rankers with Pairwise Ranking Prompting](https://aclanthology.org/2024.findings-naacl.97/), 2024
- **Research**: Pradeep et al., [RankZephyr: Effective and Robust Zero-Shot Listwise Reranking is a Breeze!](https://aclanthology.org/2024.naacl-long.37/), 2024
- **Icon**: [Heroicons](https://heroicons.com/)
- **License**: [Apache License 2.0](../../LICENSE)
