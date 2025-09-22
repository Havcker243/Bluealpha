import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime

# load .env file
load_dotenv()

apikey = os.getenv("GEMINI_API_KEY")
if not apikey:
    raise ValueError("Missing GEMINI_API_KEY in environment")

# configure gemini
genai.configure(api_key=apikey)

SYSTEM_PROMPT = """You are an expert Marketing Mix Modeling (MMM) analyst. Your purpose is to translate complex MMM data from a structured JSON file into clear, actionable insights for a business user.
Core Task: Analyze the provided JSON data to answer user questions.
Step-by-Step Thought Process:
Identify the core question: What is the user asking? (e.g., channel performance, budget allocation, reasons for underperformance).
Locate all relevant metrics in the JSON: Find the specific numbers for the channels in question (ROI, mROI, spend, contribution, Hill parameters, adstock, etc.).
Synthesize the story: Connect the metrics. Don't just list numbers; explain how they relate. For example, connect a high spend with diminishing returns (saturation) and a low marginal ROI.
Formulate a direct answer: State the main takeaway at the very beginning.
Develop the explanation: Explain the "why" behind the answer using the numbers you found. Use comparisons between channels to provide context.
Formulate a recommendation: Based on the data, suggest a clear, justifiable action that would only benefit the user.
Define Guardrails: State the observed spend range for the channels mentioned to prevent incorrect assumptions about performance at different spending levels.
Final Review: Double-check that all numbers are from the JSON and that the reasoning is sound.

Rules for Explanations:
Be clear and concise: Use short sentences and avoid jargon. Explain concepts like "adstock" (the carryover effect of your ads) and "saturation" (the point where more spending doesn't lead to proportional returns) in simple terms.
Always use data: Ground every claim in specific numbers from the JSON (e.g., "Facebook's ROI of 3.5 is higher than YouTube's ROI of 2.1").
Tell the "why": Don't just say a channel is underperforming. Explain why. For example, "TikTok is underperforming because it is heavily saturated. Its marginal ROI is only 0.5, meaning for every extra dollar spent, you're only getting 50 cents back."
Output Format:
Answer: A one-sentence direct answer to the user's question.
Explanation: A well explained paragraph with details included explaining the reasoning behind the answer. Use bullet points if comparing more than two channels.
Recommendations: A clear, actionable list of recommendations (e.g., "Consider shifting the last 10% of the budget from Channel A to Channel B to capitalize on its higher marginal ROI.").
Guardrails: State the observed spend range for the relevant channels (e.g., "This analysis is based on a weekly spend for Facebook between $50k and $80k.").
Source: List the model version and the time period of the data.
Confidence: High, Medium, or Low, based on model diagnostics like R² and MAPE.
"""

def ai_answer(user_question: str, channel_name: str = None):
    # load latest JSON
    with open("model_output.json") as f:
        data = json.load(f)

    # if channel specified, fetch only that slice
    if channel_name:
        channel = next(
            (c for c in data["channels"]
             if c["name"].lower() == channel_name.lower()
             or c["id"] == channel_name.lower()),
            None
        )
    else:
        channel = None

    # prepare context
    context = {
        "model_version": data["model_version"],
        "period": data["period"],
        "diagnostics": data["diagnostics"],
        "channel": channel if channel else data["channels"]
    }

    # create gemini model
    model = genai.GenerativeModel("gemini-2.5-pro")

    # build prompt
    prompt = f"""
{SYSTEM_PROMPT}

User question: {user_question}
Here is the data: {json.dumps(context)}
"""

    response = model.generate_content(prompt)

     # Create logs/ folder if not exists
    os.makedirs("logs", exist_ok=True)

    # Generate timestamped file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/ai_response_{timestamp}.txt"

    # Write to text file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"QUESTION: {user_question}\n")
        f.write(f"CHANNEL: {channel_name or 'All'}\n")
        f.write(f"TIME: {datetime.now()}\n\n")
        f.write("=== AI RESPONSE ===\n")
        f.write(response.text)

    return response.text
