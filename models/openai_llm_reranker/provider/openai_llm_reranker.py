from collections.abc import Mapping

from dify_plugin import ModelProvider


class OpenAILLMRerankerProvider(ModelProvider):
    def validate_provider_credentials(self, credentials: Mapping) -> None:
        pass
