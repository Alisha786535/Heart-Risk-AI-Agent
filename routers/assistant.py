"""Chatbot, profile, readings and diet-chart endpoints.
NOTE: `user_id` is a plain identifier for now. Replace with a real auth token before public deployment."""
import os
from typing import Optional, Literal
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from core import db
from chatbot.agent import handle_message
from chatbot import tools

UID = Field(..., min_length=1, max_length=64, pattern=r"^[\w.@+-]+$")


def require_key(x_api_key: Optional[str] = Header(default=None)):
    expected = os.getenv("API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(401, "Invalid or missing X-API-Key")


router = APIRouter(prefix="/assistant", tags=["🤖 Assistant"], dependencies=[Depends(require_key)])


class ChatIn(BaseModel):
    user_id: str = UID
    message: str = Field(..., min_length=1, max_length=2000)


class ProfileIn(BaseModel):
    user_id: str = UID
    fields: dict


class ReadingIn(BaseModel):
    user_id: str = UID
    kind: Literal["bp", "glucose", "hr"]
    value1: float
    value2: Optional[float] = None
    context: Literal["fasting", "post_meal", "random"] = "random"
    source: str = Field("manual", max_length=32)


class DietIn(BaseModel):
    user_id: str = UID
    days: int = Field(1, ge=1, le=7)


@router.post("/chat")
def chat(body: ChatIn):
    return handle_message(body.user_id, body.message)


@router.get("/history")
def history(user_id: str = Query(..., pattern=r"^[\w.@+-]+$", max_length=64), limit: int = Query(30, le=100)):
    return {"messages": db.get_history(user_id, limit)}


@router.put("/profile")
def put_profile(body: ProfileIn):
    return tools.update_profile(body.user_id, body.fields)


@router.get("/profile")
def get_profile(user_id: str = Query(..., pattern=r"^[\w.@+-]+$", max_length=64)):
    prof = db.get_profile(user_id)
    return {"profile": prof, "missing_for_risk": tools.missing_for_risk(prof)}


@router.post("/readings")
def post_reading(body: ReadingIn):
    """Manual entry today; sensors/gateways (ESP32, BLE cuff) POST here with their own `source`."""
    r = tools.log_reading(body.user_id, body.kind, body.value1, body.value2, body.context, body.source)
    if r["status"] == "rejected":
        raise HTTPException(422, r["reason"])
    return r


@router.get("/readings")
def list_readings(user_id: str = Query(..., pattern=r"^[\w.@+-]+$", max_length=64),
                  kind: Optional[Literal["bp", "glucose", "hr"]] = None, days: int = Query(30, le=365)):
    return {"readings": db.get_readings(user_id, kind, days)}


@router.post("/diet-chart")
def diet_chart(body: DietIn):
    return tools.make_diet_chart(body.user_id, body.days)
