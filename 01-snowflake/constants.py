### SNOWFLAKE CONFIG
MARKETPLACE_DB = "FREE_COMPANY_DATASET"
SCHEMA = "public"
WH = "compute_wh"
OUT_TABLE_NAME = "MARKET_INTEL"
COMPANY_DATA_QUERY = r"""select * from FREECOMPANYDATASET
where COUNTRY = 'united states' AND
      FOUNDED IS NOT NULL AND
      INDUSTRY IS NOT NULL AND
      LOCALITY IS NOT NULL AND
      WEBSITE IS NOT NULL AND
      TO_NUMBER(REGEXP_SUBSTR(SIZE, '\\d+$')) > 200; 
"""
OUTPUTS_DB = "FREE_COMPANY_DATASET_OUTPUTS"
CREATE_OUTPUT_DB_QUERY = f"""CREATE DATABASE IF NOT EXISTS {OUTPUTS_DB}"""

### OPENAI CONFIG
GPT_MODEL = "gpt-4o"
SYSTEM_PROMPT = """You are a helpful research assistant. 
You will be given a summary of the contents of a web site's landing page.
Summarize and output JSON with a one line description of what the company does and how it relates to AI, and a boolean that classifies whether the company is likely using AI/ML.
The JSON should have this structure: {"description": "OpenAI is an AI research firm.", "uses_ai": true}.
Do not output anything except the JSON. Be creative in imagining what the company does and how they might use AI. 
"""
USER_PROMPT_TEMPLATE = """Here are the summarized contents of the landing page:
{content}
"""
