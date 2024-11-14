import os
import asyncpg
import chromadb
from chromadb.config import Settings
from app.ai_conversation.db import migrate
from app.ai_conversation.file_handling.vectorstore import set_chroma
from app.ai_conversation.file_handling.file_upload_processor import (
    remove_unreferenced_content,
    optimize_file_content,
)
from langchain_chroma import Chroma
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_huggingface import HuggingFaceEmbeddings


async_connection_pool = None
postgres_checkpointer = None
scheduler = None
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_connection_pool():
    global async_connection_pool
    return async_connection_pool


def get_postgres_checkpointer():
    global postgres_checkpointer
    return postgres_checkpointer


def get_scheduler():
    global scheduler
    return scheduler


async def init():
    # Setup connection pool
    global async_connection_pool
    pg_user = os.getenv("POSTGRES_USER", "langchain")
    pg_password = os.getenv("POSTGRES_PASSWORD", "langchain")
    pg_db = os.getenv("POSTGRES_DB", "langchain")
    pg_host = os.getenv("POSTGRES_HOST", "postgres_langchain")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    async_connection_pool = await asyncpg.create_pool(
        user=pg_user,
        password=pg_password,
        database=pg_db,
        host=pg_host,
        port=pg_port,
        min_size=1,  # Minimum number of connections
        max_size=10,  # Maximum number of connections
    )
    await migrate(async_connection_pool)
    # setup pg checkpointer
    global postgres_checkpointer
    db_uri = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}?sslmode=disable"
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }
    pool = AsyncConnectionPool(
        conninfo=db_uri,
        max_size=10,
        kwargs=connection_kwargs,
        open=False,
    )
    await pool.open(True)
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    postgres_checkpointer = checkpointer
    # Setup Chroma
    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "chroma_langchain"),
        port=os.getenv("CHROMA_PORT", "8000"),
        settings=Settings(
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=os.getenv("CHROMA_TOKEN", "test-token"),
        ),
    )
    model = MODEL_NAME  # sentence-transformers/all-mpnet-base-v2
    sentence_transformer_ef = HuggingFaceEmbeddings(model_name=model)
    chroma = Chroma(
        client=client,
        collection_name="langchain",
        embedding_function=sentence_transformer_ef,
    )
    set_chroma(chroma)
    # Scheduler
    global scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        remove_unreferenced_content, "interval", minutes=1, args=[async_connection_pool]
    )
    scheduler.add_job(
        optimize_file_content,
        "interval",
        minutes=1,
        args=[async_connection_pool, scheduler],
    )
    scheduler.start()
    # Syncing
    await optimize_file_content(async_connection_pool, scheduler)
    await remove_unreferenced_content(async_connection_pool)
    # sanity check: await sync_with_db(async_connection_pool)


async def shutdown():
    # Close connection pool
    global async_connection_pool
    await async_connection_pool.close()
    global postgres_checkpointer
    await postgres_checkpointer.conn.close()
    # Close Scheduler
    global scheduler
    scheduler.wakeup()
    scheduler.shutdown()
