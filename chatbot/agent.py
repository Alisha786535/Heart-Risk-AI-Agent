"""Chat orchestration: safety first → LLM + tools → deterministic safety/disclaimer footers."""
from __future__ import annotations
import json, logging
from core import db, safety
from core.diet import DISCLAIMER as DIET_DISCLAIMER
from core.risk import DISCLAIMER as RISK_DISCLAIMER
from chatbot.llm import get_llm, OfflineLLM, LLMError
from chatbot.tools import TOOLS, run_tool

log = logging.getLogger(__name__)
MAX_ROUNDS = 4

SYSTEM_PROMPT = """You are CardioGuide, a friendly heart-health assistant inside a demo app.
Rules:
- Use tools for ANY number (risk, calories, readings, trends). Never invent or estimate numbers yourself.
- Do not diagnose, prescribe, or change medication. For medical decisions say: please ask your doctor.
- If the user gives personal facts (age, weight, readings...), save them with update_profile / log_reading.
- If a tool reports missing fields, ask for them ONE at a time in simple words.
- Keep answers short, warm and practical. Explain terms simply. Stay on heart, diet and wellbeing topics.
- If anything sounds like an emergency (chest pain, breathlessness, fainting), tell them to call emergency services."""


def _assistant_msg(resp):
    return {"role": "assistant", "content": resp.content or "", "tool_calls": [
        {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(c.args)}}
        for c in resp.tool_calls]}


def handle_message(user_id: str, text: str, llm=None) -> dict:
    db.add_message(user_id, "user", text)
    emergency = safety.check_text(text)
    if emergency:                       # never reaches the LLM
        db.add_message(user_id, "assistant", emergency)
        return {"reply": emergency, "tool_results": [], "emergency": True}

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + db.get_history(user_id, 12)
    llm, results, note = llm or get_llm(), [], ""
    for _ in range(MAX_ROUNDS):
        try:
            resp = llm.chat(messages, TOOLS)
        except LLMError as e:
            log.warning("LLM failed (%s); falling back to offline mode", e)
            llm, note = OfflineLLM(), "\n\n(Smart chat is unavailable right now, so I'm using basic mode.)"
            resp = llm.chat(messages, TOOLS)
        if not resp.tool_calls:
            reply = resp.content or "Sorry, I couldn't work that out. Could you rephrase?"
            break
        messages.append(_assistant_msg(resp))
        for c in resp.tool_calls:
            r = run_tool(c.name, c.args, user_id)
            results.append({"name": c.name, "result": r})
            messages.append({"role": "tool", "tool_call_id": c.id, "name": c.name, "content": json.dumps(r)})
    else:
        reply = "That took too many steps. Could you ask in a simpler way?"

    names = {x["name"] for x in results}
    for x in results:                   # deterministic alerts, not up to the LLM
        alert = (x["result"] or {}).get("alert")
        if alert:
            reply += f"\n\n🚨 {alert['message']}"
    if names & {"get_risk_assessment", "get_recommendations"}:
        reply += f"\n\nℹ️ {RISK_DISCLAIMER}"
    if "generate_diet_chart" in names:
        reply += f"\n\nℹ️ {DIET_DISCLAIMER}"
    reply += note
    db.add_message(user_id, "assistant", reply)
    return {"reply": reply, "tool_results": results, "emergency": False}
