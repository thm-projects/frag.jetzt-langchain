import asyncio

from langchain_huggingface import HuggingFaceEmbeddings
from app.ai_conversation.ai_conversation import MODEL_NAME
from app.routes.moderate import run_moderate
from app.routes.category_list import extract_keywords


async def main():
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    await embeddings.aembed_query("Hello, world!")
    run_moderate(["Test"], None)
    try:
        extract_keywords(None, ['Hi'])
    except AttributeError:
        print('OK')


asyncio.run(main())
