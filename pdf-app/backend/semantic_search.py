from sklearn.neighbors import NearestNeighbors
from sklearn.manifold import TSNE
from sentence_transformers import SentenceTransformer
import altair as alt
import numpy as np
import pandas as pd
import json


TEXT_EMBEDDING_MODEL_INFO = {
    "model_name": "all-MiniLM-L6-v2",
    "model_framework": "sentence-transformers",
    "pretrained_model_provider": "Hugging Face",
    "use_case": "text-semantic-search",
}


class SemanticSearchModel:
    """
    Manager for a semantic search model.

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

    def _get_text_embedding(self, texts, files, batch_size=1000):
        """
        Gather a stack of embedded texts, packed batch_size at a time.
        """
        embeddings = []
        file_emb = []
        n_texts = len(texts)
        for batch_start_idx in range(0, n_texts, batch_size):
            file_batch = files[batch_start_idx : (batch_start_idx + batch_size)]
            text_batch = texts[batch_start_idx : (batch_start_idx + batch_size)]
            embedding_batch = self.embedding_model.encode(text_batch)
            embeddings.append(embedding_batch)
            file_emb.append(file_batch)

        print("[DEBUG] Embedding batches:", len(embeddings))
        embeddings = np.vstack(embeddings)
        file_emb = np.vstack(file_emb)
        print("[DEBUG] Embedding reshaped:", embeddings.shape, file_emb.shape)
        return embeddings, file_emb

    def fit(self, chunks, files, batch_size=1000, n_neighbors=6):
        """
        The only public method in this class.
        Fits the model with the data when a new PDF is uploaded.
        """
        self.chunks = chunks
        self.embeddings, file_emb = self._get_text_embedding(
            self.chunks, files, batch_size=batch_size
        )
        n_neighbors = min(n_neighbors, len(self.embeddings))
        print(
            "[DEBUG] Fitting Nearest Neighbors model with %s neighbors." % n_neighbors
        )
        self.nn = NearestNeighbors(n_neighbors=n_neighbors)
        self.nn.fit(self.embeddings)
        print("[DEBUG] Fit complete.")
        self.fitted = True

        tsne = TSNE(n_components=2, random_state=77)
        embeddings_2d = tsne.fit_transform(self.embeddings)

        df = pd.DataFrame(embeddings_2d, columns=["x", "y"])

        # df['color'] = 'blue'
        df["text"] = self.chunks

        chart = (
            alt.Chart(df)
            .mark_circle(size=60)
            .encode(
                x="x",
                y="y",
                tooltip=["text"],
                # color=alt.value('blue')
            )
            .properties(title="Text Embeddings Visualization")
        )

        vega_lite_spec = chart.to_dict()
        with open("fit_chart.json", "w") as f:
            f.write(json.dumps(vega_lite_spec))

        # chart.save('fit_chart.json')
        print("[DEBUG] Fit visualization saved as 'fit_chart.json'")

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
