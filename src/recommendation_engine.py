import json

with open("./defect_map.json", encoding="utf-8") as f:
    DEFECT_MAP = json.load(f)


# DEFECT ALIAS + PRODUCT ENGINE

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
