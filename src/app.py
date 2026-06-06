from fastapi import (
    FastAPI,
    Request,
    UploadFile,
    File,
    Form,
    Cookie
)

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import (
    HTMLResponse,
    JSONResponse
)

from starlette.middleware.sessions import (
    SessionMiddleware
)

import shutil
import uuid
import os
import base64
from pathlib import Path

from datetime import datetime

from PIL import Image
from pillow_heif import register_heif_opener

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4

from openai import OpenAI
from config import OPENAI_API_KEY,CORE_BUILD_SECRET

from ai_engine import analyze_image

from database import (

    update_download,
    get_device_scans,
    log_ai_scan,
    get_dashboard_stats
)

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=CORE_BUILD_SECRET
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = WORKSPACE_ROOT / "data"
UPLOAD_FOLDER = DATA_FOLDER / "uploads"
REPORT_FOLDER = DATA_FOLDER / "reports"
CHAT_SYSTEM_PROMPT_FILE = WORKSPACE_ROOT/ "src" / "prompts" / "base_prompt.txt"

CHAT_SYSTEM_PROMPT = CHAT_SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()

register_heif_opener()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_FOLDER)),
    name="uploads"
)

app.mount(
    "/reports",
    StaticFiles(directory=str(REPORT_FOLDER)),
    name="reports"
)

templates = Jinja2Templates(directory="templates")
client = OpenAI(api_key=OPENAI_API_KEY)

result_cache = {}
image_cache = ""

# HOME

@app.get("/")
async def home(
    request: Request,
    device_id: str | None = Cookie(default=None)
):

    today = datetime.now().strftime("%d-%m-%Y")
    scans = 0

    if device_id:
        scans = get_device_scans(device_id, today)
    else:
        device_id = str(uuid.uuid4())

    remaining = max(0, 7 - scans)

    response = templates.TemplateResponse(
        request,"index.html",
        {"remaining": remaining}
    )

    if request.cookies.get("device_id") is None:
        response.set_cookie(
            key="device_id",
            value=device_id,
            max_age=31536000
        )

    return response


# PREMIUM ADMIN DASHBOARD

@app.get("/admin-leads")
async def admin_leads(request: Request):
    stats,leads = get_dashboard_stats()
    return templates.TemplateResponse(
        "admin_leads.html",
        {
            "request": request,
            "leads": leads,
            "stats": stats
        }
    )


# ANALYZE ROUTE

@app.post("/analyze")
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    device_id: str | None = Cookie(default=None)
):

    global result_cache
    global image_cache

    today = datetime.now().strftime("%d-%m-%Y")

    if not device_id:
        device_id = str(uuid.uuid4())

    scans_today = get_device_scans(device_id,today)

    if scans_today >= 7:

        log_ai_scan(
            device_id,
            "LIMIT_BLOCKED",
            blocked=True
        )

        response = templates.TemplateResponse(
            "limit.html",{"request": request}
        )

        response.set_cookie(
            key="device_id",
            value=device_id,
            max_age=31536000
        )

        return response

    filename = (
        str(uuid.uuid4())
        + "_"
        + file.filename
    )

    upload_path = UPLOAD_FOLDER / filename

    with open(
        upload_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    if upload_path.suffix.lower() in (
        ".heic",
        ".heif"
    ):

        jpg_path = upload_path.with_suffix(".jpg")

        image = Image.open(
            upload_path
        )

        image.save(
            jpg_path,
            "JPEG"
        )

        upload_path = jpg_path

    result = analyze_image(
        upload_path
    )

    issue = result.get(
        "identified_issues",
        "Unknown"
    )

    log_ai_scan(
        device_id,
        issue,
        blocked=False
    )

    combined_text = (

        str(result.get(
            "identified_issues",
            ""
        )) +

        str(result.get(
            "root_cause",
            ""
        )) +

        str(result.get(
            "site_recommendation",
            ""
        ))

    ).lower()

    out_of_scope = any(

        keyword in combined_text

        for keyword in [

            "helmet",
            "logo",
            "vehicle",
            "bike",
            "motorcycle",
            "outside scope",
            "unrelated",
            "not construction",
            "not related"

        ]
    )

    if out_of_scope:

        result[
            "catalog_recommendation"
        ] = ""

    result_cache = result
    image_cache = str(upload_path)
    image_url = "/uploads/" + upload_path.name

    # CHAT SESSION RESET

    request.session[
        "questions_left"
    ] = 3

    request.session[
        "lead_captured"
    ] = False

    request.session[
        "inspection_result"
    ] = result

    response = templates.TemplateResponse(
        request,
        "result.html",
        {
            "result": result,
            "image": image_url
        }
    )

    response.set_cookie(
        key="device_id",
        value=device_id,
        max_age=31536000
    )

    return response

# CHAT BACKEND
@app.post("/chat")
async def chat_ai(
    request: Request
):

    data = await request.json()

    question = data.get(
        "message",
        ""
    ).strip()

    if not question:

        return JSONResponse(
            {
                "reply":
                "Please enter a question."
            }
        )

    questions_left = request.session.get(
        "questions_left",
        3
    )

    if questions_left <= 0:

        return JSONResponse(
            {
                "reply":
                "You've used all AI clarifications for this inspection. Download your AI report or contact CoreBuild technical team for further assistance."
            }
        )

    inspection = request.session.get(
        "inspection_result",
        {}
    )

    context = f"""

Detected Issue:
{inspection.get('identified_issues','')}

Root Cause:
{inspection.get('root_cause','')}

Severity:
{inspection.get('severity','')}

Recommended Treatment:
{inspection.get('recommended_treatment','')}

Product Recommendation:
{inspection.get('catalog_recommendation','')}

"""

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[

            {
                "role":"system",
                "content":
                CHAT_SYSTEM_PROMPT
            },

            {
                "role":"system",
                "content":
                context
            },

            {
                "role":"user",
                "content":
                question
            }

        ],

        max_tokens=250
    )

    reply = (
        response
        .choices[0]
        .message
        .content
    )

    request.session[
        "questions_left"
    ] = questions_left - 1

    return JSONResponse(
        {
            "reply": reply,
            "remaining":
            questions_left - 1
        }
    )


