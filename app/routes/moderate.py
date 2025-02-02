from fastapi import APIRouter, Body, Request
from app.security.oauth2 import ROOM_DEPENDENCIES, per_req_config_modifier
from app.celadon.model import MultiHeadDebertaForSequenceClassification
from transformers import AutoTokenizer
from detoxify import Detoxify
from openai import OpenAI
from more_itertools import chunked
from transformers import pipeline

celadon_tokenizer = AutoTokenizer.from_pretrained("PleIAs/celadon")
celadon = MultiHeadDebertaForSequenceClassification.from_pretrained("PleIAs/celadon")
celadon.eval()

detox = Detoxify("multilingual")

sentiment_pipeline = pipeline(
    task="sentiment-analysis",
    model="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
    top_k=None,
)

sentiment_pipeline_2 = pipeline(
    task="sentiment-analysis",
    model="cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
    top_k=None,
)


def run_simple_sentiment(text_list, pipeline):
    results = pipeline(text_list)
    sentiments = []
    for result in results:
        pos = next((r["score"] for r in result if r["label"] == "positive"), None)
        neutral = next((r["score"] for r in result if r["label"] == "neutral"), None)
        neg = next((r["score"] for r in result if r["label"] == "negative"), None)
        sentiments.append([pos, neutral, neg])
    return sentiments


def combine_sentiments(sentiments):
    vec_len = len(sentiments[0])
    neg_index = 2 if vec_len < 5 else 3
    negative_sentiments = None
    rest_sentiments = []
    for s in sentiments:
        m = max(s)
        had_negative = False
        for neg_idx in range(neg_index, vec_len):
            if s[neg_idx] < m:
                continue
            had_negative = True
            if negative_sentiments is None:
                negative_sentiments = s
            else:
                negative_sentiments = [
                    negative_sentiments[i] + s[i] for i in range(vec_len)
                ]
            break
        if not had_negative:
            rest_sentiments.append(s)

    if negative_sentiments is not None:
        negative_sentiments = normalize(negative_sentiments)
        rest_sentiments = [interpolate(s, negative_sentiments) for s in rest_sentiments]
        rest_sentiments.append(negative_sentiments)

    return normalize([sum(s[i] for s in rest_sentiments) for i in range(vec_len)])


def normalize(vec):
    total = sum(vec)
    if abs(total) < 1e-10:
        return vec
    return [i / total for i in vec]


def interpolate(pos, neg):
    split_index = 2 if len(pos) > 3 else 1
    best_t = 0
    for other_index in range(split_index, len(pos)):
        cur_t = 1
        for pos_index in range(split_index):
            bottom = (
                pos[other_index] - neg[other_index] - pos[pos_index] + neg[pos_index]
            )
            if abs(bottom) < 1e-5:
                cur_t = 0
                break
            t = (neg[pos_index] - neg[other_index]) / bottom
            if t <= 0:
                cur_t = 0
                break
            elif t < cur_t:
                cur_t = t
        if cur_t >= 1:
            best_t = 1
            break
        elif cur_t > best_t:
            best_t = cur_t
    t = best_t
    t_inv = 1 - t
    return [pos[i] * t + neg[i] * t_inv for i in range(len(pos))]


def run_openai(api_key, text_list):
    client = OpenAI(api_key=api_key)
    response = client.moderations.create(
        model="text-moderation-latest",
        input=text_list,
    )
    return [
        {
            **dict(result.category_scores),
            "flagged": result.flagged,
        }
        for result in response.results
    ]


def run_detox(text_list):
    result_dict = detox.predict(text_list)
    length = len(result_dict["toxicity"])
    return [{k: v[i] for (k, v) in result_dict.items()} for i in range(length)]


def run_celadon(text_list):
    LABEL_MAX = 3
    inputs = celadon_tokenizer(
        text_list, return_tensors="pt", padding=True, truncation=True
    )
    outputs = celadon(
        input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"]
    )

    predictions = outputs.argmax(dim=-1).squeeze()
    iterations = predictions.size()[0]
    if len(predictions.size()) == 1:
        iterations = 1
        predictions = [predictions]

    result = [
        {
            "Race/Origin": predictions[i][0].item() / LABEL_MAX,
            "Gender/Sex": predictions[i][1].item() / LABEL_MAX,
            "Religion": predictions[i][2].item() / LABEL_MAX,
            "Ability": predictions[i][3].item() / LABEL_MAX,
            "Violence": predictions[i][4].item() / LABEL_MAX,
        }
        for i in range(iterations)
    ]
    for result_item in result:
        summed_values = sum(result_item.values())
        if summed_values > 2:
            result_item["Flagged"] = "Toxic"
        elif summed_values > 1 or max(result_item.values()) == 1:
            result_item["Flagged"] = "Mild"
        else:
            result_item["Flagged"] = "No"
    return result


def run_moderate(text_list, api_key):
    result = {}

    result_list = []
    for texts in chunked(text_list, 64):
        result_list.extend(run_detox(texts))
    result["detoxify"] = result_list

    result_list = []
    for texts in chunked(text_list, 2):
        result_list.extend(run_celadon(texts))
    result["celadon"] = result_list

    if api_key is not None:
        result_list = []
        for texts in chunked(text_list, 32):
            result_list.extend(run_openai(api_key, texts))
        result["openai"] = result_list

    sentiments = []
    for texts in chunked(text_list, 16):
        sentiment1 = run_simple_sentiment(texts, sentiment_pipeline)
        sentiment2 = run_simple_sentiment(texts, sentiment_pipeline_2)
        for sentis in zip(sentiment1, sentiment2):
            sentiments.append(combine_sentiments(sentis))
    result["sentiment"] = sentiments

    return result


def expand_to_list(data: dict) -> list[dict]:
    length = len(data["detoxify"])
    return [{k: v[i] for k, v in data.items()} for i in range(length)]


router = APIRouter()


@router.post("/", dependencies=ROOM_DEPENDENCIES, tags=["Moderate Texts"])
async def moderate_texts(
    request: Request,
    texts: list[str] = Body(..., embed=True),
    allow_openai: bool = False,
) -> list[dict]:
    config = {"configurable": {}}
    await per_req_config_modifier(config, request)
    # TODO: Find correct key
    api_key = config["configurable"]["api_obj"]["api_key"]
    return expand_to_list(run_moderate(texts, api_key if allow_openai else None))
