from fastapi import FastAPI
from starlette.responses import StreamingResponse

from ai_chat_service.app.core.config import get_settings
from ai_chat_service.app.core.exception import global_exception_handler, app_exception_handler, AppException
from ai_chat_service.app.core.logging_config import setup_logging
from ai_chat_service.app.llm_service import LLMService
from ai_chat_service.app.middleware.request_log import RequestLogMiddleware
from ai_chat_service.app.schemas import ChatResponse, SummaryResponse

api = FastAPI(
    title="AI Chat Service API"
)
# 获取配置信息
settings = get_settings()
# 设置日志
setup_logging(settings.log_level)
# 设置
api.add_middleware(RequestLogMiddleware)
api.add_exception_handler(AppException, app_exception_handler)
api.add_exception_handler(Exception, global_exception_handler)

llm_service = LLMService()


@api.get("/health")
def health_check():
    return {"status": "ok"}


@api.get("/chat")
def chat(message: str):
    answer = llm_service.chat(message)
    return ChatResponse(answer=answer)


@api.get("/chat2")
def chat_stream(message: str):
    def event_generator():
        try:
            for chunk in llm_service.stream_chat(message):
                yield chunk
        except Exception as e:
            yield f"data: {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@api.get("/chat-scene")
def chat_with_scene(message: str, scene: str | None = None):
    def event_generator():
        try:
            for chunk in llm_service.stream_chat_by_scene(message, scene):
                yield chunk
        except Exception as e:
            yield f"data: {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@api.get("/chat-summary", response_model=SummaryResponse)
def summary(message: str):
    return llm_service.summary(message)


@api.get("/chat-summary-schema", response_model=SummaryResponse)
def summary(message: str):
    return llm_service.summary_structured(message)


@api.get("/chat-mem")
def chat_with_memory(message: str, scene: str | None = None, id: str | None = None):
    def event_generator():
        try:
            for chunk in llm_service.chat_stream_with_memory(message, scene, id):
                yield chunk
        except Exception as e:
            yield f"data: {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
