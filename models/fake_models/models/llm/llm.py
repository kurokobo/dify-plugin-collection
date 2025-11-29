import logging
from collections.abc import Generator
from typing import Optional, Union
import re
import time

from dify_plugin import LargeLanguageModel
from dify_plugin.entities import I18nObject
from dify_plugin.errors.model import (
    CredentialsValidateFailedError,
)
from dify_plugin.entities.model import (
    AIModelEntity,
    FetchFrom,
    ModelType,
)
from dify_plugin.entities.model.llm import (
    LLMResult,
)
from dify_plugin.entities.model.message import (
    PromptMessage,
    PromptMessageTool,
)
from dify_plugin.entities.model.llm import (
    LLMMode,
    LLMResult,
    LLMResultChunk,
    LLMResultChunkDelta,
)
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    AudioPromptMessageContent,
    ImagePromptMessageContent,
    PromptMessage,
    PromptMessageContentType,
    PromptMessageTool,
    SystemPromptMessage,
    TextPromptMessageContent,
    ToolPromptMessage,
    UserPromptMessage,
)

from dify_plugin.errors.model import (
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)

import pprint

import logging
from dify_plugin.config.logger_format import plugin_logger_handler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class FakeLlmLargeLanguageModel(LargeLanguageModel):
    """
    Model class for fake_models large language model.
    """

    def validate_credentials(self, model: str, credentials: dict) -> None:
        pass

    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        """
        Invoke large language model

        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param tools: tools for tool calling
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        :return: full response or stream response chunk generator result
        """
        if model == "echo":
            yield from self._handle_echo_response(
                model=model,
                credentials=credentials,
                prompt_messages=prompt_messages,
                model_parameters=model_parameters,
                tools=tools,
                stop=stop,
                stream=stream,
                user=user,
            )
        elif model == "fixed":
            yield from self._handle_fixed_response(
                model=model,
                credentials=credentials,
                prompt_messages=prompt_messages,
                model_parameters=model_parameters,
                tools=tools,
                stop=stop,
                stream=stream,
                user=user,
            )
        elif model == "hello":
            yield from self._handle_hello_response(
                model=model,
                credentials=credentials,
                prompt_messages=prompt_messages,
                model_parameters=model_parameters,
                tools=tools,
                stop=stop,
                stream=stream,
                user=user,
            )
        else:
            raise InvokeBadRequestError(f"Unknown model: {model}")

    def _generate_response(
        self,
        response_message: str,
        model: str,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        stream: bool = True,
    ) -> Generator:
        """
        Generate response chunks or full response

        :param response_message: the response message to return
        :param model: model name
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param stream: whether to stream the response
        :return: generator of LLMResultChunk or LLMResult
        """
        # Get delay and interval from model_parameters
        delay_ms = model_parameters.get("delay_ms", 0)
        interval_ms = model_parameters.get("interval_ms", 0)

        # Apply initial delay before starting response
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

        if stream:
            fake_chunks = re.findall(r"[^ \n]+[ \n]*|^[ \n]+", response_message)
            for idx, chunk in enumerate(fake_chunks):
                if idx > 0 and interval_ms > 0:
                    time.sleep(interval_ms / 1000.0)
                yield LLMResultChunk(
                    model=model,
                    prompt_messages=prompt_messages,
                    delta=LLMResultChunkDelta(
                        index=idx,
                        message=AssistantPromptMessage(
                            content=chunk,
                            tool_calls=[],
                        ),
                    ),
                )
            yield LLMResultChunk(
                model=model,
                prompt_messages=prompt_messages,
                delta=LLMResultChunkDelta(
                    index=len(fake_chunks),
                    message=AssistantPromptMessage(
                        content="",
                        tool_calls=[],
                    ),
                    finish_reason="stop",
                ),
            )
        else:
            yield LLMResult(
                model=model,
                prompt_messages=prompt_messages,
                message=AssistantPromptMessage(
                    content=response_message,
                    tool_calls=[],
                ),
            )

    def _handle_echo_response(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Generator:
        """
        Handle echo model response - echoes back the user's last message
        """
        repeat = model_parameters.get("repeat", 1)
        for msg in reversed(prompt_messages):
            if isinstance(msg, UserPromptMessage):
                if isinstance(msg.content, str):
                    response_message = msg.content * repeat
                elif isinstance(msg.content, list):
                    text_contents = [c.data for c in msg.content if isinstance(c, TextPromptMessageContent)]
                    if text_contents:
                        response_message = " ".join(text_contents) * repeat
                break
        yield from self._generate_response(
            response_message=response_message,
            model=model,
            prompt_messages=prompt_messages,
            model_parameters=model_parameters,
            stream=stream,
        )

    def _handle_fixed_response(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Generator:
        """
        Handle fixed model response - returns a fixed response from model_parameters
        """
        response_message = model_parameters.get("response", "Hello, World!")
        yield from self._generate_response(
            response_message=response_message,
            model=model,
            prompt_messages=prompt_messages,
            model_parameters=model_parameters,
            stream=stream,
        )

    def _handle_hello_response(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Generator:
        """
        Handle hello model response - returns a fixed response
        """
        response_message = "Hello, Dify!"
        yield from self._generate_response(
            response_message=response_message,
            model=model,
            prompt_messages=prompt_messages,
            model_parameters=model_parameters,
            stream=stream,
        )

    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
    ) -> int:
        return 0

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        return {
            InvokeConnectionError: [InvokeConnectionError],
            InvokeServerUnavailableError: [InvokeServerUnavailableError],
            InvokeRateLimitError: [InvokeRateLimitError],
            InvokeAuthorizationError: [InvokeAuthorizationError],
            InvokeBadRequestError: [InvokeBadRequestError],
        }
