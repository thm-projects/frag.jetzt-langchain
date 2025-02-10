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


prompt = """You are an AI assistant tasked with analyzing a summarized text and extracting a list of general categories based on its content. Your role is to organize the text into high-level, non-contradictory categories that accurately represent the main topics or themes. These categories should be:  

1. **General:** Broad enough to encompass subtopics within the text.  
2. **Non-Contradictory:** Do not overlap in a way that creates logical conflicts.  
3. **Relevant:** Directly related to the main ideas presented in the text.  

Provide the categories as a clear, concise list without additional explanation unless requested.
Generate the categories in the language of the summarized text.
If possible, always output a lemmatized version of the category, not the original."""


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
