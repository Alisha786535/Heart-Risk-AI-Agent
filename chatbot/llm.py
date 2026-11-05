"""Provider-agnostic LLM layer.

LLM_PROVIDER=offline        → rule-based, no network, no cost (default)
LLM_PROVIDER=openai_compat  → any OpenAI-compatible server: Ollama (local, free), Groq, Gemini's
                              OpenAI endpoint, OpenAI, ...  Set LLM_BASE_URL, LLM_MODEL, LLM_API_KEY.
"""
from __future__ import annotations
import json, os, re
from dataclasses import dataclass, field
from core.diet import chart_to_text


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMError(Exception):
    pass


class OpenAICompatLLM:
    def __init__(self):
        self.base = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
        self.model = os.getenv("LLM_MODEL", "llama3.1")
        self.key = os.getenv("LLM_API_KEY", "ollama")

    def chat(self, messages, tools) -> LLMResponse:
        import requests
        try:
            r = requests.post(f"{self.base}/chat/completions", timeout=90,
                              headers={"Authorization": f"Bearer {self.key}"},
                              json={"model": self.model, "messages": messages, "tools": tools, "temperature": 0.3})
            r.raise_for_status()
            msg = r.json()["choices"][0]["message"]
        except Exception as e:
            raise LLMError(str(e)) from e
        calls = []
        for tc in msg.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append(ToolCall(tc.get("id", tc["function"]["name"]), tc["function"]["name"], args))
        return LLMResponse(msg.get("content") or "", calls)


# ── Offline mode: regex intent routing + deterministic wording ──────────────
HELP = ("I can help with: 🫀 your risk estimate, 🥗 a diet chart (say 'diet chart' or 'weekly diet'), "
        "📏 logging readings (e.g. 'BP 128/84' or 'fasting sugar 105'), 📈 trends, "
        "💡 recommendations, and explaining terms ('what is cholesterol?'). "
        "Fill in your profile in the sidebar first so I can personalise things.")


class OfflineLLM:
    def chat(self, messages, tools) -> LLMResponse:
        last = messages[-1]
        if last["role"] == "tool":
            tail = []
            for m in reversed(messages):
                if m["role"] != "tool":
                    break
                tail.append(m)
            return LLMResponse("\n\n".join(_format(m["name"], json.loads(m["content"])) for m in reversed(tail)))
        t = last["content"].lower()
        if (m := re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", t)):
            return _call("log_reading", kind="bp", value1=float(m[1]), value2=float(m[2]))
        if (m := re.search(r"(sugar|glucose)\D{0,25}(\d{2,3})", t)):
            ctx = "fasting" if "fasting" in t else "post_meal" if re.search(r"after|post|pp", t) else "random"
            return _call("log_reading", kind="glucose", value1=float(m[2]), context=ctx)
        if re.search(r"trend|average|history|my readings", t):
            return _call("get_reading_trend", kind="glucose" if re.search(r"sugar|glucose", t) else "bp",
                         days=30 if "month" in t else 7)
        if re.search(r"diet|meal|food|what (should|can) i eat", t):
            return _call("generate_diet_chart", days=7 if "week" in t else 1)
        if re.search(r"recommend|advice|tips|improve|what should i do", t):
            return _call("get_recommendations")
        if re.search(r"\brisk\b|heart attack|assess", t) and not re.search(r"what is|explain", t):
            return _call("get_risk_assessment")
        if (m := re.search(r"(?:what is|what's|explain|meaning of|define)\s+(?:an? |the )?(.+)", t)):
            return _call("explain_term", term=m[1])
        return LLMResponse(HELP)


def _call(name, **args) -> LLMResponse:
    return LLMResponse("", [ToolCall(f"call_{name}", name, args)])


def _format(name: str, r: dict) -> str:
    st = r.get("status")
    if st == "incomplete":
        return "I still need a few details: " + ", ".join(r["missing"]) + ". Please add them in the sidebar profile."
    if st in ("rejected", "error"):
        return "⚠️ " + r.get("reason", "Something went wrong.")
    if name == "get_risk_assessment":
        f = ", ".join(r["top_risk_factors"]) or "none of the main risk factors flagged"
        return (f"Your estimated risk is {r['risk_score_percent']}% ({r['risk_level']}). {r['message']}\n"
                f"Main factors: {f}.")
    if name == "get_recommendations":
        return "Top priorities for you:\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(r["priority_actions"], 1)) + \
               f"\n\nLifestyle score: {r['lifestyle_score']}/100. {r['monitoring_advice']}"
    if name == "generate_diet_chart":
        return chart_to_text(r)
    if name == "log_reading":
        val = f"{r['value1']:g}/{r['value2']:g} mmHg" if r["kind"] == "bp" else f"{r['value1']:g}"
        return f"Saved your {r['kind']} reading ({val}). Category: {r['category'].replace('_', ' ')}."
    if name == "get_reading_trend":
        if st == "empty":
            return f"No {r['kind']} readings in the last {r['days']} days yet."
        extra = f"/{r['avg2']}" if r["kind"] == "bp" else ""
        return (f"Last {r['days']} days: {r['count']} readings, average {r['avg1']}{extra}, "
                f"range {r['min1']:g}-{r['max1']:g}.")
    if name == "explain_term":
        return r.get("explanation") or f"I don't have a vetted explanation for “{r['term']}” yet. Please ask your doctor."
    if name == "update_profile":
        return "Saved: " + ", ".join(r["saved"]) if r["saved"] else "Nothing saved."
    return json.dumps(r)


def get_llm():
    return OpenAICompatLLM() if os.getenv("LLM_PROVIDER", "offline") == "openai_compat" else OfflineLLM()
