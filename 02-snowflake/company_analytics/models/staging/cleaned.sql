WITH base AS (
    SELECT 
        COUNTRY,
        CASE 
            WHEN LENGTH(FOUNDED) = 4 THEN CAST(FOUNDED AS INTEGER)
            ELSE NULL
        END AS FOUNDED,
        ID,
        UPPER(INDUSTRY) AS INDUSTRY,
        CASE 
            WHEN LINKEDIN_URL LIKE 'http%' THEN LINKEDIN_URL
            ELSE 'https://' || LINKEDIN_URL
        END AS LINKEDIN_URL_TRANSFORMED,
        INITCAP(LOCALITY) AS LOCALITY,
        NAME,
        INITCAP(REGION) AS REGION,
        CASE 
            WHEN SIZE LIKE '%-%' THEN SIZE
            ELSE NULL
        END AS SIZE,
        CASE 
            WHEN WEBSITE LIKE 'http%' THEN WEBSITE
            ELSE 'https://' || WEBSITE
        END AS WEBSITE_TRANSFORMED,
        "completion_tokens" as COMPLETION_TOKENS,
        "description" as DESCRIPTION,
        "model" as MODEL,
        "prompt" as PROMPT,
        "prompt_tokens" as PROMPT_TOKENS,
        "raw_completion" as RAW_COMPLETION,
        "return_code" as RETURN_CODE,
        "system_fingerprint" as SYSTEM_FINGERPRINT,
        "total_tokens" as TOTAL_TOKENS,
        "uses_ai" as USES_AI,
        LINKEDIN_URL
    from {{ source('market_intel', 'MARKET_INTEL') }}
),

derived AS (
    SELECT
        COUNTRY,
        FOUNDED,
        ID,
        INDUSTRY,
        LINKEDIN_URL_TRANSFORMED AS LINKEDIN_URL,
        LOCALITY,
        NAME,
        REGION,
        SIZE,
        WEBSITE_TRANSFORMED AS WEBSITE,
        COMPLETION_TOKENS,
        DESCRIPTION,
        MODEL,
        PROMPT,
        PROMPT_TOKENS,
        RAW_COMPLETION,
        RETURN_CODE,
        SYSTEM_FINGERPRINT,
        TOTAL_TOKENS,
        USES_AI,
        EXTRACT(YEAR FROM CURRENT_DATE) - FOUNDED AS COMPANY_AGE,
        CASE 
            WHEN USES_AI = 1 THEN TRUE
            ELSE FALSE
        END AS USES_AI_FLAG
    FROM base
)

SELECT * FROM derived