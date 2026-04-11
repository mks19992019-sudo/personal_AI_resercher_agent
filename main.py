from fastapi import FastAPI
from graph import work_flow
from langchain_core.messages import HumanMessage
from pydantic import AliasChoices, BaseModel, Field


app = FastAPI()


class ChatRequest(BaseModel):
    user: str = Field(validation_alias=AliasChoices("user", "message"))
    thread_id: str = Field(validation_alias=AliasChoices("thread_id", "threadId"))


def _run_chat(user: str, thread_id: str) -> dict[str, str]:
    initial_state = {"messages": [HumanMessage(content=user)], "summary": ""}
    config = {"configurable": {"thread_id": thread_id}}

    answer = work_flow.invoke(initial_state, config=config)

    return {"response": answer["messages"][-1].content}


@app.post("/chat")
def chat(request: ChatRequest):
    return _run_chat(request.user, request.thread_id)

    
