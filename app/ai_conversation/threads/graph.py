from typing import Any, List
from uuid import UUID
from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from app.ai_conversation.ai_conversation import get_postgres_checkpointer
from app.ai_conversation.entities.thread import Thread
from app.ai_conversation.file_handling.vectorstore import get_chroma
from langchain_core.runnables import RunnableConfig
from app.ai_conversation.threads.service import create_thread, list_threads, get_thread
from app.routes.utils import select_model
from langserve.serialization import WellKnownLCSerializer
from app.ai_conversation.threads.chat_namer import chain as chat_namer_chain
import json
import datetime

prompt = ChatPromptTemplate.from_messages(
    [
        MessagesPlaceholder(variable_name="conversation"),
        SystemMessagePromptTemplate.from_template(
            """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question.
            Add citations in the form of †[document_id, metadata_as_json]† at the end of a paragraph, inside the text or at the end of the answer when you use information from a document.
            When you use more than one document, add the citations in the order you use them.
            If you don't know the answer, just say that you don't know. Keep the answer concise and always answer in the language of the user.

            Context: {context}"""
        ),
        MessagesPlaceholder(variable_name="additional_prompt", optional=True),
        MessagesPlaceholder(variable_name="question"),
    ]
)


GraphState = MessagesState


def format_docs(docs: List[Document]):
    unwanted_keys = ["ref_id", "id"]
    return "\n\n".join(
        f"†[{doc.metadata['id']}, { {x: doc.metadata[x] for x in doc.metadata if x not in unwanted_keys} }]†:\n{doc.page_content}"
        for doc in docs
    )


def _message_to_str(message: HumanMessage):
    if isinstance(message.content, str):
        return message.content
    text = ""
    for x in message.content:
        if isinstance(x, str):
            text += x + "\n"
        elif isinstance(x, dict) and "text" in x:
            text += x["text"] + "\n"
    return text


async def _rag_for_last_message(state: GraphState):
    messages = state["messages"]
    input = messages[-1]
    if input.type != "human":
        raise ValueError("Last message must be human")
    documents = await get_chroma().as_retriever().ainvoke(_message_to_str(input))
    message = ToolMessage(
        content="", artifact={"documents": documents}, tool_call_id="rag"
    )
    return {"messages": [message]}


def _filter_docs(docs: list[Document]):
    return list(filter(lambda x: x.type not in ["rag"], docs))


async def _make_answer(state: GraphState, config: RunnableConfig):
    messages = state["messages"]
    documents = messages[-1].artifact["documents"]
    input = messages[-2]
    conversation = _filter_docs(messages[:-2])
    llm = select_model(None, config)
    chain = prompt | llm
    response = await chain.ainvoke(
        {
            "question": [input],
            "context": format_docs(documents),
            "conversation": conversation,
            "additional_prompt": [],
        }
    )
    return {"messages": [response]}


builder = StateGraph(GraphState)
builder.add_node("rag", _rag_for_last_message)
builder.add_node("answer", _make_answer)
builder.add_edge(START, "rag")
builder.add_edge("rag", "answer")
builder.add_edge("answer", END)


class Encoding(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return str(obj)
        return super().default(obj)


class GraphWrapper:
    graph: CompiledStateGraph
    serializer: WellKnownLCSerializer

    def __init__(self, graph: CompiledStateGraph):
        self.graph = graph
        self.serializer = WellKnownLCSerializer()

    async def list_chats(self, config: RunnableConfig) -> list[Thread]:
        configurable = config["configurable"]
        room_id = configurable["room_id"]
        user_id = configurable["user_info"]["id"]
        return await list_threads(room_id, user_id)

    async def new_chat(self, input: HumanMessage, config: RunnableConfig) -> Any:
        configurable = config["configurable"]
        room_id = UUID(configurable["room_id"])
        user_id = configurable["user_info"]["id"]
        name = await chat_namer_chain.ainvoke({"messages": [input]}, config)
        thread = await create_thread(
            room_id,
            user_id,
            name,
        )
        yield {
            "data": json.dumps(thread.__dict__, cls=Encoding),
            "event": "thread_created",
        }
        config["configurable"]["thread_id"] = str(thread.id)
        async for event in self._call_graph({"messages": input}, config):
            yield event

    async def continue_chat(
        self, input: HumanMessage | None, thread_id: UUID, config: RunnableConfig
    ) -> Any:
        configurable = config["configurable"]
        room_id = UUID(configurable["room_id"])
        user_id = configurable["user_info"]["id"]
        thread = await get_thread(thread_id, room_id, user_id)
        if not thread:
            raise HTTPException(
                status_code=404,
                detail="Thread not found",
            )
        config["configurable"]["thread_id"] = str(thread.id)
        state = await self.graph.aget_state(config)
        print(state.next)
        # assert message and state
        async for event in self._call_graph({"messages": [input]}, config):
            yield event

    async def get_chat_messages(self, thread_id: UUID, config: RunnableConfig) -> Any:
        configurable = config["configurable"]
        user_id = configurable["user_info"]["id"]
        thread = await get_thread(thread_id, None, user_id)
        if not thread:
            raise HTTPException(
                status_code=404,
                detail="Thread not found",
            )
        config["configurable"]["thread_id"] = str(thread.id)
        state = await self.graph.aget_state(config)
        return state.values["messages"] if state and "messages" in state.values else []

    async def _call_graph(self, input: dict, config: RunnableConfig) -> Any:
        async for event in self.graph.astream(
            input,
            config,
            stream_mode=["messages", "values"],
        ):
            if event[0] == "values":
                yield {
                    "data": self.serializer.dumps(event[1]).decode("utf-8"),
                    "event": "value",
                }
            else:
                yield {
                    "data": self.serializer.dumps(event[1][0]).decode("utf-8"),
                    "event": "message",
                }
        yield {"event": "end"}


graph_wrapper: GraphWrapper = None


def get_graph_wrapper() -> GraphWrapper:
    global graph_wrapper
    if graph_wrapper is None:
        graph_wrapper = GraphWrapper(
            builder.compile(checkpointer=get_postgres_checkpointer())
        )
    return graph_wrapper
