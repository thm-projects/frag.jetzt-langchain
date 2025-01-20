from app.ai_conversation.ai_conversation import get_embedding_function


async def transform_standard_retrieve(texts: list[str]):
    return await get_embedding_function().aembed_documents(texts)
