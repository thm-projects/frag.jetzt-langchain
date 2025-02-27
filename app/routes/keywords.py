from langchain_core.runnables import RunnableLambda, RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    ConfigurableField,
    RunnableSerializable,
)
from app.routes.utils import select_model
from pydantic import BaseModel, Field


class KeywordExtraction(BaseModel):
    """Contains all extracted keywords, entities and special numbers from the content."""

    keywords: list[str] = Field(
        description="Contains keywords, which contain the essential meaning of the text"
    )
    named_entities: list[str] = Field(
        description="Contains proper nouns, names, people, organizations, locations, products, dates, identifiers and others"
    )
    special_numbers: list[str] = Field(
        description="Important Numbers with metric, if available, such as distances, references, dates, monetary values, measurements, percentages and so on"
    )

chat_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an intelligent assistant designed to analyze text and extract important elements. Your task is to identify and output the following:

1. **Keywords**: The most essential terms that convey the main ideas of the text, excluding common stop words. Apply **nominalization** where applicable (e.g., *analyzing -> analysis*, *happy -> happiness*).
2. **Named Entities**: Proper nouns such as names of people, organizations, locations, dates, and other specific identifiers.
3. **Special Numbers**: Numerically significant references, such as dates, monetary values, measurements, or percentages.

Example:
On July 5th, 1991, a fish named Bob attempted to swim in 1 meter of water. Later in the year 1991, Bob successfully swam in the water.

Example output:
```json
{
  "keywords": ["fish", "swimming", "water"],
  "named_entities": ["Bob"],
  "special_numbers": ["1 meter", "Year 1991", "July 5th, 1991"]
}
```

Additional Requirements:
- **Nominalization:** Convert verbs and adjectives into their noun forms whenever possible.
- **Language Consistency:** Generate all output in the same language as the input text.""",
        ),
        ("human", "{text}"),
    ]
)


class ExtractionTransformer(
    RunnableSerializable[KeywordExtraction, dict[str, list[str]]]
):
    """Deduplicates entries, if necessary."""

    allow_duplicates: bool

    def invoke(self, input: KeywordExtraction, config) -> dict[str, list[str]]:
        """Invoke the transformer."""

        keywords_dict = {
            "keywords": [x.strip() for x in input.keywords if x.strip() != ""],
            "entities": [x.strip() for x in input.named_entities if x.strip() != ""],
            "special": [x.strip() for x in input.special_numbers if x.strip() != ""],
        }
        if self.allow_duplicates:
            return keywords_dict
        # Remove duplicates
        keywords = keywords_dict["keywords"]
        entities = keywords_dict["entities"]
        special = keywords_dict["special"]
        keywords_dict["keywords"] = [
            x for x in keywords if x not in entities and x not in special
        ]
        keywords_dict["entities"] = [x for x in entities if x not in special]
        return keywords_dict


configurable_extraction_transformer = ExtractionTransformer(
    allow_duplicates=False
).configurable_fields(
    allow_duplicates=ConfigurableField(
        id="allow_duplicates",
        name="Allow Duplicates",
        description="If true, returns duplicates between the keywords.",
    )
)


async def get_structured_model(input: str, config: RunnableConfig):
    model = select_model(input, config)
    return await model.with_structured_output(KeywordExtraction).ainvoke(input)


chain = (
    chat_template
    | RunnableLambda(get_structured_model)
    | configurable_extraction_transformer
)
