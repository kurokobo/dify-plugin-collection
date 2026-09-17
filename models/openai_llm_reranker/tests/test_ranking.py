import unittest

from models.rerank.ranking import (
    InvalidRankingError,
    RankingSettings,
    reciprocal_rank_score,
    rerank_with_sliding_windows,
    rerank_with_sliding_windows_and_scores,
    validate_permutation,
)


class ValidatePermutationTests(unittest.TestCase):
    def test_accepts_complete_permutation(self) -> None:
        self.assertEqual(validate_permutation([2, 0, 1], 3), [2, 0, 1])

    def test_rejects_duplicate_or_missing_ids(self) -> None:
        with self.assertRaises(InvalidRankingError):
            validate_permutation([0, 0, 2], 3)

    def test_rejects_out_of_range_ids(self) -> None:
        with self.assertRaises(InvalidRankingError):
            validate_permutation([0, 1, 3], 3)


class SlidingWindowTests(unittest.TestCase):
    def test_maps_relative_order_back_to_document_indices(self) -> None:
        order = rerank_with_sliding_windows(
            query="query",
            documents=["a", "b", "c", "d"],
            rank_window=lambda _query, docs: list(reversed(range(len(docs)))),
            settings=RankingSettings(window_size=20, step_size=10),
        )

        self.assertEqual(order, [3, 2, 1, 0])

    def test_processes_tail_first_and_includes_the_head_window(self) -> None:
        calls: list[list[str]] = []

        def preserve_order(_query: str, docs: list[str]) -> list[int]:
            calls.append(list(docs))
            return list(range(len(docs)))

        rerank_with_sliding_windows(
            query="query",
            documents=[str(index) for index in range(25)],
            rank_window=preserve_order,
            settings=RankingSettings(window_size=20, step_size=10),
        )

        self.assertEqual(calls[0], [str(index) for index in range(5, 25)])
        self.assertEqual(calls[1], [str(index) for index in range(15)])

    def test_reuses_overlap_scores_and_estimates_each_document_once(self) -> None:
        existing_score_calls: list[list[float | None]] = []

        def preserve_with_scores(
            _query: str,
            docs: list[str],
            existing_scores: list[float | None],
        ) -> tuple[list[int], list[float]]:
            existing_score_calls.append(list(existing_scores))
            return (
                list(range(len(docs))),
                [score if score is not None else 0.2 for score in existing_scores],
            )

        order, scores = rerank_with_sliding_windows_and_scores(
            query="query",
            documents=[str(index) for index in range(25)],
            rank_window=preserve_with_scores,
            settings=RankingSettings(window_size=20, step_size=10),
        )

        self.assertEqual(order, list(range(25)))
        self.assertEqual(scores, dict.fromkeys(range(25), 0.2))
        self.assertEqual(existing_score_calls[0], [None] * 20)
        self.assertEqual(existing_score_calls[1], [None] * 5 + [0.2] * 10)
        self.assertEqual(
            sum(score is None for call_scores in existing_score_calls for score in call_scores),
            25,
        )


class ReciprocalRankScoreTests(unittest.TestCase):
    def test_returns_rank_based_pseudo_score(self) -> None:
        self.assertEqual(reciprocal_rank_score(0), 1.0)
        self.assertEqual(reciprocal_rank_score(1), 0.5)
        self.assertAlmostEqual(reciprocal_rank_score(2), 1 / 3)


if __name__ == "__main__":
    unittest.main()
