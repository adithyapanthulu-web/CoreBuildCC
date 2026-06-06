import json
from pathlib import Path

DEFECT_MAP_FILE = Path(__file__).resolve().parent / "context" / "defect_map.json"

with open(DEFECT_MAP_FILE, encoding="utf-8") as f:
    DEFECT_MAP = json.load(f)

def get_recommendation(diagnosis):
    text = json.dumps(
        diagnosis
    ).lower()
    for defect in DEFECT_MAP.values():
        aliases = defect["aliases"]
        if any(
            alias.lower() in text
            for alias in aliases
        ):
            products = defect["products"]
            output = "\n".join(
                [
                    f"• {p}"
                    for p in products
                ]
            )
            return f"Recommended Products:{output}"

    return "Recommended Products:• Technical product selection under review"
