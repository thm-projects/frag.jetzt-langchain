from fastapi import HTTPException, status
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    ConfigurableField,
    RunnableSerializable,
)
from app.routes.utils import select_model

chat_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
**Prompt:** You are an intelligent assistant designed to analyze text and extract important elements. Your task is to identify and output the following:

1. **Keywords**: The most essential terms that convey the main ideas of the text, excluding common stop words.
2. **Named Entities**: Proper nouns such as names of people, organizations, locations, dates, and other specific identifiers.
3. **Special Numbers**: Numerically significant references, such as dates, monetary values, measurements, or percentages.

**Example:** "On July 5th, 1991, a fish named Bob attempted to swim in 1 meter of water. Later in the year 1991, Bob successfully swam in the water."

Output each section in the format:

```
Keywords: keyword1; keyword2; keyword3;
:::
Named Entities: entity1; entity2; entity3;
:::
Special Numbers: number1; number2; number3;
```

For the example given, your output would be:
```
Keywords: fish; swim; water;
:::
Named Entities: Bob;
:::
Special Numbers: 1 meter; Year 1991; July 5th, 1991;
```

If a section is empty, output an empty string for that section. If there are no keywords, named entities, or special numbers, output an empty string for each section.
Like so:
```
Keywords:
:::
Named Entities:
:::
Special Numbers:
```
         """,
        ),
        ("human", "{text}"),
    ]
)


class StringTransformer(RunnableSerializable[str, dict[str, list[str]]]):
    """Parses the string returned by the model."""

    allow_duplicates: bool

    def invoke(self, input: str, config) -> dict[str, list[str]]:
        """Invoke the transformer."""
        if input.startswith("```"):
            input = input[3:]
        if input.endswith("```"):
            input = input[:-3]
        text = input.strip()
        categories = text.split("\n:::\n")
        if len(categories) != 3:
            print("Failed keywords:", text)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Try again."
            )
        if (
            not categories[0].lower().startswith("keywords:")
            or not categories[1].lower().startswith("named entities:")
            or not categories[2].lower().startswith("special numbers:")
        ):
            print("Failed keywords:", text)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Try again."
            )
        keywords_dict = {
            "keywords": [
                x.strip() for x in categories[0][9:].split(";") if x.strip() != ""
            ],
            "entities": [
                x.strip() for x in categories[1][15:].split(";") if x.strip() != ""
            ],
            "special": [
                x.strip() for x in categories[2][16:].split(";") if x.strip() != ""
            ],
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


configurable_string_transformer = StringTransformer(
    allow_duplicates=False
).configurable_fields(
    allow_duplicates=ConfigurableField(
        id="allow_duplicates",
        name="Allow Duplicates",
        description="If true, returns duplicates between the categories.",
    )
)


chain = (
    chat_template | select_model | StrOutputParser() | configurable_string_transformer
)
