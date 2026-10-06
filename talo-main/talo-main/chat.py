"""
Lets a compliance officer ask natural-language questions about their own
uploaded data and drift results, instead of only reading a static report.
This is the piece that makes the product feel like an AI tool, not a PDF
generator with a model quietly doing the writing in the background.
"""
import json
from fastapi import APIRouter
from pydantic import BaseModel
from llm_client import call_llm

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    drift_results: dict
    normalized_rows: list[dict]
    conversation_history: list[dict] = []  # [{"role": "user"/"assistant", "content": "..."}]


@router.post("/ask")
async def ask(req: ChatRequest):
    context = f"""You are answering a compliance officer's question about
their own institution's AI system, based on the drift analysis and
transaction data below. Be specific, cite the actual numbers you were
given, and say plainly if the data doesn't support an answer.

Drift results:
{json.dumps(req.drift_results, indent=2)}

Sample data ({len(req.normalized_rows)} total rows, showing first 10):
{json.dumps(req.normalized_rows[:10], indent=2, default=str)}

Question: {req.question}"""

    answer = await call_llm(context, max_tokens=600)
    return {"answer": answer}
