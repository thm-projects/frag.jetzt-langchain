from typing import Optional
from fastapi import APIRouter, Body, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from langchain_core.prompts import SystemMessagePromptTemplate

from app.routes.category_list import extract_keywords, CategoryList
from app.routes.utils import select_model
from app.security.oauth2 import ROOM_DEPENDENCIES, per_req_config_modifier


class CategorySelect(BaseModel):
    """The selected category or null/None for the content"""

    category: Optional[str] = Field(description="The selected category, if available")


prompt = SystemMessagePromptTemplate.from_template("""You are an AI assistant tasked with determining if a piece of content belongs to any category from the following predefined list:

{categories}

Your role:
1. **Match the Content:** Compare the content to each category and decide if it aligns with any of them.
2. **Output the Category:** If the content fits a category, output the most appropriate category from the list.
3. **Exclusion:** If the content does not fit any category, respond with nothing.

Provide only the selected category or nothing as the output, ensuring precision and consistency in your decisions.""")


async def run_category_select(model, categories: list[str], text: str):
    model = model.with_structured_output(CategorySelect)
    return await model.ainvoke(
        [prompt.format(categories="\n".join(categories)), HumanMessage(text)]
    )


router = APIRouter()


@router.post("/apply", dependencies=ROOM_DEPENDENCIES, tags=["Category List"])
async def apply_category(
    request: Request,
    categories: list[str] = Body(..., embed=True),
    text: str = Body(..., embed=True),
) -> CategorySelect:
    config = {"configurable": {}}
    await per_req_config_modifier(config, request)
    model = select_model(None, config)
    return await run_category_select(model, categories, text)


@router.post("/extract", dependencies=ROOM_DEPENDENCIES, tags=["Category List"])
async def extract_categories(
    request: Request,
    texts: list[str] = Body(..., embed=True),
) -> CategoryList:
    config = {"configurable": {}}
    await per_req_config_modifier(config, request)
    model = select_model(None, config)
    return await extract_keywords(model, texts)
