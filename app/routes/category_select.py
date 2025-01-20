from typing import Optional
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from langchain_core.prompts import SystemMessagePromptTemplate


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
    return await model.with_structured_output(CategorySelect).ainvoke(
        [prompt.format(categories="\n".join(categories)), HumanMessage(text)]
    )
