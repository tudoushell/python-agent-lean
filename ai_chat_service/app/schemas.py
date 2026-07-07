from pydantic import BaseModel, Field, ConfigDict, field_validator


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户输入问题")
    scene: str | None = Field(default=None, description="Prompt 场景")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="AI生成的回答")


class SummaryResponse(BaseModel):
    """
        model_config = ConfigDict(
              extra="ignore",              # 多余字段忽略
              extra="forbid",              # 多余字段报错
              extra="allow",               # 多余字段允许保留
              frozen=True,                 # 模型不可修改
              from_attributes=True,        # 支持从对象属性读取，类似 v1 的 orm_mode=True
              populate_by_name=True,       # 允许用字段名填充 alias 字段
              str_strip_whitespace=True,   # 字符串去空格
              validate_assignment=True,    # 修改字段时也校验
          )
    """
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(..., min_length=1, description="一句话总结，不能使用占位符")
    keyPoints: list[str] = Field(..., min_length=1, description="核心要点列表，不能使用占位符")
    suggestions: list[str] = Field(..., min_length=1, description="建议列表，不能使用占位符")
    # summary: str = Field(..., description="一句话总结")
    # keyPoints: list[str] = Field(..., description="核心要点列表")
    # suggestions: list[str] = Field(..., description="建议列表")
