from metaflow import (
    FlowSpec,
    step,
    pypi_base,
    pypi,
    Parameter,
    IncludeFile,
    card,
    current,
    S3,
    environment,
)
from metaflow.cards import Table
import os


@pypi_base(python="3.12")
class PDFRAGIndexing(FlowSpec):

    local_pdf_path = Parameter(
        "local_pdf_path",
        help="Local directory containing the PDF files.",
    )
    url_list = IncludeFile(
        "url_list",
        help="A file containing a mapping between PDF URLs and names.",
        default="pdfList.txt",
        is_text=True,
    )
    tmp_dir = "/tmp/pdf"

    @step
    def start(self):
        import os
        from pdf_utils import download_pdf

        if self.local_pdf_path is None and self.url_list is None:
            raise ValueError(
                "Either local_pdf_path or local_pdf_path or url_list param must be provided."
            )

        self.s3_pdf_paths = []
        if self.url_list is not None:
            for line in self.url_list.split("\\n"):
                split = line.strip().split(": ")
                name, url = split[0], split[1]
                name = name.strip() + ".pdf"
                if not url.startswith("http"):
                    raise ValueError(f"Invalid URL: {url}")
                if not os.path.exists(self.tmp_dir):
                    os.makedirs(self.tmp_dir)
                local_tmp_path = f"{self.tmp_dir}/{name}"
                download_pdf(url, local_tmp_path)
                with S3(run=self) as s3:
                    s3.put_files([(name, local_tmp_path)])
                    self.s3_pdf_paths.append(name)

        if self.local_pdf_path is not None:
            if not os.path.exists(self.local_pdf_path):
                raise FileNotFoundError(
                    f"Directory {self.local_pdf_path} does not exist."
                )

            with S3(run=self) as s3:
                for root, _, files in os.walk(self.local_pdf_path):
                    for file in files:
                        s3.put_files([(file, os.path.join(root, file))])
                        self.s3_pdf_paths.append(file)

        self.next(self.extract_text, foreach="s3_pdf_paths")

    @pypi(packages={"pymupdf": "1.24.6"})
    @step
    def extract_text(self):
        from pdf_utils import pdf_to_text, text_to_chunks

        self.file_name = self.input
        self.pdf_path = f"{self.tmp_dir}/{self.file_name}"
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        with S3(run=self) as s3:
            obj = s3.get(self.input)
            os.rename(obj.path, self.pdf_path)
        text_ls = pdf_to_text(self.pdf_path)
        self.chunks = text_to_chunks(text_ls)
        self.next(self.join)

    @card
    @pypi(
        packages={
            "sentence-transformers": "3.0.1",
            "scikit-learn": "1.5.0",
            "altair": "5.3.0",
            "pandas": "2.2.2",
        }
    )
    @environment(vars={"TOKENIZERS_PARALLELISM": "false"})
    @step
    def join(self, inputs):
        self.chunks = []
        for i in inputs:
            for c in i.chunks:
                self.chunks.append([c[0], c[1], i.file_name])
        current.card.append(Table(headers=["Chunk", "Page", "File"], data=self.chunks))
        self.model = self._fit([c[0] for c in self.chunks])
        self.next(self.end)

    def _fit(self, chunks):
        from semantic_search import SemanticSearchModel

        recommender = SemanticSearchModel()
        recommender.fit(chunks)
        with open("fit_chart.html", "r") as f:
            self.chart_html = f.read()
        return recommender

    @step
    def end(self):
        pass


if __name__ == "__main__":
    PDFRAGIndexing()
