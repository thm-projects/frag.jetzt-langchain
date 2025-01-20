import streamlit as st
import json
import pandas as pd
from openai import OpenAI
from transformers import AutoTokenizer
from celadon.model import MultiHeadDebertaForSequenceClassification
from detoxify import Detoxify
import os
import re


@st.cache_resource
def get_tokenizer():
    return AutoTokenizer.from_pretrained("distilbert/distilbert-base-multilingual-cased")


@st.cache_resource
def get_celadon_tokenizer():
    return AutoTokenizer.from_pretrained("celadon")


@st.cache_resource
def get_celadon_model():
    celadon = MultiHeadDebertaForSequenceClassification.from_pretrained("celadon")
    celadon.eval()
    return celadon


@st.cache_resource
def get_detoxify():
    return Detoxify("multilingual")


@st.cache_data
def get_source():
    data = pd.read_csv(
        "./MultiLanguageTrainDataset.csv", usecols=["text", "label", "language"]
    )
    german = data[data.language == 5]
    english = data[data.language == 2]
    french = data[data.language == 4]

    german = german.drop(columns=["language"])
    english = english.drop(columns=["language"])
    french = french.drop(columns=["language"])
    return {"german": german, "english": english, "french": french}


@st.cache_data
def get_data():
    result = {}
    for x in ["german", "english", "french"]:
        with open(f"multihatespeech/{x}-oai-mhd.json") as f:
            oai = json.load(f)
        with open(f"multihatespeech/{x}-celadon-mhd.json") as f:
            celadon = json.load(f)
        with open(f"multihatespeech/{x}-detox-mhd.json") as f:
            detox = json.load(f)
        v = {"oai": oai, "celadon": celadon, "detox": detox}
        result[x] = v
    return result


@st.cache_data
def get_token_offsets(text):
    offsets = get_tokenizer()(
        text, return_attention_mask=False, return_offsets_mapping=True
    )["offset_mapping"]
    result = []
    for i, offset in enumerate(offsets):
        if offset[0] == 0 and offset[1] == 0:
            continue
        result.append(
            {
                "start": offset[0],
                "end": offset[1],
                "index": i,
                "text": text[offset[0] : offset[1]],
            }
        )
    return result


