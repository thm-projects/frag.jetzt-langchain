from llmlingua import PromptCompressor
import re
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field


class CategoryList(BaseModel):
    """All categories from the content"""

    categories: list[str] = Field(
        description="The list containing all categories starting with uppercase, if useful"
    )


llm_lingua = PromptCompressor(
    model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
    use_llmlingua2=True,
    device_map="cpu",
)


prompt = """You are an AI assistant specialized in text analysis. Your task is to extract a list of general categories from a summarized text, organizing its content into high-level, non-contradictory themes. 

Pay attention for:
1. **General:** Categories should be broad enough to cover subtopics within the text.  
2. **Non-Contradictory:** Avoid overlapping categories that could create logical conflicts.  
3. **Relevant:** Ensure all categories accurately reflect the core topics of the text.  
4. **Nominalized:** Convert verbs and adjectives into their noun forms whenever possible (e.g., *analyzing -> analysis*, *efficient -> efficiency*).  
5. **Language Consistency:** Generate the categories in the same language as the input text.

Present the categories as a clear, concise list. Do not include explanations."""


def prepare(data):
    text = ".".join(data)
    text = re.sub(r"\.(\s*\.)+", ".", text, count=0, flags=re.MULTILINE)
    text = re.sub(r"\?(\s*\?)+", "?", text, count=0, flags=re.MULTILINE)
    return re.sub(r"!(\s*!)+", "!", text, count=0, flags=re.MULTILINE)


async def extract_keywords(chat_model, texts):
    compressed = llm_lingua.compress_prompt(
        prepare(texts), target_token=10_000, force_tokens=["?", "!", "."]
    )
    chat_model = chat_model.with_structured_output(CategoryList)
    return await chat_model.ainvoke(
        [SystemMessage(prompt), HumanMessage(compressed["compressed_prompt"])]
    )
