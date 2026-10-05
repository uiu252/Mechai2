# MERCH.AI

**1st Place — The Home Depot Hometown AI Innovation Challenge**

MERCH.AI is a human-in-the-loop assortment planning prototype designed to help merchants evaluate product assortments using multiple AI-powered perspectives.

The system analyzes product data through specialized **Finance, Operations, and Merchandising agents**, combines their recommendations, and presents the results to the merchant for final review and approval.

## How It Works

**Product Data → AI Agents → Recommendation → Human Review**

Each agent evaluates the assortment from a different business perspective. Their outputs are combined into an interactive interface where the merchant can compare recommendations and make the final decision.

## Tech Stack

Python • Streamlit • OpenAI API • Pandas

## Running Locally

```bash
git clone https://github.com/uiu252/mechai.git
cd mechai
pip install -r requirements.txt
streamlit run app.py
```

Add your API credentials to the appropriate environment configuration before running AI-powered features.

## Note

This repository contains a demonstration version of the project using sample data. Competition-provided source data is not included.
