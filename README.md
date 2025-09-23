# MMM AI Interpretation Layer

## Overview
An AI-powered system that translates complex Marketing Mix Model (MMM) data into actionable business insights. It allows users to ask natural language questions about channel performance and get data-grounded answers with recommendations.

## 🚀 Key Features

### Core Capabilities
- **Natural Language Q&A**: Ask questions like "Which channel has the best ROI?" or "Why is TikTok underperforming?"
- **Multi-Channel Analysis**: Compare performance across all marketing channels
- **Data-Grounded Insights**: All answers are validated against actual model data
- **Actionable Recommendations**: Get specific budget optimization advice
- **Response Validation**: Automated checks ensure answer accuracy

### Interface Options
- **REST API** (FastAPI) - for web applications
- **Command Line Interface** - for testing and scripting
- **Direct Python API** - for integration into other systems

## 📊 Data Structure

The system uses structured JSON data containing:
- Channel metrics (ROI, mROI, contribution, spend)
- Response curves and saturation points
- Adstock parameters and Hill coefficients
- Model diagnostics (R², MAPE)

Example channel data:
```json
{
  "id": "facebook_ads",
  "name": "Facebook Ads", 
  "spend": 110000.0,
  "contribution_pct": 0.33,
  "roi": 1.45,
  "mroi": 0.017,
  "response_curve_points": [...],
  "adstock": {"decay": 0.55, "max_lag_weeks": 7},
  "hill": {"half_sat": 75000, "alpha": 1.1}
}
```

## 🏗️ Architecture 
Core Components
📁 Project Structure:
1. AI.py              # Main AI analyst class & Gemini integration
2. Validation.py      # Response validation system 
3. workflow.py        # Basic channel data operations
4. app.py            # FastAPI REST server
5. runner.py         # Command-line interface
6. model_output.json # MMM data source


## Installation & Setup
1.  **Clone the repository**
2.  **Install dependencies:** `pip install -r requirements.txt`
3.  **Set your API key:** Create a `.env` file with `GEMINI_API_KEY=your_key_here`

## How to Run
**1. Command-Line Testing:**
```bash
# Test the AI
python runner.py --mode ai --name "Google Ads" --question "Add your question here " (eg . what is the highest channel ) 

# Find best performing channel 
python runner.py --mode best

# Get safe spend ranges
python runner.py --mode safe --name "Google Ads"

#Ask a natural-language AI question 
python runner.py --mode ai --question "Add your question here "

#if you want to restrict the question to a specific channel 
python runner.py --model ai --question "Add your question here" --name "Google Ads"

```

## Future Enhancements

**Planned Features**
Real-time data pipelines from Meridian model

Advanced visualization integration

Multi-period comparison capabilities

Scenario analysis tools

Export functionality for reports

**Current Limitations**
Uses static JSON data (awaiting live model integration)

Basic frontend interface

Limited to single-period analysis



