from fastapi import FastAPI
from workflow import list_channels, get_safe_spend_range, get_best_channel_by_roi
from AI import ai_answer

app = FastAPI()

@app.get("/channels")
def channels():
    return list_channels()

@app.get("/channel")
def channel(name: str, question:str ):
    return ai_answer(question, name)

@app.get("/safe_range")
def safe_range(name: str):
    return get_safe_spend_range(name)

@app.get("/best_channel")
def best_channel():
    return get_best_channel_by_roi()

