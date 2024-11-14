from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.routes.utils import select_model

chat_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            "Please create a headline from the following text, summarizing it in a few impactful words (maximum 5) that capture the main idea. Use the language of the user for the headline. If the text contains any profane or informal language, please rephrase it to maintain a formal tone. Do not answer the question, just create a headline.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = chat_template | select_model | StrOutputParser()