def run_celadon(text_list):
    LABEL_MAX = 3
    inputs = get_celadon_tokenizer()(
        text_list, return_tensors="pt", padding=True, truncation=True
    )
    outputs = get_celadon_model()(
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


def run_openai(text):
    client = OpenAI(api_key="sk...")
    response = client.moderations.create(
        model="text-moderation-latest",
        input=text,
    )
    return [
        {
            **dict(result.category_scores),
            "flagged": result.flagged,
        }
        for result in response.results
    ]


def run_detox(text_list):
    result_dict = get_detoxify().predict(text_list)
    length = len(result_dict["toxicity"])
    return [{k: v[i] for (k, v) in result_dict.items()} for i in range(length)]


def make_check(text):
    selections = st.session_state.get("label-selection", [])
    text2 = text
    text3 = text
    for select in selections:
        start = select["start"]
        end = select["end"]
        length = end - start
        text = text[:start] + "_" * length + text[end:]
        text2 = text2[:start] + " " * length + text2[end:]
        text3 = text3[:start] + "*" * length + text3[end:]
    st.text(text)
    text_list = [text2]
    oai = run_openai(text_list)
    keys = [*oai[0].keys()]
    for key in keys:
        if "/" not in key:
            continue
        other = key.replace("/", "_")
        if other not in oai[0]:
            continue
        for i in range(len(oai)):
            del oai[i][other]

    st.session_state["last_request"] = {
        "oai": oai,
        "celadon": run_celadon([text]),
        "detox": run_detox([text]),
    }


@st.cache_data
def make_sentence_check(text):
    # Split text into sentences
    texts = re.split(r"([.?!])(?!\1)", text)
    length = len(texts) // 2
    sentences = []
    add_text = ""
    for i in range(length):
        new_text = texts[i * 2] + texts[i * 2 + 1]
        new_text = add_text + new_text.strip()
        if len(new_text) < 10:
            add_text = new_text
            continue
        sentences.append(new_text)
    new_text = texts[-1]
    new_text = add_text + new_text.strip()
    if new_text != "":
        sentences.append(new_text)
    # request OpenAI, Celadon and Detoxify
    oai = run_openai(sentences)
    celadon = run_celadon(sentences)
    detox = run_detox(sentences)
    # combine results
    res = []
    for i in range(len(sentences)):
        res.append(
            {
                "text": sentences[i],
                "oai": get_meta(oai[i]),
                "celadon": get_meta(celadon[i]),
                "detox": get_meta(detox[i]),
            }
        )
    return res


def get_meta(map):
    min_val = None
    min_cat = None
    max_val = None
    max_cat = None
    summed = 0
    count = 0
    for key, x in map.items():
        if type(x) is not float:
            continue
        summed += x
        count += 1
        if min_val is None or x < min_val:
            min_val = x
            min_cat = key
        if max_val is None or x > max_val:
            max_val = x
            max_cat = key
    return {
        "min": {"category": min_cat, "value": min_val},
        "max": {"category": max_cat, "value": max_val},
        "average": summed / count,
    }


def calc_max_value(max_value, max_index, data, i):
    oai = get_meta(data["oai"][i])["average"]
    detox = get_meta(data["detox"][i])["average"]
    celadon = get_meta(data["celadon"][i])["average"]
    if max_value is None:
        return i, [oai, detox, celadon]
    r_oai, r_detox, r_celadon = max_value
    if r_oai < oai or r_detox < detox or r_celadon < celadon:
        return i, [oai, detox, celadon]
    return max_index, max_value


def who_flagged(data, i, source):
    result = ""
    if source.iloc[i]["label"] == 1.0:
        result += "Source "

    for key, v in data["oai"][i].items():
        if type(v) is not float:
            if key == "flagged" and v:
                result += "OpenAI "
                break
            continue
        if v > 0.4:
            result += "OpenAI "
            break

    for key, v in data["celadon"][i].items():
        if type(v) is not float:
            if key == "Flagged" and v != "No":
                result += "Celadon "
                break
            continue
        if v > 0.7:
            result += "Celadon "
            break

    for key, v in data["detox"][i].items():
        if type(v) is not float:
            continue
        if v > 0.25:
            result += "Detoxify "
            break

    if result != "":
        return result
    return "None"


@st.cache_data
def calculate_metas(data):
    def compress(v, v1):
        if v["min"]["value"] > v1["min"]["value"]:
            v["min"] = v1["min"]
        if v["max"]["value"] < v1["max"]["value"]:
            v["max"] = v1["max"]
        v["average"] = (v["average"] + v1["average"]) / 2
        return v

    def max_celadon(v, v1):
        d = {
            "No": 0,
            "Mild": 1,
            "Toxic": 2,
        }
        if d[v] < d[v1]:
            return v1
        return v

    m_oai = get_meta(data["oai"][0])
    m_oai_data = data["oai"][0]
    for i in range(1, len(data["oai"])):
        m_oai = compress(m_oai, get_meta(data["oai"][i]))
        for key, v in data["oai"][i].items():
            if v is None:
                continue
            if type(v) is not float:
                m_oai_data[key] = max(m_oai_data[key], v)
            else:
                m_oai_data[key] = (m_oai_data[key] + v) / 2

    m_cel = get_meta(data["celadon"][0])
    m_cel_data = data["celadon"][0]
    for i in range(1, len(data["celadon"])):
        m_cel = compress(m_cel, get_meta(data["celadon"][i]))
        for key, v in data["celadon"][i].items():
            if type(v) is not float:
                m_cel_data[key] = max_celadon(m_cel_data[key], v)
            else:
                m_cel_data[key] = (m_cel_data[key] + v) / 2

    m_detox = get_meta(data["detox"][0])
    m_detox_data = data["detox"][0]
    for i in range(1, len(data["detox"])):
        m_detox = compress(m_detox, get_meta(data["detox"][i]))
        for key, v in data["detox"][i].items():
            if type(v) is not float:
                continue
            m_detox_data[key] = (m_detox_data[key] + v) / 2
    return {
        "metas": [m_oai, m_cel, m_detox],
        "oai": m_oai_data,
        "celadon": m_cel_data,
        "detox": m_detox_data,
    }


def write_columns(d):
    d = calculate_metas(d)

    m_oai = d["metas"][0]
    m_cel = d["metas"][1]
    m_detox = d["metas"][2]

    st.write("## Results")
    st.write(
        f"OpenAI - Flagged: {d['oai']['flagged']} Max: {m_oai['max']['category']} {m_oai['max']['value']}"
    )
    st.write(f"Detox - Max: {m_detox['max']['category']}\t{m_detox['max']['value']}")
    st.write(
        f"Celadon - Status: {d['celadon']['Flagged']} Max: {m_cel['max']['category']} {m_cel['max']['value']}"
    )

    oai, celadon, detox = st.columns(3)
    oai.write("## OpenAI")
    oai.table(d["oai"])
    oai.write(f"Min: {m_oai['min']['category']} {m_oai['min']['value']}")
    oai.write(f"Max: {m_oai['max']['category']} {m_oai['max']['value']}")
    oai.write(f"Average: {m_oai['average']}")

    celadon.write("## Celadon")
    celadon.table(d["celadon"])
    celadon.write(f"Min: {m_cel['min']['category']} {m_cel['min']['value']}")
    celadon.write(f"Max: {m_cel['max']['category']} {m_cel['max']['value']}")
    celadon.write(f"Average: {m_cel['average']}")

    detox.write("## Detoxify")
    detox.table(d["detox"])
    detox.write(f"Min: {m_detox['min']['category']} {m_detox['min']['value']}")
    detox.write(f"Max: {m_detox['max']['category']} {m_detox['max']['value']}")
    detox.write(f"Average: {m_detox['average']}")


def reset():
    st.session_state.pop("last_request", None)
    st.session_state.pop("widget_count", None)
    st.session_state.pop("current_index", None)


def check_selection():
    selections = st.session_state.get("label-selection", [])
    if len(selections) == 0:
        return None
    selections = set(map(lambda x: x["index"], selections))
    for i in range(st.session_state.get("widget_count", 1)):
        if f"label-{i}" not in st.session_state:
            return "Please classify all selections"
        selection = st.session_state[f"label-{i}"]
        for s in selection:
            s = s["index"]
            if s not in selections:
                return "Please do not classify the same selection twice"
            else:
                selections.remove(s)
    if len(selections) > 0:
        return "Please classify all selections"
    return None


def find_max_index(language, source):
    current = st.session_state["data"][language]
    max_index = 0
    max_value = None
    keys = list(map(int, current.keys()))
    for i in range(len(source)):
        if source.index[i] in keys:
            continue
        if who_flagged(data, i, source) == "None":
            continue
        max_index, max_value = calc_max_value(max_value, max_index, data, i)
    return max_index


def submit_data(language, data, index, source):
    all_data = st.session_state["data"]
    all_data[language][str(source.index[index])] = data
    with open("streamlit-data.json", "w") as f:
        json.dump(all_data, f)


def get_selection_options(i):
    selections = st.session_state.get("label-selection", [])
    max_count = min(i, st.session_state.get("widget_count", 1))
    for j in range(max_count):
        if f"label-{j}" not in st.session_state:
            continue
        current_selection = set(
            map(lambda x: x["index"], st.session_state[f"label-{j}"])
        )
        selections = list(
            filter(lambda x: x["index"] not in current_selection, selections)
        )

    if f"label-{i}" not in st.session_state:
        return [], selections
    all_ids = set(map(lambda x: x["index"], selections))
    filtered = list(
        filter(lambda x: x["index"] in all_ids, st.session_state[f"label-{i}"])
    )
    return filtered, selections


if "data" not in st.session_state:
    st.session_state["data"] = {"german": {}, "english": {}, "french": {}}
    if os.path.isfile("streamlit-data.json"):
        with open("streamlit-data.json") as f:
            st.session_state["data"] = json.load(f)


labels_explanation = {
    "violent": "Content that incites or glorifies physical harm or aggression, including threats.\nExample: 'I'm going to hurt you, and you deserve it.'",
    "obscene": "Content that is vulgar, explicit, or offensive in language or sexual nature.\nExample: 'What the **** is wrong with you, you piece of ****?'",
    "harassment": "Content that includes persistent unwanted behavior or personal attacks.\nExample: 'You're a failure, and everyone knows it.'",
    "hate_discrimination": "Content that demeans, attacks, or excludes based on personal or group attributes.\nExample: 'People like you shouldn't exist.'",
    "self_harm": "Content that promotes self-harm, suicide, or glorifies injury.\nExample: 'Cutting yourself is the only way to feel better.'",
    "inappropriate": "Content that is contextually inappropriate or violates the norms of a specific audience.\nExample: Sharing adult-themed jokes in a children's forum.",
}

labels = [
    # Content that incites or glorifies physical harm or aggression, including threats.
    "violent",  # Example: "I'm going to hurt you, and you deserve it."
    # Content that is vulgar, explicit, or offensive in language or sexual nature.
    "obscene",  # Example: "What the **** is wrong with you, you piece of ****?"
    # Content that includes persistent unwanted behavior or personal attacks.
    "harassment",  # Example: "You're a failure, and everyone knows it."
    # Content that demeans, attacks, or excludes based on personal or group attributes.
    "hate_discrimination",  # Example: "People like you shouldn't exist."
    # Content that promotes self-harm, suicide, or glorifies injury.
    "self_harm",  # Example: "Cutting yourself is the only way to feel better."
    # Content that is contextually inappropriate or violates the norms of a specific audience.
    "inappropriate",  # Example: Sharing adult-themed jokes in a children's forum.
]

st.title("Labeling Tool")

language = st.selectbox(
    "Language",
    ["german", "english", "french"],
    on_change=lambda: reset(),
)
data = get_data()[language]
source = get_source()[language]
source
if "current_index" not in st.session_state:
    current_index = find_max_index(language, source)
    st.session_state["current_index"] = current_index
else:
    current_index = st.session_state["current_index"]


text = source.iloc[current_index]["text"]

st.write(f"Current Index: {current_index}")
st.write(f"Who flagged: {who_flagged(data, current_index, source)}")

with st.expander("Source values"):
    d = {
        "oai": [data["oai"][current_index]],
        "celadon": [data["celadon"][current_index]],
        "detox": [data["detox"][current_index]],
    }
    write_columns(d)

    

offsets = get_token_offsets(text)

res = make_sentence_check(text)
for r in res:
    st.write(f"> {r['text']}")
    oai = f"OpenAI-max: {r['oai']['max']['category']} {r['oai']['max']['value']}"
    celadon = f"Celadon-max: {r['celadon']['max']['category']} {r['celadon']['max']['value']}"
    detox = f"Detoxify-max: {r['detox']['max']['category']} {r['detox']['max']['value']}"
    st.text(f"{oai}\n{celadon}\n{detox}")

selection = st.pills(
    "Label Selection",
    offsets,
    format_func=lambda x: x["text"],
    selection_mode="multi",
    key="label-selection",
)

if "widget_count" not in st.session_state:
    st.session_state["widget_count"] = 1

if st.button("Add"):
    st.session_state["widget_count"] += 1

if st.button("Remove"):
    st.session_state["widget_count"] = max(1, st.session_state["widget_count"] - 1)

with st.expander("Labels Explanation"):
    for key, value in labels_explanation.items():
        st.write(f"### {key}")
        st.write(value)

for i in range(st.session_state["widget_count"]):
    default_value, select_values = get_selection_options(i)
    st.multiselect(
        f"Input {i}",
        select_values,
        format_func=lambda x: x["text"],
        key=f"label-{i}",
    )
    st.radio(f"Class {i}", labels, key=f"label-{i}-radio")


if st.button("Check"):
    make_check(text)

hint = check_selection()
if hint is not None:
    st.warning(hint)


def submit():
    data = []
    for i in range(st.session_state.get("widget_count", 1)):
        selection = st.session_state[f"label-{i}"]
        category = st.session_state[f"label-{i}-radio"]
        for s in selection:
            data.append((s["index"], s["start"], s["end"], category))
    submit_data(language, data, current_index, source)
    reset()


if st.button("Submit", type="primary", disabled=hint is not None, on_click=submit):
    st.success("Data submitted")

if "last_request" in st.session_state:
    d = st.session_state["last_request"]
    write_columns(d)
