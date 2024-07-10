from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import re
import os
import json
import subprocess
import requests


try:
    import pymupdf as fitz  # available with v1.24.3
except ImportError:
    import fitz

import numpy as np
from openai import OpenAI
from fitz import Document as FitzDocument
from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
from sklearn.neighbors import NearestNeighbors
from sentence_transformers import SentenceTransformer
from metaflow import Runner, Flow

router = APIRouter()

### Global variables ###
pdf = None
# Routes provided in pdf_chat.py assume a single PDF in memory.
# TODO: Fix this if we want to support multiple PDFs or multiple users.
text_ls = None  # List of text from the PDF.
chunks = None  # List of vectors/embeddings.

### Keys
assert "OPENAI_API_KEY" in os.environ, "Please set OPENAI_API_KEY environment variable."
oai_compatible_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    # base_url="http://0.0.0.0:8000/v1", api_key="not-used" # NIM
)

### Tuning and model selection. ###
DEFAULT_WORD_LENGTH = 100
DEFAULT_BATCH_SIZE = 1000
DEFAULT_N_NEIGHBORS = 8
TEXT_EMBEDDING_MODEL_INFO = {
    "model_name": "all-MiniLM-L6-v2",
    "model_framework": "sentence-transformers",
    "pretrained_model_provider": "Hugging Face",
    "use_case": "text-semantic-search",
}
LLM_MODEL_INFO = {
    "remote_path": "openAI",
    "local_path": None,
    "model_name": "gpt-4o",
    "model_version": None,
    "model_framework": "openai",
    "pretrained_model_provider": "OpenAI",
    "use_case": "document-chat",
}
FLOW_NAME = "PDFRAGIndexing"


# A model container M_search.
# M_search affects what the user is shown
# by modeling similarity between chunks of text in 1 to N PDFs.
# M_search uses sklearn.neighbors.NearestNeighbors over sentence-transformers embeddings.
class SemanticSearchModel:
    """
    Manager for a semantic search model.
    Use M_search = SemanticSearchModel() to create a new instance.
        M_search.fit(data) to fit the model when a PDF is uploaded.
        M_search(text) to get the nearest neighbors of a new text at inference time,
            to give the LLM a boost.

    args:
        None

    methods:
        fit(data: List[str], batch: int, n_neighbors: int) -> None:
            Fits the model M with the data.
        _get_text_embedding(texts: List[str], batch: int) -> np.ndarray:
            Returns the embeddings of the text.
    """

    def __init__(self):
        self.embedding_model = SentenceTransformer(
            TEXT_EMBEDDING_MODEL_INFO["model_name"]
        )
        self.fitted = False

    def _get_text_embedding(self, texts, batch_size=DEFAULT_BATCH_SIZE):
        """
        Gather a stack of embedded texts, packed batch_size at a time.
        """
        embeddings = []
        n_texts = len(texts)
        for batch_start_idx in range(0, n_texts, batch_size):
            text_batch = texts[batch_start_idx : (batch_start_idx + batch_size)]
            embedding_batch = self.embedding_model.encode(text_batch)
            embeddings.append(embedding_batch)
        print("[DEBUG] Embedding batches:", len(embeddings))
        embeddings = np.vstack(embeddings)
        print("[DEBUG] Embedding reshaped:", embeddings.shape)
        return embeddings

    def fit(self, data, batch_size=DEFAULT_BATCH_SIZE, n_neighbors=DEFAULT_N_NEIGHBORS):
        """
        Fit the model conditioned on nearest neighbors in sentence-transformers embedding space of a PDF.
        """
        self.data = data
        self.embeddings = self._get_text_embedding(data, batch_size=batch_size)
        n_neighbors = min(n_neighbors, len(self.embeddings))
        print(
            "[DEBUG] Fitting Nearest Neighbors model with %s neighbors." % n_neighbors
        )
        self.nn = NearestNeighbors(n_neighbors=n_neighbors)
        self.nn.fit(self.embeddings)
        print("[DEBUG] Fit complete.")
        self.fitted = True

    def __call__(self, text, return_data=True):
        """
        Inference time method.
        Return the nearest neighbors of a new text.
        """
        print("[DEBUG] Getting nearest neighbors of text:", text)
        embedding = self.embedding_model.encode([text])
        print("[DEBUG] Embedding:", embedding.shape)
        neighbors = self.nn.kneighbors(embedding, return_distance=False)[0]
        if return_data:
            return [self.data[text_neighbs] for text_neighbs in neighbors]
        else:
            return neighbors


