from metaflow import (
    FlowSpec,
    step,
    current,
    project,
    Flow,
    IncludeFile,
    Parameter,
    card,
)
from metaflow.cards import Markdown, ProgressBar, VegaChart
import math, os, time, io, csv
from itertools import islice

from metaflow import nim

MODEL = "meta/llama3-8b-instruct"
PROMPT = "answer with one word HAPPY if the sentiment of the following sentence is positive, otherwise answer with one word SAD"


def make_batches(items, n):
    bs = math.ceil(len(items) / n)
    return [items[i * bs : (i + 1) * bs] for i in range(n)]


@nim(models=[MODEL])
class ReviewSentimentFlow(FlowSpec):

    num_parallel = Parameter("num_parallel", default=5)
    review_csv = IncludeFile("reviews", default="reviews.csv")

    @step
    def start(self):
        self.reviews = [
            row["Review Text"] for row in csv.DictReader(io.StringIO(self.review_csv))
        ]
        print("Number of reviews:", len(self.reviews))
        self.batches = make_batches(self.reviews, self.num_parallel)
        self.next(self.prompt, foreach="batches")

    @card(type="blank", refresh_interval=1)
    @step
    def prompt(self):
        import sentiment_chart

        progress = ProgressBar(max=len(self.input) - 1, label="Reviews processed")
        text = Markdown()
        chart = VegaChart(sentiment_chart.spec())
        current.card.append(Markdown(f"## Prompt\n### {PROMPT}"))
        current.card.append(progress)
        current.card.append(chart)
        current.card.append(text)

        # get a client connected to the NIM container
        llm = current.nim.models[MODEL]

        counts = {"HAPPY": 0, "SAD": 0}
        latest = []
        self.results = []
        for i, review in enumerate(self.input):
            if review:

                # send a prompt to the LLM
                prompt = {"role": "user", "content": f"{PROMPT}: {review}"}
                chat_completion = llm(messages=[prompt], model=MODEL)
                sentiment = chat_completion["choices"][0]["message"]["content"]

                if sentiment in counts:
                    counts[sentiment] += 1
                    self.results.append((review, sentiment))

                    latest.append(f"**{sentiment}** - {review[:150]}...")
                    text.update("\n\n".join(list(reversed(latest))[:50]))

                    chart.update(sentiment_chart.spec(**counts))
                    progress.update(i)
                    current.card.refresh()
        self.next(self.join)

    @step
    def join(self, inputs):
        self.results = []
        for inp in inputs:
            self.results.extend(inp.results)
        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    ReviewSentimentFlow()
