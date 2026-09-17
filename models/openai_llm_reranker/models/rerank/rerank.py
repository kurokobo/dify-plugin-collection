import logging

import httpx
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    PermissionDeniedError,
    RateLimitError,
)

from dify_plugin import RerankModel
from dify_plugin.entities.model import AIModelEntity, FetchFrom, I18nObject, ModelType
from dify_plugin.entities.model.rerank import RerankDocument, RerankResult
from dify_plugin.errors.model import (
    CredentialsValidateFailedError,
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)

from .ranking import (
    InvalidRankingError,
    RankingSettings,
    reciprocal_rank_score,
    rerank_with_sliding_windows,
    rerank_with_sliding_windows_and_scores,
)
from .responses_client import InvalidScoreError, create_responses_client

logger = logging.getLogger(__name__)


class OpenAILLMRerankerModel(RerankModel):
    def _invoke(
        self,
        model: str,
        credentials: dict,
        query: str,
        docs: list[str],
        score_threshold: float | None = None,
        top_n: int | None = None,
        user: str | None = None,
    ) -> RerankResult:
        if not docs:
            return RerankResult(model=model, docs=[])

        client = create_responses_client(credentials, _endpoint_model_name(credentials))
        max_doc_characters = _positive_int(credentials, "max_doc_characters", 4000)
        truncated_docs = [document[:max_doc_characters] for document in docs]
        window_size = _positive_int(credentials, "window_size", 20)

        settings = RankingSettings(
            window_size=window_size,
            step_size=_positive_int(credentials, "step_size", 10),
        )
        use_llm_scores = _use_llm_scores(credentials)
        scores_by_index: dict[int, float] | None = None

        if use_llm_scores:
            def rank_scored_window(
                window_query: str,
                window_docs: list[str],
                existing_scores: list[float | None],
            ) -> tuple[list[int], list[float]]:
                try:
                    result = client.rank_with_scores(
                        window_query,
                        window_docs,
                        existing_scores,
                        user=user,
                    )
                    return result.order, result.scores
                except InvalidScoreError:
                    logger.warning(
                        "Structured scored ranking failed; preserving order and known scores"
                    )
                    return (
                        list(range(len(window_docs))),
                        [score if score is not None else 0.0 for score in existing_scores],
                    )

            ranked_indices, scores_by_index = rerank_with_sliding_windows_and_scores(
                query=query,
                documents=truncated_docs,
                rank_window=rank_scored_window,
                settings=settings,
            )
            ranked_indices.sort(key=lambda index: -scores_by_index[index])
        elif len(docs) == 1:
            ranked_indices = [0]
        else:
            def rank_window(window_query: str, window_docs: list[str]) -> list[int]:
                try:
                    return client.rank(window_query, window_docs, user=user)
                except InvalidRankingError:
                    logger.warning("Structured ranking failed; preserving the current window order")
                    return list(range(len(window_docs)))

            ranked_indices = rerank_with_sliding_windows(
                query=query,
                documents=truncated_docs,
                rank_window=rank_window,
                settings=settings,
            )

        result_limit = len(docs) if top_n is None else max(0, min(top_n, len(docs)))
        reranked_docs: list[RerankDocument] = []
        for rank, document_index in enumerate(ranked_indices[:result_limit]):
            score = (
                scores_by_index[document_index]
                if scores_by_index is not None
                else reciprocal_rank_score(rank)
            )
            if score_threshold is not None and score < score_threshold:
                continue
            reranked_docs.append(
                RerankDocument(
                    index=document_index,
                    text=docs[document_index],
                    score=score,
                )
            )

        return RerankResult(model=model, docs=reranked_docs)

    def validate_credentials(self, model: str, credentials: dict) -> None:
        try:
            client = create_responses_client(credentials, _endpoint_model_name(credentials))
            if _use_llm_scores(credentials):
                client.rank_with_scores(
                    "Which document identifies the capital of Japan?",
                    [
                        "Osaka is a major commercial center in Japan.",
                        "Tokyo is the capital of Japan.",
                    ],
                    [None, None],
                )
            else:
                client.rank(
                    "Which document identifies the capital of Japan?",
                    [
                        "Osaka is a major commercial center in Japan.",
                        "Tokyo is the capital of Japan.",
                    ],
                )
        except Exception as error:
            raise CredentialsValidateFailedError(str(error)) from error

    def get_customizable_model_schema(self, model: str, credentials: dict) -> AIModelEntity:
        return AIModelEntity(
            model=model,
            label=I18nObject(en_us=model, zh_hans=model),
            model_type=ModelType.RERANK,
            fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
            model_properties={},
        )

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        return {
            InvokeConnectionError: [httpx.ConnectError, APIConnectionError, APITimeoutError],
            InvokeServerUnavailableError: [httpx.RemoteProtocolError, InternalServerError],
            InvokeRateLimitError: [RateLimitError],
            InvokeAuthorizationError: [AuthenticationError, PermissionDeniedError],
            InvokeBadRequestError: [BadRequestError, ValueError],
        }


def _positive_int(credentials: dict, name: str, default: int) -> int:
    value = int(credentials.get(name) or default)
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


def _endpoint_model_name(credentials: dict) -> str:
    endpoint_model_name = str(credentials.get("endpoint_model_name") or "").strip()
    if not endpoint_model_name:
        raise ValueError("API model or deployment name is required")
    return endpoint_model_name


def _use_llm_scores(credentials: dict) -> bool:
    mode = credentials.get("score_mode") or "reciprocal_rank"
    if mode == "reciprocal_rank":
        return False
    if mode == "llm_estimated_relevance":
        return True
    raise ValueError(f"Unsupported score mode: {mode}")


