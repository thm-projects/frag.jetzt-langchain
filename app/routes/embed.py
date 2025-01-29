from app.ai_conversation.ai_conversation import get_embedding_function
from fastapi import APIRouter, Body
import base64
import numpy as np

from app.security.oauth2 import DEPENDENCIES


async def transform_standard_retrieve(texts: list[str]):
    return await get_embedding_function().aembed_documents(texts)


def to_b64(vec: list[float]) -> str:
    vec = np.array(vec, dtype=np.float32)
    return base64.b64encode(vec).decode("utf-8")


router = APIRouter()


@router.post("/embed", dependencies=DEPENDENCIES, tags=["Similarity Embedding"])
async def embed_texts(texts: list[str] = Body(..., embed=True)) -> list[str]:
    """
    You can convert base64 string to Float32Array with the following code:
    
    <pre><code>
    base64 = "AACAPwAAAEDD9UhAexQuQA=="
    byte_array = Uint8Array.from(atob(base64), c => c.charCodeAt(0))
    vectors = new Float32Array(byte_array.buffer)
    </code></pre>
    """
    vectors = await transform_standard_retrieve(texts)
    return [to_b64(v) for v in vectors]
