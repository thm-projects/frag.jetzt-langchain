import asyncio

from langchain_huggingface import HuggingFaceEmbeddings
from app.ai_conversation.ai_conversation import MODEL_NAME


async def main():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    await embeddings.aembed_query("Hello, world!")


asyncio.run(main())
