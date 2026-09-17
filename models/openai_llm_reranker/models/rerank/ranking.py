from collections.abc import Callable, Sequence
from dataclasses import dataclass


class InvalidRankingError(ValueError):
    pass


@dataclass(frozen=True)
class RankingSettings:
    window_size: int = 20
    step_size: int = 10

    def __post_init__(self) -> None:
        if self.window_size < 2:
            raise ValueError("window_size must be at least 2")
        if self.step_size < 1 or self.step_size >= self.window_size:
            raise ValueError("step_size must be between 1 and window_size - 1")


RankWindow = Callable[[str, Sequence[str]], list[int]]
ScoredRankWindow = Callable[
    [str, Sequence[str], Sequence[float | None]],
    tuple[list[int], list[float]],
]


def validate_permutation(order: Sequence[int], size: int) -> list[int]:
    if len(order) != size or set(order) != set(range(size)):
        raise InvalidRankingError(
            f"ranking must contain every document ID exactly once: expected 0..{size - 1}"
        )
    return list(order)


def rerank_with_sliding_windows(
    query: str,
    documents: Sequence[str],
    rank_window: RankWindow,
    settings: RankingSettings,
) -> list[int]:
    ranked_indices = list(range(len(documents)))
    if not ranked_indices:
        return ranked_indices

    end = len(ranked_indices)
    while True:
        start = max(0, end - settings.window_size)
        window_indices = ranked_indices[start:end]
        window_documents = [documents[index] for index in window_indices]
        relative_order = validate_permutation(
            rank_window(query, window_documents), len(window_indices)
        )
        ranked_indices[start:end] = [window_indices[index] for index in relative_order]

        if start == 0:
            break
        end -= settings.step_size

    return ranked_indices


def rerank_with_sliding_windows_and_scores(
    query: str,
    documents: Sequence[str],
    rank_window: ScoredRankWindow,
    settings: RankingSettings,
) -> tuple[list[int], dict[int, float]]:
    ranked_indices = list(range(len(documents)))
    scores_by_index: dict[int, float] = {}
    if not ranked_indices:
        return ranked_indices, scores_by_index

    end = len(ranked_indices)
    while True:
        start = max(0, end - settings.window_size)
        window_indices = ranked_indices[start:end]
        window_documents = [documents[index] for index in window_indices]
        existing_scores = [scores_by_index.get(index) for index in window_indices]
        relative_order, relative_scores = rank_window(
            query,
            window_documents,
            existing_scores,
        )
        relative_order = validate_permutation(relative_order, len(window_indices))
        if len(relative_scores) != len(window_indices):
            raise ValueError("scores must match the number of documents in the window")
        scores_by_index.update(zip(window_indices, relative_scores, strict=True))
        ranked_indices[start:end] = [window_indices[index] for index in relative_order]

        if start == 0:
            break
        end -= settings.step_size

    return ranked_indices, scores_by_index


def reciprocal_rank_score(zero_based_rank: int) -> float:
    if zero_based_rank < 0:
        raise ValueError("zero_based_rank must not be negative")
    return 1.0 / (zero_based_rank + 1)
