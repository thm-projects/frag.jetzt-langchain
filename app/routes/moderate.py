from fastapi import APIRouter, Body, Request
from app.security.oauth2 import ROOM_DEPENDENCIES, per_req_config_modifier
from detoxify import Detoxify
from openai import OpenAI
from more_itertools import chunked
from transformers import pipeline

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


def split_text_by_tokens(tokenizer, text, max_length):
    tokens = tokenizer.tokenize(text)
    chunks = []

    for i in range(0, len(tokens), max_length):
        chunk = tokens[i : i + max_length]
        chunks.append(tokenizer.convert_tokens_to_string(chunk))

    return chunks


def run_simple_sentiment(text_list, pipeline, max_size):
    tokens = []
    offsets = []
    for text in text_list:
        tokens.extend(
            split_text_by_tokens(pipeline.tokenizer, text, max_size - 2)
        )  # -2 for BOS and EOS
        offsets.append(len(tokens))
    results = pipeline(tokens)
    sentiments = []
    old_results = results
    results = []
    current_val = None
    k = 0
    for i, result in enumerate(old_results):
        if i == offsets[k]:
            length = sum(map(lambda x: x["score"], current_val))
            results.append(
                [
                    {"score": r["score"] / length, "label": r["label"]}
                    for r in current_val
                ]
            )
            current_val = None
            k += 1
        if current_val is None:
            current_val = result
        current_val = [
            {"score": r["score"] + r2["score"], "label": r["label"]}
            for r, r2 in zip(result, current_val)
        ]
    length = sum(map(lambda x: x["score"], current_val))
    results.append(
        [
            {"score": r["score"] / length, "label": r["label"]}
            for r in current_val
        ]
    )
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


def run_moderate(text_list, api_key):
    result = {}

    result_list = []
    for texts in chunked(text_list, 64):
        result_list.extend(run_detox(texts))
    result["detoxify"] = result_list

    if api_key is not None:
        result_list = []
        for texts in chunked(text_list, 32):
            result_list.extend(run_openai(api_key, texts))
        result["openai"] = result_list

    sentiments = []
    for texts in chunked(text_list, 16):
        sentiment1 = run_simple_sentiment(texts, sentiment_pipeline, 512)
        sentiment2 = run_simple_sentiment(texts, sentiment_pipeline_2, 512)
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
