import logging
from collections.abc import Mapping

from dify_plugin import ModelProvider
from dify_plugin.entities.model import ModelType
from dify_plugin.errors.model import CredentialsValidateFailedError

logger = logging.getLogger(__name__)


class FakeLlmModelProvider(ModelProvider):
    def validate_provider_credentials(self, credentials: Mapping) -> None:
        pass
