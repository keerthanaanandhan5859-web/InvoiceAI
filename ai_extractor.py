import json
import os
from groq import Groq
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

SYSTEM_PROMPT = """
You are an AI assistant for an invoice automation system.

Extract from the customer's natural-language service request:
1. Customer name
2. Customer email
3. Requested services
4. Quantity for each service
5. Additional notes

STRICT RULES:
- Never invent customer information.
- Never invent services.
- Never invent prices.
- Never calculate prices or totals.
- If information is missing, return null.
- If a service is requested without a quantity, use quantity 1.
- Normalize obvious variations in service names.
- Return ONLY valid JSON.

JSON format:
{
  "customer_name": null,
  "email": null,
  "services": [{"service_name": "", "quantity": 1}],
  "notes": ""
}
"""


def extract_requirements(customer_text: str):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": customer_text},
        ],
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Groq returned invalid JSON.") from exc