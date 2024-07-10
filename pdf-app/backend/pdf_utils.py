import re
import requests


def preprocess(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def pdf_to_text(path, start_page=1, end_page=None):
    try:
        import pymupdf as fitz  # available with v1.24.3
    except ImportError:
        import fitz
    doc = fitz.open(path)
    total_pages = doc.page_count
    if end_page is None:
        end_page = total_pages
    text_list = []
    for i in range(start_page - 1, end_page):
        text = doc.load_page(i).get_text("text")
        text = preprocess(text)
        text_list.append({"content": text, "page": i + 1})
    doc.close()
    return text_list


def text_to_chunks(texts, word_length=150, start_page=1):
    text_toks = [(t["content"].split(" "), t["page"]) for t in texts]
    chunks = []

    for idx, words_and_page in enumerate(text_toks):
        words = words_and_page[0]
        page = words_and_page[1]
        for i in range(0, len(words), word_length):
            chunk = words[i : i + word_length]
            if (
                (i + word_length) > len(words)
                and (len(chunk) < word_length)
                and (len(text_toks) != (idx + 1))
            ):
                # text_toks[idx + 1] = chunk + text_toks[idx + 1]
                text_toks[idx + 1] = (
                    chunk + text_toks[idx + 1][0],
                    text_toks[idx + 1][1],
                )
                continue
            chunk = " ".join(chunk).strip()
            chunk = f"[Page no. {idx+start_page}]" + " " + '"' + chunk + '"'
            chunks.append((chunk, page))

    return chunks


def download_pdf(url, save_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"PDF downloaded successfully and saved to {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download PDF: {e}")