import atexit
import os
from langchain_core.messages import HumanMessage , RemoveMessage 
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from psycopg_pool import ConnectionPool

from langchain_core.messages.utils import trim_messages , count_tokens_approximately



load_dotenv()

model = ChatGroq(model="openai/gpt-oss-120b")

agent = create_react_agent(
    model=model,
    tools=[],
    prompt=(
        "You are a helpful assistant that answers questions based on the given "
        "context. If you don't know the answer, say you don't know. Always use "
        "the provided tools if they are relevant to the question."
    ),
)



class Chatstate(MessagesState):
    summary: str

def summery_agent(state:Chatstate):

    existing_summary = state['summary']

    if existing_summary:
        prompt = (
            f"Existing summary:\n{existing_summary}\n\n"
            "Extend the summary using the new conversation above."
        )
    else:
        prompt = "Summarize the conversation above."

    messages_for_summary = state["messages"] + [
        HumanMessage(content=prompt)
    ]

    response = model.invoke(messages_for_summary)

    # Keep only last 2 messages verbatim
    messages_to_delete = state["messages"][:-2]

    return {
        "summary": response.content,
        "messages": [RemoveMessage(id=m.id) for m in messages_to_delete],

    }




def AI_agent(state: Chatstate):

    msg = []
    # if summery exit then 
    if state.get("summary"):
        msg.append({
            "role": "system",
            "content": f"Conversation summary:\n{state['summary']}"
        })

    msg.extend(state['messages'])

    
    result = agent.invoke({"messages": msg})

    return {"messages": result["messages"], "summary": state.get("summary", "")}


def should_summeries(state:Chatstate):
    return len(state["messages"]) > 6

graph = StateGraph(Chatstate)

graph.add_node("AI_agent", AI_agent)
graph.add_node("summery",summery_agent)



graph.add_edge(START, "AI_agent")

graph.add_conditional_edges("AI_agent", should_summeries,{
    True: "summery",
    False:"__end__"

})



DB_URI = os.getenv("DB_URI", "postgresql://postgres:postgres@localhost:5442/postgres")

connection_pool = ConnectionPool(
    conninfo=DB_URI,
    min_size=1,
    max_size=5,
    open=True,
    kwargs={"autocommit": True, "prepare_threshold": 0},
)
# for closing the conection
atexit.register(connection_pool.close)

checkpointer = PostgresSaver(connection_pool)

checkpointer.setup()

work_flow = graph.compile(checkpointer=checkpointer)












