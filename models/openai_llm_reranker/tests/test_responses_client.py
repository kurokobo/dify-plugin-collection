import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from models.rerank.ranking import InvalidRankingError
from models.rerank.responses_client import (
    InvalidScoreError,
    StructuredRankingClient,
    create_responses_client,
)


class StructuredRankingClientTests(unittest.TestCase):
    def test_requests_strict_json_schema_and_parses_ranking(self) -> None:
        api = Mock()
        api.responses.create.return_value = SimpleNamespace(
            status="completed", output_text=json.dumps({"ranking": [1, 0]})
        )

        result = StructuredRankingClient(api, "gpt-test").rank(
            "query", ["first", "second"], user="user-1"
        )

        self.assertEqual(result, [1, 0])
        request = api.responses.create.call_args.kwargs
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertTrue(request["text"]["format"]["strict"])
        self.assertFalse(request["store"])
        self.assertNotEqual(request["safety_identifier"], "user-1")

    def test_retries_invalid_permutation_once(self) -> None:
        api = Mock()
        api.responses.create.side_effect = [
            SimpleNamespace(status="completed", output_text='{"ranking":[0,0]}'),
            SimpleNamespace(status="completed", output_text='{"ranking":[1,0]}'),
        ]

        result = StructuredRankingClient(api, "gpt-test").rank("query", ["a", "b"])

        self.assertEqual(result, [1, 0])
        self.assertEqual(api.responses.create.call_count, 2)

    def test_rejects_incomplete_response_after_retry(self) -> None:
        api = Mock()
        api.responses.create.return_value = SimpleNamespace(status="incomplete", output_text="")

        with self.assertRaises(InvalidRankingError):
            StructuredRankingClient(api, "gpt-test").rank("query", ["a", "b"])

        self.assertEqual(api.responses.create.call_count, 2)

    def test_requests_scored_ranking_and_preserves_existing_scores(self) -> None:
        api = Mock()
        api.responses.create.return_value = SimpleNamespace(
            status="completed",
            output_text=json.dumps({"results": [{"id": 1, "score": 0.8}, {"id": 0, "score": 0.2}]}),
        )

        result = StructuredRankingClient(api, "gpt-test").rank_with_scores(
            "query", ["first", "second"], [None, 0.8]
        )

        self.assertEqual(result.order, [1, 0])
        self.assertEqual(result.scores, [0.2, 0.8])
        request = api.responses.create.call_args.kwargs
        schema = request["text"]["format"]["schema"]
        score_schema = schema["properties"]["results"]["items"]["properties"]["score"]
        self.assertEqual(score_schema["enum"], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        request_input = json.loads(request["input"])
        self.assertEqual(request_input["allowed_scores"], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        self.assertEqual(request_input["documents"][1]["existing_score"], 0.8)
        self.assertIn("immutable anchor", request["instructions"])

    def test_retries_changed_existing_score_then_rejects(self) -> None:
        api = Mock()
        api.responses.create.return_value = SimpleNamespace(
            status="completed",
            output_text='{"results":[{"id":0,"score":0.8},{"id":1,"score":0.4}]}',
        )

        with self.assertRaises(InvalidScoreError):
            StructuredRankingClient(api, "gpt-test").rank_with_scores(
                "query", ["first", "second"], [0.6, None]
            )

        self.assertEqual(api.responses.create.call_count, 2)

    def test_requests_continuous_scores_and_preserves_exact_anchors(self) -> None:
        api = Mock()
        api.responses.create.return_value = SimpleNamespace(
            status="completed",
            output_text='{"results":[{"id":1,"score":0.76543},{"id":0,"score":0.63}]}',
        )

        result = StructuredRankingClient(api, "gpt-test").rank_with_scores(
            "query",
            ["first", "second"],
            [None, 0.76543],
            user="user-1",
            continuous_scores=True,
        )

        self.assertEqual(result.order, [1, 0])
        self.assertEqual(result.scores, [0.63, 0.76543])
        request = api.responses.create.call_args.kwargs
        self.assertTrue(request["text"]["format"]["strict"])
        self.assertFalse(request["store"])
        self.assertNotEqual(request["safety_identifier"], "user-1")
        schema = request["text"]["format"]["schema"]
        self.assertEqual(
            schema["properties"]["results"]["items"]["properties"]["score"],
            {"type": "number"},
        )
        request_input = json.loads(request["input"])
        self.assertNotIn("allowed_scores", request_input)
        self.assertEqual(request_input["score_range"], {"minimum": 0.0, "maximum": 1.0})
        self.assertEqual(request_input["documents"][1]["existing_score"], 0.76543)
        self.assertIn("immutable anchor", request["instructions"])
        self.assertIn("intermediate values", request["instructions"])

    def test_continuous_scores_accept_endpoints_and_all_zero_scores(self) -> None:
        for scores in ([0.0, 1.0], [0.0, 0.0]):
            with self.subTest(scores=scores):
                api = Mock()
                api.responses.create.return_value = SimpleNamespace(
                    status="completed",
                    output_text=json.dumps(
                        {"results": [{"id": 1, "score": scores[1]}, {"id": 0, "score": scores[0]}]}
                    ),
                )

                result = StructuredRankingClient(api, "gpt-test").rank_with_scores(
                    "query", ["first", "second"], [None, None], continuous_scores=True
                )

                self.assertEqual(result.scores, scores)

    def test_continuous_scores_reject_invalid_values_after_retry(self) -> None:
        for score in (
            -0.01,
            1.01,
            float("nan"),
            float("inf"),
            -float("inf"),
            True,
            "0.73",
            None,
            10**400,
        ):
            with self.subTest(score=score):
                api = Mock()
                api.responses.create.return_value = SimpleNamespace(
                    status="completed",
                    output_text=json.dumps({"results": [{"id": 0, "score": score}]}),
                )

                with self.assertRaises(InvalidScoreError):
                    StructuredRankingClient(api, "gpt-test").rank_with_scores(
                        "query", ["first"], [None], continuous_scores=True
                    )

                self.assertEqual(api.responses.create.call_count, 2)

    def test_continuous_scores_reject_invalid_rankings_and_changed_anchors(self) -> None:
        for results, anchors in (
            ([{"id": 0, "score": 0.73}, {"id": 0, "score": 0.63}], [None, None]),
            ([{"id": 0, "score": 0.73}], [None, None]),
            ([{"id": 0, "score": 0.63}, {"id": 1, "score": 0.73}], [None, None]),
            ([{"id": 0, "score": 0.73}, {"id": 1, "score": 0.63}], [0.731, None]),
        ):
            with self.subTest(results=results, anchors=anchors):
                api = Mock()
                api.responses.create.return_value = SimpleNamespace(
                    status="completed", output_text=json.dumps({"results": results})
                )

                with self.assertRaises(InvalidScoreError):
                    StructuredRankingClient(api, "gpt-test").rank_with_scores(
                        "query", ["first", "second"], anchors, continuous_scores=True
                    )

                self.assertEqual(api.responses.create.call_count, 2)

    def test_six_level_mode_still_rejects_intermediate_scores(self) -> None:
        api = Mock()
        api.responses.create.return_value = SimpleNamespace(
            status="completed", output_text='{"results":[{"id":0,"score":0.73}]}'
        )

        with self.assertRaises(InvalidScoreError):
            StructuredRankingClient(api, "gpt-test").rank_with_scores("query", ["first"], [None])

        self.assertEqual(api.responses.create.call_count, 2)

    def test_rejects_scores_that_increase_in_ranking_order(self) -> None:
        api = Mock()
        api.responses.create.return_value = SimpleNamespace(
            status="completed",
            output_text='{"results":[{"id":0,"score":0.2},{"id":1,"score":0.8}]}',
        )

        with self.assertRaises(InvalidScoreError):
            StructuredRankingClient(api, "gpt-test").rank_with_scores(
                "query", ["first", "second"], [None, None]
            )


class CreateResponsesClientTests(unittest.TestCase):
    @patch("models.rerank.responses_client.OpenAI")
    def test_creates_openai_client(self, openai: Mock) -> None:
        create_responses_client(
            {
                "service": "openai",
                "api_key": "secret",
                "openai_base_url": "https://api.openai.com/v1",
            },
            "gpt-test",
        )

        openai.assert_called_once_with(
            api_key="secret",
            base_url="https://api.openai.com/v1",
            max_retries=1,
        )

    @patch("models.rerank.responses_client.AzureOpenAI")
    def test_creates_azure_client_for_dated_endpoint(self, azure_openai: Mock) -> None:
        create_responses_client(
            {
                "service": "azure_openai",
                "api_key": "secret",
                "azure_endpoint": "https://example.openai.azure.com",
                "azure_api_version": "2025-04-01-preview",
            },
            "deployment-name",
        )

        azure_openai.assert_called_once_with(
            api_key="secret",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2025-04-01-preview",
            max_retries=1,
        )

    @patch("models.rerank.responses_client.OpenAI")
    def test_uses_openai_client_for_azure_v1_endpoint(self, openai: Mock) -> None:
        create_responses_client(
            {
                "service": "azure_openai",
                "api_key": "secret",
                "azure_endpoint": "https://example.openai.azure.com/openai/v1",
            },
            "deployment-name",
        )

        openai.assert_called_once_with(
            api_key="secret",
            base_url="https://example.openai.azure.com/openai/v1/",
            max_retries=1,
        )


if __name__ == "__main__":
    unittest.main()
