from langchain_core.prompts import ChatPromptTemplate
from app.routes.utils import select_model
from langchain_core.output_parsers import StrOutputParser

chat_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an assistant which reviews and improves text for grammar, spelling, punctuation, and overall readability. Your task is to enhance the writing style while preserving the original meaning and content. Do not modify any logical arguments, equations, or factual claims, even if they appear incorrect or inconsistent.",
        ),
        ("human", "{text}"),
    ]
)


chain = (
    chat_template | select_model | StrOutputParser()
)
