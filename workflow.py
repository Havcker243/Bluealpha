import json


with open("model_output.json", "r") as f:
    data = json.load(f)

def list_channels():
    """Return available channel names/ids."""
    return [ch["name"] for ch in data["channels"]]

def answer_channel_question(channel_name: str):
    for ch in data["channels"]:
        if ch["name"].lower() == channel_name.lower() or ch["id"] == channel_name.lower():
            return {
                "answer": f"In {data['period']}, {ch['name']} contributed {ch['contribution_pct']*100:.1f}% "
                          f"(≈${ch['incremental_kpi']:.0f}) on ${ch['spend']:.0f} spend. ROI ≈ {ch['roi']:.2f}.",
                "explanation": f"The curve shows diminishing returns (Hill) near ~${ch['hill']['half_sat']} "
                               f"and adstock carryover with decay {ch['adstock']['decay']}.",
                "guardrails": f"Observed spend range: ${ch['observed_spend_min']}–${ch['observed_spend_max']}.",
                "source": {
                    "model_version": data["model_version"],
                    "period": data["period"],
                    "channel": ch["id"]
                },
                "confidence": "High"
            }
    return {"error": f"Channel {channel_name} not found"}

def get_safe_spend_range(channel_name: str):
    """Return safe observed spend range."""
    for ch in data["channels"]:
        if ch["name"].lower() == channel_name.lower() or ch["id"] == channel_name.lower():
            return {
                "answer": f"Safe spend range for {ch['name']} in {data['period']}: "
                          f"${ch['observed_spend_min']}–${ch['observed_spend_max']}.",
                "guardrails": "Avoid extrapolating outside this range.",
                "source": {
                    "model_version": data["model_version"],
                    "period": data["period"],
                    "channel": ch["id"]
                }
            }
    return {"error": f"Channel {channel_name} not found"}

def get_best_channel_by_roi():
    """Find channel with highest ROI."""
    best = max(data["channels"], key=lambda ch: ch["roi"])
    return {
        "answer": f"In {data['period']}, {best['name']} had the highest ROI ≈ {best['roi']:.2f}.",
        "explanation": f"Contribution was {best['contribution_pct']*100:.1f}% "
                       f"(≈${best['incremental_kpi']:.0f}) on ${best['spend']:.0f} spend.",
        "source": {
            "model_version": data["model_version"],
            "period": data["period"],
            "channel": best["id"]
        },
        "confidence": "High"
    }