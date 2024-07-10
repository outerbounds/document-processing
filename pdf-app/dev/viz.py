import pandas as pd
from sklearn.manifold import TSNE
import altair as alt
import numpy as np

# num_chunks = 100
# embedding_dim = 512
# embeddings = np.random.rand(num_chunks, embedding_dim)
# document_ids = np.random.randint(0, 10, size=num_chunks)  # Assuming 10 documents

# Perform t-SNE to reduce dimensionality to 2D
tsne = TSNE(n_components=2, random_state=42)
embeddings_2d = tsne.fit_transform(embeddings)

# Create a DataFrame for visualization
df = pd.DataFrame(embeddings_2d, columns=["x", "y"])
df["document_id"] = document_ids
df["chunk_id"] = range(num_chunks)

# Visualize using Altair
chart = (
    alt.Chart(df)
    .mark_circle(size=60)
    .encode(x="x", y="y", color="document_id:N", tooltip=["document_id", "chunk_id"])
    .properties(title="Document Chunks Visualization")
)

# Save the chart as an HTML file
chart.save("chart.html")
