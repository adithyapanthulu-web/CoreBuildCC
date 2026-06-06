from openai import OpenAI
from config import OPENAI_API_KEY
from recommendation_engine import get_recommendation
import base64
import json

client = OpenAI(
    api_key=OPENAI_API_KEY
)

SYSTEM_PROMPT = """
You are CoreBuild AI.

ONLY analyze:

- construction defects
- waterproofing failures
- leakage
- rehabilitation
- structural repair
- construction chemical related problems

If image is outside CoreBuild scope
(people, helmets, vehicles, logos,
pets, electronics, unrelated objects)

reject professionally.

Rules:

- professional
- concise
- readable
- consultation style
- no essays
- no emojis
- no confidence score
- no pricing
- no cost estimation
- no backend logic
- no internal recommendation logic
- preliminary inspection wording only

Use stable engineering wording.

Prefer terms such as:

- concrete spalling
- steel corrosion
- honeycombing
- dampness
- efflorescence
- interior wall cracks
- exterior wall cracks
- terrace leakage
- roof leakage
- water tank leakage
- bathroom leakage
- balcony leakage

Return JSON only:

{
"is_valid_scope": true,
"identified_issues":"",
"root_cause":"",
"severity":"",
"recommended_treatment":"",
"site_recommendation":""
}
"""


def analyze_image(image_path):

    with open(
        image_path,
        "rb"
    ) as img:

        encoded = base64.b64encode(
            img.read()
        ).decode(
            "utf-8"
        )

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[

            {
                "role":"system",
                "content":SYSTEM_PROMPT
            },

            {
                "role":"user",

                "content":[

                    {
                        "type":"text",

                        "text":"""
Analyze image.

If unrelated:

set is_valid_scope = false

Reject professionally.

Maximum 2 short sentences
per section.

Use stable construction terminology.
"""
                    },

                    {
                        "type":"image_url",

                        "image_url":{
                            "url":
                            f"data:image/jpeg;base64,{encoded}"
                        }
                    }

                ]
            }

        ],

        max_tokens=500
    )

    raw = (

        response
        .choices[0]
        .message
        .content

    )

    cleaned = (

        raw
        .replace(
            "```json",
            ""
        )
        .replace(
            "```",
            ""
        )

    )

    diagnosis = json.loads(
        cleaned
    )

    # HARD SCOPE FILTER

    text_blob = (

        str(
            diagnosis.get(
                "identified_issues",
                ""
            )
        )

        +

        str(
            diagnosis.get(
                "root_cause",
                ""
            )
        )

        +

        str(
            diagnosis.get(
                "recommended_treatment",
                ""
            )
        )

    ).lower()

    reject_terms = [

        "outside corebuild",
        "not related",
        "not relevant",
        "unrelated",
        "logo",
        "branding",
        "helmet",
        "vehicle",
        "electronics",
        "product image",
        "not construction",
        "not applicable",
        "please upload"

    ]

    rejected = any(

        term in text_blob

        for term in reject_terms

    )

    scope_flag = str(

        diagnosis.get(
            "is_valid_scope",
            False
        )

    ).lower()

    # PRODUCT ENGINE

    if scope_flag == "true" and not rejected:

        diagnosis[
            "catalog_recommendation"
        ] = get_recommendation(
            diagnosis
        )

    else:

        diagnosis[
            "catalog_recommendation"
        ] = ""

    return diagnosis
