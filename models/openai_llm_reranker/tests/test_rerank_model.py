import unittest
from unittest.mock import Mock, patch

from models.rerank.ranking import InvalidRankingError
from models.rerank.rerank import OpenAILLMRerankerModel
from models.rerank.responses_client import InvalidScoreError, RankedScores


class RerankModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = object.__new__(OpenAILLMRerankerModel)

    @patch("models.rerank.rerank.create_responses_client")
    def test_returns_original_documents_with_rank_scores(self, create_client: Mock) -> None:
        client = create_client.return_value
        client.rank.return_value = [2, 0, 1]

        result = self.model._invoke(
            model="rank-only-config",
            credentials={
                "endpoint_model_name": "gpt-test",
                "window_size": "20",
                "step_size": "10",
            },
            query="query",
            docs=["first", "second", "third"],
            top_n=2,
        )

        self.assertEqual([document.index for document in result.docs], [2, 0])
        self.assertEqual([document.text for document in result.docs], ["third", "first"])
        self.assertEqual([document.score for document in result.docs], [1.0, 0.5])
        self.assertEqual(result.model, "rank-only-config")
        create_client.assert_called_once_with(
            {
                "endpoint_model_name": "gpt-test",
                "window_size": "20",
                "step_size": "10",
            },
            "gpt-test",
        )

    @patch("models.rerank.rerank.create_responses_client")
    def test_requires_endpoint_model_name(self, create_client: Mock) -> None:
        with self.assertRaisesRegex(ValueError, "API model or deployment name is required"):
            self.model._invoke(
                model="display-name",
                credentials={},
                query="query",
                docs=["document"],
            )

        create_client.assert_not_called()

    @patch("models.rerank.rerank.create_responses_client")
    def test_applies_score_threshold_to_pseudo_scores(self, create_client: Mock) -> None:
        create_client.return_value.rank.return_value = [0, 1, 2]

        result = self.model._invoke(
            model="gpt-test",
            credentials={"endpoint_model_name": "gpt-test"},
            query="query",
            docs=["first", "second", "third"],
            score_threshold=0.4,
        )

        self.assertEqual([document.index for document in result.docs], [0, 1])

    @patch("models.rerank.rerank.create_responses_client")
    def test_preserves_order_after_invalid_structured_responses(self, create_client: Mock) -> None:
        create_client.return_value.rank.side_effect = InvalidRankingError("invalid")

        result = self.model._invoke(
            model="gpt-test",
            credentials={"endpoint_model_name": "gpt-test"},
            query="query",
            docs=["first", "second"],
        )

        self.assertEqual([document.index for document in result.docs], [0, 1])

    @patch("models.rerank.rerank.create_responses_client")
    def test_uses_llm_relevance_scores_and_applies_threshold(self, create_client: Mock) -> None:
        client = create_client.return_value
        client.rank_with_scores.return_value = RankedScores(
            order=[2, 0, 1], scores=[0.0, 0.0, 0.2]
        )

        result = self.model._invoke(
            model="gpt-test",
            credentials={
                "endpoint_model_name": "gpt-test",
                "score_mode": "llm_estimated_relevance",
            },
            query="query",
            docs=["first", "second", "third"],
            score_threshold=0.1,
        )

        self.assertEqual([document.index for document in result.docs], [2])
        self.assertEqual([document.score for document in result.docs], [0.2])
        client.rank_with_scores.assert_called_once_with(
            "query", ["first", "second", "third"], [None, None, None], user=None
        )

    @patch("models.rerank.rerank.create_responses_client")
    def test_preserves_listwise_order_when_llm_scores_are_tied(
        self, create_client: Mock
    ) -> None:
        client = create_client.return_value
        client.rank_with_scores.return_value = RankedScores(
            order=[2, 0, 1], scores=[0.6, 0.2, 0.6]
        )

        result = self.model._invoke(
            model="gpt-test",
            credentials={
                "endpoint_model_name": "gpt-test",
                "score_mode": "llm_estimated_relevance",
            },
            query="query",
            docs=["first", "second", "third"],
        )

        self.assertEqual([document.index for document in result.docs], [2, 0, 1])
        self.assertEqual([document.score for document in result.docs], [0.6, 0.6, 0.2])

    @patch("models.rerank.rerank.create_responses_client")
    def test_assigns_zero_to_all_documents_after_invalid_scores(
        self, create_client: Mock
    ) -> None:
        client = create_client.return_value
        client.rank_with_scores.side_effect = InvalidScoreError("invalid")

        result = self.model._invoke(
            model="gpt-test",
            credentials={
                "endpoint_model_name": "gpt-test",
                "score_mode": "llm_estimated_relevance",
            },
            query="query",
            docs=["first", "second"],
        )

        self.assertEqual([document.index for document in result.docs], [0, 1])
        self.assertEqual([document.score for document in result.docs], [0.0, 0.0])

    @patch("models.rerank.rerank.create_responses_client")
    def test_scores_a_single_document_with_the_llm(self, create_client: Mock) -> None:
        client = create_client.return_value
        client.rank_with_scores.return_value = RankedScores(order=[0], scores=[0.2])

        result = self.model._invoke(
            model="gpt-test",
            credentials={
                "endpoint_model_name": "gpt-test",
                "score_mode": "llm_estimated_relevance",
            },
            query="query",
            docs=["weakly related"],
        )

        self.assertEqual(result.docs[0].score, 0.2)
        client.rank.assert_not_called()
        client.rank_with_scores.assert_called_once_with(
            "query", ["weakly related"], [None], user=None
        )


if __name__ == "__main__":
    unittest.main()
