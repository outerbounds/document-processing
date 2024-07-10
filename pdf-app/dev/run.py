import asyncio
from metaflow import Runner


async def main():
    with await Runner("batch_pdfchat.py", environment='pypi').async_run(local_pdf_path='pdfs') as running:
        while running.status == "running":
            async for _, line in running.stream_log("stdout"):
                print(line)
            await asyncio.sleep(1)
        print(f"{running.run} finished")
        print(f"Run status is {running.status}")


asyncio.run(main())
