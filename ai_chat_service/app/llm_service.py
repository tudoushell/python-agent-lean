import json
import logging
from typing import Generator

from openai import OpenAI
from pydantic import ValidationError

from ai_chat_service.app.core.config import Settings
from ai_chat_service.app.core.exception import AppException
from ai_chat_service.app.core.json_utils import extract_json_object
from ai_chat_service.app.prompt.prompt_service import PromptService
from ai_chat_service.app.schemas import SummaryResponse
from ai_chat_service.app.services.memory_service import MemoryService
from ai_chat_service.app.tools.order_tools import ORDER_TOOLS_SCHEMA, call_order_tool

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.settings = Settings()
        self.prompt_service = PromptService()
        self.client = OpenAI(
            base_url=self.settings.base_url, api_key=self.settings.api_key
        )
        self.memory_service = MemoryService(max_messages=20)

    def chat(self, message: str) -> str:
        logger.info("calling llm, model=%s", self.settings.model_name)
        response = self.client.responses.create(
            model=self.settings.model_name, instructions="回答简洁", input=message
        )
        return response.output_text

    def stream_chat(self, message: str) -> Generator[str, None, None]:
        stream = self.client.responses.create(
            model=self.settings.model_name, input=message, stream=True
        )
        for chunk in stream:
            if chunk.type == "response.output_text.delta":
                yield chunk.delta

    def stream_chat_by_scene(
            self, message: str, scene: str | None = None
    ) -> Generator[str, None, None]:
        if not message or not message.strip():
            raise AppException(
                message="消息不能为空",
                code="INVALID_MESSAGE",
                status_code=400,
            )
        prompt_template = self.prompt_service.get_template(scene)
        user_prompt = self.prompt_service.render_user_prompt(
            prompt_template.user_template, message
        )

        logger.info(
            "stream calling llm, model=%s, scene=%s",
            self.settings.default_scene,
            prompt_template.scene,
        )

        stream = self.client.responses.create(
            model=self.settings.model_name,
            instructions=prompt_template.system_prompt,
            input=user_prompt,
            stream=True,
        )

        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta

    # 汇总聊天，返回指定结构
    def summary(self, message: str) -> SummaryResponse:
        """
         汇总聊天返回，指定结构
        :param message:
        :return:
        """
        if not message or not message.strip():
            raise AppException(
                message="消息不能为空",
                code="INVALID_MESSAGE",
                status_code=400,
            )
        prompt_template = self.prompt_service.get_template("summary")
        user_prompt = self.prompt_service.render_user_prompt(
            prompt_template.user_template, message
        )

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
                "format": {
                    "type": "json_schema",
                    "name": "summary_response",
                    "schema": SummaryResponse.model_json_schema(),
                    "strict": True,
                }
            },
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

    def summary_structured(self, message: str) -> SummaryResponse:
        if not message or not message.strip():
            raise AppException(
                message="消息不能为空",
                code="INVALID_MESSAGE",
                status_code=400,
            )
        prompt_template = self.prompt_service.get_template("summary_schema")
        user_prompt = self.prompt_service.render_user_prompt(
            prompt_template.user_template, message
        )

        logger.info(
            "calling llm structured summary, model=%s, scene=%s",
            self.settings.model_name,
            prompt_template.scene,
        )

        first_output = self.client.responses.create(
            model=self.settings.model_name,
            instructions=prompt_template.system_prompt,
            input=user_prompt,
        )
        try:
            return self._parse_summary_output(first_output)
        except Exception as first_error:
            logger.warning(
                "first summary parse failed, retrying once, error: %s", first_error
            )

            retry_prompt = self._build_summary_retry_prompty(
                original_message=message,
                bad_output=first_error,
                error_message=str(first_error),
            )

            second_output = self._call_text(
                system_prompt=prompt_template.system_prompt, user_prompt=retry_prompt
            )
            try:
                return self._parse_summary_output(second_output)
            except Exception as second_error:
                logger.exception("summary parse failed after retry")
                raise AppException(
                    message="模型返回结构解析失败，请稍后重试",
                    code="STRUCTURED_OUTPUT_PARSE_ERROR",
                    status_code=500,
                ) from second_error

    def chat_stream_with_memory(
            self,
            message: str,
            scene: str | None = None,
            conversation_id: str | None = None,
    ) -> Generator[str, None, None]:
        """
         聊天带记忆功能
        :param message:
        :param scene:
        :param conversation_id:
        :return:
        """
        self._validate_message(message)
        conversation_id = self._validate_conversation_id(conversation_id)
        prompt_template = self.prompt_service.get_template(scene)
        user_prompt = self.prompt_service.render_user_prompt(
            prompt_template.user_template, message
        )

        history_message = self.memory_service.get_message(conversation_id)

        input_message = [*history_message, {"role": "user", "content": user_prompt}]

        stream = self.client.responses.create(
            model=self.settings.model_name,
            instructions=prompt_template.system_prompt,
            input=input_message,
            stream=True,
        )
        answer_parts: list[str] = []
        for event in stream:
            if event.type == "response.output_text.delta":
                answer_parts.append(event.delta)
                yield event.delta
        result_answer = "".join(answer_parts)

        self.memory_service.add_user_message(conversation_id, user_prompt)
        self.memory_service.add_assistant_message(conversation_id, result_answer)

        logger.info(
            f"conversation id: {conversation_id}, history_message: {self.memory_service.get_message(conversation_id)}"
        )

    def tool_chat(
            self, message: str, conversation_id: str | None = None
    ) -> Generator[str, None, Generator[str, None, None] | None]:
        """
         工具调用
        :param message:
        :param conversation_id:
        :return:
        """
        self._validate_message(message)
        conversation_id = self._validate_conversation_id(conversation_id)
        tool_prompt = self.prompt_service.get_template("tool_assistant")
        user_prompt = self.prompt_service.render_user_prompt(
            tool_prompt.user_template, message
        )
        history_messages = self.memory_service.get_message(conversation_id)
        input_message = [*history_messages, {"role": "user", "content": user_prompt}]

        logger.info(
            "calling llm with tools, model=%s, conversation_id=%s",
            self.settings.model_name,
            conversation_id,
        )

        response = self.client.responses.create(
            model=self.settings.model_name,
            instructions=tool_prompt.system_prompt,
            input=input_message,
            tools=ORDER_TOOLS_SCHEMA,
            tool_choice="auto",
            parallel_tool_calls=False,
        )

        # 如果模型没有调用工具，直接返回普通回答
        function_call = self._has_function_call(response)
        if function_call is None:
            answer = response.output_text
            self.memory_service.add_user_message(conversation_id, user_prompt)
            self.memory_service.add_assistant_message(conversation_id, answer)
            yield answer
            return
        # 有工具调用时，执行工具，把工具结果发回模型
        result: list[str] = []
        ai_answer = self._handle_tool_calls(input_message, response, tool_prompt.system_prompt)
        for e in ai_answer:
            result.append(e)
            yield e
        self.memory_service.add_user_message(conversation_id, user_prompt)
        self.memory_service.add_assistant_message(conversation_id, "".join(result))

    def _handle_tool_calls(self,
                           input_message: list,
                           first_response,
                           system_prompt: str) -> Generator[str, None, None]:
        next_input = [
            *input_message,
            *first_response.output,
        ]

        for item in first_response.output:
            if item.type != "function_call":
                continue
            # ResponseFunctionToolCall(arguments='{"order_id":"OD1001"}',
            # call_id='call_cs22vmkr', name='query_order',
            # type='function_call', id='fc_resp_111002_0', namespace=None, status='completed')
            logger.info(f"calling llm with tools, tool is {item.name}")
            tool_result = self._execute_tool_call(item)
            next_input.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": tool_result,
            })
        stream = self.client.responses.create(
            model=self.settings.model_name,
            instructions=system_prompt,
            input=next_input,
            tools=ORDER_TOOLS_SCHEMA,
            tool_choice="auto",
            parallel_tool_calls=False,
            stream=True,
        )
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta

    def _execute_tool_call(self, item) -> str:
        try:
            name = item.name
            arguments = json.loads(item.arguments)
        except Exception as e:
            return f"工具调用参数解析失败：{str(e)}"
        try:
            return call_order_tool(name=name, arguments=arguments)
        except Exception as e:
            logger.exception("execute tool failed")
            return f"工具执行失败：{str(e)}"

    def _has_function_call(self, response):
        for item in response.output:
            if item.type == "function_call":
                return item
        return None

    def _validate_conversation_id(self, conversation_id: str) -> str:
        if not conversation_id or not conversation_id.strip():
            return "1"
        return conversation_id

    def _validate_message(self, message: str):
        if not message or not message.strip():
            raise AppException(
                message="消息不能为空",
                code="INVALID_MESSAGE",
                status_code=400,
            )

    def _call_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.responses.create(
            model=self.settings.model_name,
            instructions=system_prompt,
            input=user_prompt,
        )
        return response.output_text

    def _parse_summary_output(self, output_text: str) -> SummaryResponse:
        data = extract_json_object(output_text)
        try:
            return SummaryResponse.model_validate(data)
        except ValidationError as e:
            raise AppException(
                message=f"模型返回 JSON 字段不符合要求：{e}",
                code="SUMMARY_SCHEMA_VALIDATE_ERROR",
                status_code=500,
            ) from e

    def _build_summary_retry_prompty(self,
                                     original_message: str,
                                     bad_output: str,
                                     error_message: str, ) -> str:
        return f"""
                    上一次输出不符合 JSON 结构要求，请重新生成。
                    
                    原始内容：
                    {original_message}
                    
                    上一次错误输出：
                    {bad_output}
                    
                    解析错误：
                    {error_message}
                    
                    请严格只返回如下 JSON 对象，不要 Markdown，不要代码块，不要解释：
                    
                    {{
                      "summary": "一句话总结",
                      "keyPoints": ["核心要点1", "核心要点2", "核心要点3"],
                      "suggestions": ["建议1", "建议2"]
                    }}
                """.strip()
