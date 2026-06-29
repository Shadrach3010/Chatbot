from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., description="User Input")
    system: str | None = Field(
        default="You are a helpful, concise assistant.",
        description="System behavior instruction"
    )

class ChatResponse(BaseModel):
    reply: str
    model: str
    tokens_in: int | None = None
    tokens_out: int | None = None
    