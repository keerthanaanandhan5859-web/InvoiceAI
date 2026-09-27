# InvoicePilot AI

AI-powered invoice automation built for the KODNEXUS AI Build Battle.

## Workflow

Customer Requirement → Groq AI Extraction → Verified Price Lookup → Invoice Calculation → Human Approval → PDF Export

## Tech Stack

- Python
- Streamlit
- Groq API
- Llama 3.3 70B
- Pandas
- CSV pricing database
- ReportLab

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your Groq API key:

```env
GROQ_API_KEY=your_key_here
```

Run:

```bash
streamlit run app.py
```

## Important design decision

The AI extracts services and quantities but never determines prices. Prices are retrieved from the approved pricing CSV. If a requested service has no approved price, the invoice is blocked and the item is flagged for manual review.
