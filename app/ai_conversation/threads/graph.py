from typing import Any, List
from uuid import UUID
from fastapi import HTTPException
from langchain_core.documents import Document
from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
    BaseMessage,
    SystemMessage,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from app.ai_conversation.ai_conversation import (
    get_connection_pool,
    get_postgres_checkpointer,
)
from app.ai_conversation.assistants.models import WrappedAssistant
from app.ai_conversation.assistants.service import get_generic_assistant
from app.ai_conversation.entities.thread import Thread
from app.ai_conversation.file_handling.vectorstore import get_chroma
from langchain_core.runnables import RunnableConfig
from app.ai_conversation.threads.service import (
    create_thread,
    delete_thread,
    list_threads,
    get_thread,
)
from app.routes.utils import select_model
from langserve.serialization import WellKnownLCSerializer
from app.ai_conversation.threads.chat_namer import chain as chat_namer_chain
import json
import datetime

rag_template = SystemMessagePromptTemplate.from_template(
    """You are an assistant for question-answering tasks. Use the following pieces of retrieved context and the role below to answer the question.
Always add citations whenever possible in the form of †[document_id]† at the end of a paragraph, inside the text, or at the end of the answer.
When you use information from multiple documents, cite them in the order they appear, like this: †[document_id_1]† †[document_id_2]†.
Even when the answer is based on general knowledge or reasoning, include citations from relevant documents whenever applicable.
If you don't know the answer, just say that you don't know. Keep the answer concise and always respond in the user's language.

Context: {context}

------

Role: {role}

------
**Cite all references you use!**"""
)

prompt = ChatPromptTemplate.from_messages(
    [
        MessagesPlaceholder(variable_name="conversation"),
        MessagesPlaceholder(variable_name="system_messages"),
        MessagesPlaceholder(variable_name="question"),
    ]
)


GraphState = MessagesState


def format_docs(docs: List[Document]):
    return "\n\n".join(f"†[{doc.metadata['id']}]†:\n{doc.page_content}" for doc in docs)


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


async def _make_content_filter(state: GraphState, config: RunnableConfig):
    assistant: WrappedAssistant = config["configurable"]["assistant"]
    ids = set([str(f.content_id) for _, f in assistant.files])
    messages: list[BaseMessage] = state["messages"]
    message_ids = set(
        [e for m in messages for e in m.additional_kwargs.get("attachments", [])]
    )
    # files to content ids
    async with get_connection_pool().acquire() as conn:
        rows = await conn.fetch(
            """SELECT content_id
               FROM uploaded_file
               WHERE account_id = $1 AND id IN (SELECT unnest($2::uuid[]));""",
            config["configurable"]["user_info"]["id"],
            list(message_ids),
        )
    for row in rows:
        ids.add(str(row["content_id"]))
    if len(ids) < 1:
        return None
    return {
        "ref_id": {"$in": list(ids)},
    }


async def _apply_file_names(documents: list[Document], account_id: UUID):
    async with get_connection_pool().acquire() as conn:
        rows = await conn.fetch(
            """SELECT content_id, name
               FROM uploaded_file
               WHERE account_id = $1 AND content_id IN (SELECT unnest($2::uuid[]));""",
            account_id,
            list(set(d.metadata["ref_id"] for d in documents)),
        )

    for row in rows:
        content_id = str(row["content_id"])
        for e in filter(lambda x: x.metadata["ref_id"] == content_id, documents):
            e.metadata["name"] = row["name"]


async def _rag_for_last_message(state: GraphState, config: RunnableConfig):
    messages = state["messages"]
    input = messages[-1]
    if input.type != "human":
        raise ValueError("Last message must be human")
    content_filter = await _make_content_filter(state, config)
    if content_filter:
        documents = (
            await get_chroma()
            .as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "score_threshold": 0.4,
                    "k": 7,
                    "filter": content_filter,
                },
            )
            .ainvoke(_message_to_str(input))
        )
    else:
        documents = []
    if len(documents) < 1:
        return {"messages": []}
    # add names as metadata
    await _apply_file_names(documents, config["configurable"]["user_info"]["id"])
    message = ToolMessage(
        content="", artifact={"documents": documents}, tool_call_id="rag"
    )
    return {"messages": [message]}


def _filter_messages(messages: list[BaseMessage]):
    return list(
        filter(
            lambda x: not x.type == "tool" or x.tool_call_id not in ["rag"],
            messages,
        )
    )


async def _make_answer(state: GraphState, config: RunnableConfig):
    assistant: WrappedAssistant = config["configurable"]["assistant"]
    messages = state["messages"]
    input = messages[-1]
    end = -1
    system_message = None
    if input.type == "tool":
        system_message = rag_template.format(
            context=format_docs(input.artifact["documents"]),
            role=assistant.assistant.instruction,
        )
        input = messages[-2]
        end = -2
    else:
        system_message = SystemMessage(content=assistant.assistant.instruction)
    conversation = _filter_messages(messages[:end])
    llm = select_model(None, config)
    chain = prompt | llm
    response = await chain.ainvoke(
        {
            "question": [input],
            "conversation": conversation,
            "system_messages": [system_message],
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
        room_id = configurable["room"]["id"]
        user_id = configurable["user_info"]["id"]
        return await list_threads(room_id, user_id)

    async def delete_chat(self, config: RunnableConfig, thread_id: UUID) -> None:
        configurable = config["configurable"]
        room_id = configurable["room"]["id"]
        user_id = configurable["user_info"]["id"]
        await delete_thread(thread_id, room_id, user_id)

    async def new_chat(
        self, config: RunnableConfig, input: HumanMessage, assistant_id: UUID
    ) -> Any:
        configurable = config["configurable"]
        room_id = configurable["room"]["id"]
        user_id = configurable["user_info"]["id"]
        input = self._strip_information(input)
        assistant = await get_generic_assistant(config, assistant_id)
        if not assistant:
            raise HTTPException(
                status_code=404,
                detail="Assistant not found",
            )
        configurable["assistant"] = assistant
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
        self,
        config: RunnableConfig,
        thread_id: UUID,
        assistant_id: UUID,
        input: HumanMessage | None,
    ) -> Any:
        configurable = config["configurable"]
        room_id = configurable["room"]["id"]
        user_id = configurable["user_info"]["id"]
        input = self._strip_information(input)
        assistant = await get_generic_assistant(config, assistant_id)
        if not assistant:
            raise HTTPException(
                status_code=404,
                detail="Assistant not found",
            )
        configurable["assistant"] = assistant
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

    def _strip_information(self, message: HumanMessage):
        if not message:
            return None
        additional = message.additional_kwargs
        return HumanMessage(
            content=message.content,
            additional_kwargs={
                "attachments": additional.get("attachments", []),
            },
        )


graph_wrapper: GraphWrapper = None


def get_graph_wrapper() -> GraphWrapper:
    global graph_wrapper
    if graph_wrapper is None:
        graph_wrapper = GraphWrapper(
            builder.compile(checkpointer=get_postgres_checkpointer())
        )
    return graph_wrapper