# DOWNLOAD REPORT

@app.post("/download-report")
async def download_report(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...)
):

    global result_cache
    global image_cache

    if not result_cache:

        return {
            "error":
            "No report available"
        }

    request.session[
        "lead_captured"
    ] = True

    today = datetime.now().strftime(
        "%d-%m-%Y"
    )

    update_download(
        phone,
        name,
        today
    )

    report_id = str(
        uuid.uuid4()
    )[:8].upper()

    pdf_path = REPORT_FOLDER / f"{report_id}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=22,
        bottomMargin=22
    )

    styles = getSampleStyleSheet()

    title_style = styles[
        "Heading1"
    ]

    title_style.alignment = (
        TA_CENTER
    )

    section_style = styles[
        "Heading2"
    ]

    body_style = styles[
        "BodyText"
    ]

    small_style = styles[
        "Italic"
    ]

    elements = []

    try:

        header = RLImage(
            "static/logos/report_header.png",
            width=530,
            height=105
        )

        elements.append(
            header
        )

    except:
        pass

    elements.append(
        Spacer(1,10)
    )

    elements.append(
        Paragraph(
            "COREBUILD AI INSPECTION REPORT",
            title_style
        )
    )

    elements.append(
        Spacer(1,12)
    )

    meta = Table(
        [
            [
                "Inspection ID",
                report_id
            ],
            [
                "Date",
                today
            ],
            [
                "Client",
                name
            ]
        ],
        colWidths=[150,320]
    )

    meta.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0,0),
                (0,-1),
                colors.HexColor("#111315")
            ),
            (
                "TEXTCOLOR",
                (0,0),
                (0,-1),
                colors.white
            ),
            (
                "GRID",
                (0,0),
                (-1,-1),
                1,
                colors.HexColor("#CFAE70")
            )
        ])
    )

    elements.append(meta)
    elements.append(Spacer(1,15))

    try:

        img = RLImage(
            image_cache,
            width=430,
            height=280
        )

        elements.append(img)
        elements.append(Spacer(1,15))

    except:
        pass

    sections = [

        (
            "Detected Issue",
            result_cache.get(
                "identified_issues",
                "N/A"
            )
        ),

        (
            "Root Cause",
            result_cache.get(
                "root_cause",
                "N/A"
            )
        ),

        (
            "Severity Assessment",
            result_cache.get(
                "severity",
                "N/A"
            )
        ),

        (
            "Recommended Treatment",
            result_cache.get(
                "recommended_treatment",
                "N/A"
            )
        ),

        (
            "Site Recommendation",
            result_cache.get(
                "site_recommendation",
                "N/A"
            )
        )

    ]

    if result_cache.get(
        "catalog_recommendation"
    ):

        sections.append(
            (
                "Recommended Product System",
                result_cache.get(
                    "catalog_recommendation",
                    ""
                )
            )
        )

    for heading, content in sections:

        elements.append(
            Paragraph(
                heading,
                section_style
            )
        )

        elements.append(
            Paragraph(
                str(content),
                body_style
            )
        )

        elements.append(
            Spacer(1,6)
        )

    doc.build(
        elements
    )

    return HTMLResponse(
        f"""
        <script>

        alert(
        "Dear {name}, your CoreBuild AI report is ready and downloading now."
        );

        window.location.href =
        "/reports/{report_id}.pdf";

        </script>
        """
    )
