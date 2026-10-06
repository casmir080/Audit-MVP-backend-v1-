"""
Thin wrapper around the LLM API so the rest of the codebase never talks to
a specific provider directly. If you swap providers later, this is the
only file that changes.

Using QwenCloud via DashScope's OpenAI-compatible endpoint here, to match
what Rampamble already runs on - same account, same API key, nothing new
to set up. Double-check the base_url below against whatever you actually
used in Rampamble's code; DashScope has region-specific endpoints and I
don't have your original file to copy it from exactly.
"""
import os
import re
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()  # reads .env into os.environ - this was missing before

_client = AsyncOpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
MODEL = "qwen3.7-max"


async def call_llm(prompt: str, max_tokens: int = 2000) -> str:
    response = await _client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def extract_json(raw: str) -> str:
    """
    Models don't always follow "return ONLY JSON" literally every time -
    sometimes it's wrapped in a ```json fence, sometimes there's a stray
    word before or after it. Strip that instead of letting json.loads
    crash the whole request over formatting the model didn't quite follow.
    """
    if raw is None:
        raise ValueError("LLM returned an empty response - check the API call succeeded")
    raw = raw.strip()
    if not raw:
        raise ValueError("LLM returned an empty response - check the API call succeeded")
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        raw = raw.strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]
    return raw