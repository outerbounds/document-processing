from constants import USER_PROMPT_TEMPLATE, SYSTEM_PROMPT, GPT_MODEL
import json
import re


def fetch_page_content(url, timeout=5):
    import requests
    from bs4 import BeautifulSoup

    try:
        response = requests.get(url, timeout=timeout)
    except requests.exceptions.ConnectTimeout as e:
        return "", 408
    except requests.exceptions.ReadTimeout as e:
        return "", 408
    except requests.exceptions.ConnectionError as e:
        return "", 404
    except:  # catch all other exceptions
        return "", 500
    if response.status_code != 200:
        text = ""
    else:
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all(["p", "div"])
        text = " ".join(paragraph.get_text() for paragraph in paragraphs)
    return text.strip(), response.status_code


def add_https(url):
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def clean_text_data(data):
    text = re.sub(r"\[[0-9]*\]", " ", data)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r",", " ", text)
    return text


def compute_word_frequency(word_tokens, stopwords):
    word_frequencies = {}
    for word in word_tokens:
        if word not in stopwords:
            if word not in word_frequencies.keys():
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1
    return word_frequencies


def compute_sentence_scores(sent_tokens, word_frequencies):
    from nltk.tokenize import word_tokenize

    sentence_scores = {}
    for sentence in sent_tokens:
        for word in word_tokenize(sentence):
            if word in word_frequencies.keys():
                if (len(sentence.split(" "))) < 30:
                    if sentence not in sentence_scores.keys():
                        sentence_scores[sentence] = word_frequencies[word]
                    else:
                        sentence_scores[sentence] += word_frequencies[word]
    return sentence_scores


def get_key(val, sentence_scores):
    for key, value in sentence_scores.items():
        if val == value:
            return key


def filter_too_short_keys(sentence_scores, n=50):
    return {k: v for k, v in sentence_scores.items() if len(k) >= n}


def summarize_and_classify(url, n=5):

    import re
    import heapq
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from openai import OpenAI

    nltk.download("punkt")
    nltk.download("stopwords")

    text, status_code = fetch_page_content(url)
    if status_code != 200:
        return {
            "return_code": status_code,
            "prompt": "",
            "raw_completion": "",
            "description": "",
            "uses_ai": None,
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
            "system_fingerprint": "",
            "model": "",
        }

    cleaned_text = clean_text_data(text)

    sent_tokens = sent_tokenize(cleaned_text)
    word_tokens = word_tokenize(cleaned_text)
    stopwords = set(stopwords.words("english"))
    word_frequencies = compute_word_frequency(word_tokens, stopwords)
    sentence_scores = compute_sentence_scores(sent_tokens, word_frequencies)
    sentence_scores = filter_too_short_keys(sentence_scores)

    try:
        key = get_key(max(sentence_scores.values()), sentence_scores)
        summary = heapq.nlargest(n, sentence_scores, key=sentence_scores.get)
        summary = " ".join(summary)
    except ValueError:
        summary = ""

    client = OpenAI()
    prompt = USER_PROMPT_TEMPLATE.format(content=summary)
    completion = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    completion_tokens = completion.usage.completion_tokens
    prompt_tokens = completion.usage.prompt_tokens
    total_tokens = completion.usage.total_tokens
    system_fingerprint = completion.system_fingerprint
    model = completion.model
    content = completion.choices[0].message.content

    ### Sometimes OpenAI returns JSON like this regex
    openai_json_regex = r"```json\s*\n(.*?)\n```"
    match = re.search(openai_json_regex, content, re.DOTALL)
    if match:
        json_str = match.group(1)
        json_dict = json.loads(json_str)
        description = json_dict["description"]
        uses_ai = json_dict["uses_ai"]
    elif content.strip().startswith('{"description":'):
        json_dict = json.loads(content)
        description = json_dict["description"]
        uses_ai = json_dict["uses_ai"]
    else:
        uses_ai = None
        description = None

    return {
        "return_code": status_code,
        "prompt": prompt,
        "raw_completion": completion.choices[0].message.content,
        "description": description,
        "uses_ai": uses_ai,
        "completion_tokens": completion_tokens,
        "prompt_tokens": prompt_tokens,
        "total_tokens": total_tokens,
        "system_fingerprint": system_fingerprint,
        "model": model,
    }
