import logging
from openai import OpenAI
from typing import Generator

from pydantic import ValidationError

from ai_chat_service.app.core.config import Settings
from ai_chat_service.app.core.exception import AppException
from ai_chat_service.app.prompt.prompt_service import PromptService
from ai_chat_service.app.schemas import SummaryResponse

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.settings = Settings()
        self.prompt_service = PromptService()
        self.client = OpenAI(base_url=self.settings.base_url, api_key=self.settings.api_key)

    def chat(self, message: str) -> str:
        logger.info("calling llm, model=%s", self.settings.model_name)
        response = self.client.responses.create(
            model=self.settings.model_name,
            instructions="回答简洁",
            input=message
        )
        return response.output_text

    def stream_chat(self, message: str) -> Generator[str, None, None]:
        stream = self.client.responses.create(
            model=self.settings.model_name,
            input=message,
            stream=True
        )
        for chunk in stream:
            if chunk.type == 'response.output_text.delta':
                yield chunk.delta

    def stream_chat_by_scene(self, message:str, scene: str|None = None) -> Generator[str, None, None]:
        if not message or not message.strip():
            raise AppException(
                message="消息不能为空",
                code="INVALID_MESSAGE",
                status_code=400,
            )
        prompt_template = self.prompt_service.get_template(scene)
        user_prompt = self.prompt_service.render_user_prompt(prompt_template.user_template, message)

        logger.info(
            "stream calling llm, model=%s, scene=%s",
            self.settings.default_scene,
            prompt_template.scene,
        )

        stream = self.client.responses.create(
            model=self.settings.model_name,
            instructions=prompt_template.system_prompt,
            input=user_prompt,
            stream=True
        )

        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta

    #汇总聊天，返回指定结构
    def summary(self, message: str) -> SummaryResponse:
        if not message or not message.strip():
            raise AppException(
                message="消息不能为空",
                code="INVALID_MESSAGE",
                status_code=400,
            )
        prompt_template = self.prompt_service.get_template("summary")
        user_prompt = self.prompt_service.render_user_prompt(prompt_template.user_template, message)

        logger.info(
            "calling llm structured summary, model=%s, scene=%s",
            self.settings.model_name,
            prompt_template.scene,
        )

        response = self.client.responses.create(
            model=self.settings.model_name,
            instructions=prompt_template.system_prompt,
            input=user_prompt,
            text={
                "format" : {
                    "type": "json_schema",
                    "name": "summary_response",
                    "schema": SummaryResponse.model_json_schema(),
                    "strict": True
                }
            }
        )
        try:
            return SummaryResponse.model_validate_json(response.output_text)
        except ValidationError as e:
            logger.error("summary validation error: %s", e)
            raise AppException(
                message="模型返回结构解析失败",
                code="INVALID_MESSAGE",
                status_code=400,
            )
