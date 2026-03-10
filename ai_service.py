import json
import os
import re
from typing import Any, Dict, List

import httpx

# Load required env vars
_DIGITALOCEAN_INFERENCE_KEY = os.getenv("DIGITALOCEAN_INFERENCE_KEY")
_DO_INFERENCE_MODEL = os.getenv("DO_INFERENCE_MODEL", "openai-gpt-oss-120b")

_INFERENCE_ENDPOINT = "https://inference.do-ai.run/v1/chat/completions"

def _extract_json(text: str) -> str:
    """Extract the first JSON object or array from a string, handling markdown fences."""
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

async def _call_inference(messages: List[Dict[str, str]], max_tokens: int = 512) -> Dict[str, Any]:
    """Send a chat‑completion request to DigitalOcean inference and return parsed JSON.

    On any error a fallback dict with a ``note`` key is returned.
    """
    headers = {
        "Authorization": f"Bearer {_DIGITALOCEAN_INFERENCE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _DO_INFERENCE_MODEL,
        "messages": messages,
        "max_completion_tokens": max_tokens,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(_INFERENCE_ENDPOINT, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            # The AI returns a message content string – we expect JSON inside it
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            raw_json = _extract_json(content)
            return json.loads(raw_json) if raw_json else {"note": "Empty response from AI"}
    except Exception as exc:
        # Log could be added here; for now we just return a fallback
        return {"note": f"AI service temporarily unavailable: {str(exc)}"}

# ---------------------------------------------------------------------------
# Public helpers used by route handlers
# ---------------------------------------------------------------------------
async def generate_summary(url: str) -> Dict[str, Any]:
    """Ask the LLM to produce a concise summary for a given URL.

    The prompt is deliberately simple – in a production system we would fetch the page
    content first and pass it to the model.
    """
    messages = [
        {"role": "system", "content": "You are an assistant that creates concise, 2‑3 sentence summaries of web pages. Only respond with a JSON object containing a single key `summary`.",},
        {"role": "user", "content": f"Provide a summary for the following URL: {url}"},
    ]
    return await _call_inference(messages, max_tokens=512)

async def expand_search_query(query: str) -> Dict[str, Any]:
    """Ask the LLM to expand a user query into a richer semantic query.

    Returns a dict with at least ``expanded_query`` key.
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant that rewrites search queries to be more expressive and include related concepts. Respond only with JSON containing the key `expanded_query`."},
        {"role": "user", "content": f"Expand this search query: {query}"},
    ]
    return await _call_inference(messages, max_tokens=256)