M_search = SemanticSearchModel()
# M_search is used in routes as a Python global variable. 😬


# @router.post("/return-fit-chart")
# async def return_fit_chart():
#     from metaflow import Flow, namespace
#     flow = Flow(FLOW_NAME)
#     namespace(None)
#     run = flow.latest_successful_run
#     print(f"{run.id} finished")
#     json_content = run.data.chart_json
#     return JSONResponse(content=json_content, status_code=200)


@router.post("/upload-url-list-file")
async def upload_url_from_file_list(text_ls: str):
    """
    Run a Metaflow workflow to download PDFs from a list of URLs.
    """
    print("[INFO] Received: ", text_ls)
    filename = "pdfList.txt"
    with open(filename, "w") as f:
        f.write(text_ls)
    with Runner("pdf_batch_flow.py", environment="pypi").run(
        url_list=filename
    ) as running:
        import time

        while running.status == "running":
            time.sleep(3)
        print(f"{running.run} finished")
        print(f"Run status is {running.status}")

        if running.status == "successful":
            global M_search
            flow = Flow(FLOW_NAME)
            run = flow.latest_successful_run
            M_search = run.data.model
            json_content = run.data.chart_json
            return JSONResponse(content=json_content, status_code=200)
        else:
            return {"message": "ERROR. Metaflow workflow failed."}


@router.post("/upload-pdf-url")
async def upload_pdf_from_url(url: str, name: str):

    def download_pdf(url, save_path):
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(save_path, "wb") as file:
                file.write(response.content)
            print(f"PDF downloaded successfully and saved to {save_path}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download PDF: {e}")

    # Download the PDF file.
    pdf_file_path = f"data/{name.strip().replace(" ", "_")}.pdf"
    download_pdf(url, pdf_file_path)
    return pdf_to_rag(pdf_file_path)


@router.post("/upload-pdf-file")
async def upload_pdf_from_file(uf: UploadFile):
    """
    UploadFile request makes a spooled file.
    It does a kind of buffering, storing the file in memory to a size, then store it on disk.
    Read more: https://fastapi.tiangolo.com/tutorial/request-files/#file-parameters-with-uploadfile
    """

    print("[INFO] Received: ", uf.filename)
    # NOTE: dumb logging now. good time to tee stuff or use actual logger
    if uf.content_type != "application/pdf":
        return {"Error": "Only PDF files are allowed!"}
    pdf_file_path = f"data/{uf.filename}"
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(pdf_file_path, "wb") as f:
        f.write(pdf_bytes)

    return pdf_to_rag(uf.file.read())


