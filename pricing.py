import pandas as pd
from difflib import get_close_matches

PRICING_FILE = "data/pricing.csv"

def load_pricing():
    df = pd.read_csv(PRICING_FILE)
    df["service_name"] = df["service_name"].astype(str).str.strip()
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    return df

def normalize(text):
    return str(text).lower().strip().replace("-", " ").replace("_", " ")

def find_price(service_name, pricing_df):
    normalized_service = normalize(service_name)

    for _, row in pricing_df.iterrows():
        if normalize(row["service_name"]) == normalized_service:
            return {
                "found": True,
                "service_name": row["service_name"],
                "unit_price": float(row["unit_price"]),
                "description": row["description"],
            }

    choices = pricing_df["service_name"].tolist()
    normalized_choices = [normalize(choice) for choice in choices]
    matches = get_close_matches(
        normalized_service, normalized_choices, n=1, cutoff=0.80
    )

    if matches:
        index = normalized_choices.index(matches[0])
        row = pricing_df.iloc[index]
        return {
            "found": True,
            "service_name": row["service_name"],
            "unit_price": float(row["unit_price"]),
            "description": row["description"],
        }

    return {
        "found": False,
        "service_name": service_name,
        "unit_price": None,
        "description": None,
    }

def lookup_services(extracted_data, pricing_df):
    results = []

    for service in extracted_data.get("services", []):
        service_name = service.get("service_name", "")
        quantity = service.get("quantity", 1)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        if quantity < 1:
            quantity = 1

        price_data = find_price(service_name, pricing_df)

        results.append({
            "requested_name": service_name,
            "matched_name": price_data["service_name"],
            "quantity": quantity,
            "unit_price": price_data["unit_price"],
            "description": price_data["description"],
            "found": price_data["found"],
        })

    return results
