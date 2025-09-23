from fastapi import FastAPI
from workflow import list_channels, get_safe_spend_range, get_best_channel_by_roi
from AI import ai_answer

app = FastAPI()

# Define API endpoints
@app.get("/channels")
def channels():
    return list_channels()

# Single endpoint to ask a question about a specific channel
@app.get("/channel")
def channel(name: str, question:str ):
    return ai_answer(question, name)

# Endpoint to get safe spend range for a channel
@app.get("/safe_range")
def safe_range(name: str):
    return get_safe_spend_range(name)

# Endpoint to get the best channel by ROI
@app.get("/best_channel")
def best_channel():
    return get_best_channel_by_roi()