def pdf_to_rag(pdf_file_path):

    print("[INFO] Processing PDF: ", pdf_file_path)
    process_pdf(pdf_file_path)
    # Have now created the RAG+LLM inputs, including setting M_search.
    global M_search
    if M_search is None:
        return {
            "message": "ERROR. PDF upload isn't working because M_search hasn't been set."
        }
    print("[INFO] Organizing prompt...")
    prompt = ""
    prompt += "search results:\n\n"
    # TODO: Add a check for the prompt length, depending on model.
    question = "What are the key points of the document?"
    topn_chunks = M_search(question)  # RAG🌶️
    for similar_chunk in topn_chunks:
        prompt += similar_chunk + "\n\n"
    message_history = [
        {
            "role": "system",
            "content": "You are an insightful and wise assistant. You discuss topics related to the search results, and no others."
            "Instructions: Provide an executive summary of the documents. "
            "Weave responses and citations into a coherent and succinct paragraph in the answer key of the output JSON. "
            "Answer step-by-step."
            "Return a JSON object with the following format: \n\n"
            "\n\n{\n"
            f'  "query": "{question}",\n'
            '   "summary": "...",\n',
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]
    # print("[INFO] Sending request to OpenAI.", message_history)
    completion = oai_compatible_client.chat.completions.create(
        model=LLM_MODEL_INFO["model_name"],
        messages=message_history,
        response_format={"type": "json_object"},
    )
    out_json = completion.choices[0].message.content
    # TODO: Postprocessing.
    return json.loads(out_json)


@router.get("/pdf-chat")
async def pdf_chat(question: str, ctx_messages: str):

    global M_search
    if M_search is None:
        return {"message": "ERROR. Upload a PDF file before chatting."}

    ctx_messages = json.loads(ctx_messages)
    prompt = ""
    prompt += "search results:\n\n"
    topn_chunks = M_search(question)
    for c in topn_chunks:
        prompt += c + "\n\n"
    message_history = [
        {
            "role": "system",
            "content": "You are an insightful and wise assistant that helps contextualize PDF documents. "
            "You discuss topics related to the search results, and no others, and you help your counterpart find what they are looking for quickly."
            "Instructions: Only reply to the query based on the search results given. "
            "Respond succinctly and precisely. Be informative but add minimal fluff."
            "Anchor responses based on the search results."
            "Cite each reference using [ Page N ] notation."
            "(every result has this number at the beginning). "
            "Weave responses and citations into a coherent and succinct paragraph in the answer key of the output JSON. "
            "Citation should also be done in a separate JSON field. "
            "Only include information found in the results and "
            "only answer what is asked. "
            "Return a JSON object with the following format: \n\n"
            "{\n"
            f'  "query": "{question}",\n'
            f'  "citations": "[<Page Number>]",\n'
            '  "answer": "Answer here"\n'
            "}\n\n"
            "Answer step-by-step. Include the page number in the most relevant citations. "
            "\n\n{\n"
            f'  "query": "{question}",\n'
            '   "citations": "...",\n'
            '   "answer": "...",\n',
        },
        *ctx_messages,
        {
            "role": "user",
            "content": prompt,
        },
    ]

    # TODO: Add a check for the prompt length, depending on model.
    # TODO: Content moderation. Flag PII.

    completion = oai_compatible_client.chat.completions.create(
        model=LLM_MODEL_INFO["model_name"],
        messages=message_history,
        response_format={"type": "json_object"},
    )
    out_json = completion.choices[0].message.content

    # TODO: Log request/response/and stuff in a to-be-eval'd DB.

    return json.loads(out_json)


def process_pdf(pdf_file_path):
    """
    This function processes the PDF file and prepares the data for the LLM.
    It is called pretty soon after the user uploads a PDF file.

    Extract text from the PDF file.
    Split the text into chunks.
    **Side effect**: store chunks. Fit new M_search. Set text_ls and chunks too based on new PDF.
    Make a new SemanticSearchModel model, put it in M_search and fit it with the chunks.
    """
    global M_search, text_ls, chunks
    # TODO part 1: user has been waiting since request gets to API server.
    text_ls = pdf_to_text(pdf_file_path)
    chunks = text_to_chunks(text_ls)
    M_search.fit([c[0] for c in chunks])
    # TODO part 2: now loading screen stops for user.
    return chunks


################################################################
# Following is based on this repo:
# https://github.com/bhaskatripathi/pdfGPT/blob/main/api.py#L105
################################################################


def preprocess(text):
    """
    Apply rules to process one string of text that is extracted from a PDF.
    """
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def pdf_to_text(path, start_page=1, end_page=None):
    """
    Extracts text from a PDF file and preprocesses it.
    """
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


def text_to_chunks(
    texts,  # list of Dict[Tuple] like {'content'='', 'page': int})
    word_length=DEFAULT_WORD_LENGTH,
    start_page=1,
):
    text_toks = [(t["content"].split(" "), t["page"]) for t in texts]
    text_toks_len = len(text_toks)
    chunks = []
    for token_idx, words_and_page in enumerate(text_toks):
        words = words_and_page[0]
        n_words = len(words)
        page = words_and_page[1]
        for i in range(0, n_words, word_length):
            chunk = words[i : i + word_length]
            chunk_sz = len(chunk)
            if (
                (i + word_length) > n_words
                and (chunk_sz < word_length)
                and (text_toks_len != (token_idx + 1))
            ):
                text_toks[token_idx + 1] = (
                    chunk + text_toks[token_idx + 1][0],
                    text_toks[token_idx + 1][1],
                )
                continue
            chunk_join = " ".join(chunk).strip()
            # TODO: Improve way to add page number citation.
            # Rely less on LLM to do citation through token generation, maybe 🤨.
            chunk = f"[Page no. {token_idx+start_page}]" + " " + '"' + chunk_join + '"'
            chunks.append((chunk, page))
    return chunks
