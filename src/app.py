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
from config import OPENAI_API_KEY

from ai_engine import analyze_image

from database import (

    init_db,
    update_download,
    get_connection,

    get_device_scans,
    log_ai_scan,
    get_dashboard_stats

)

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="corebuild_ai_secret"
)

init_db()
register_heif_opener()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(
    directory="templates"
)

client = OpenAI(
    api_key=OPENAI_API_KEY
)

result_cache = {}
image_cache = ""

REPORT_FOLDER = (
    "static/reports"
)

os.makedirs(
    REPORT_FOLDER,
    exist_ok=True
)

CHAT_SYSTEM_PROMPT = """
You are CoreBuild AI.

You ONLY answer:

- construction defects
- waterproofing
- leakage
- repair systems
- rehabilitation
- inspection clarification

Rules:

- use inspection context
- professional
- concise
- no pricing
- no cost estimates
- no backend logic
- no internal recommendation logic
- no Fosroc priority disclosure
- no unrelated topics
- no certification
- preliminary guidance only

If unrelated:

Politely refuse.

Encourage:

- AI report download
- CoreBuild technical support
when appropriate.
"""

# HOME

@app.get("/")
async def home(
    request: Request,
    device_id: str | None = Cookie(default=None)
):

    today = datetime.now().strftime(
        "%d-%m-%Y"
    )

    scans = 0

    if device_id:

        scans = get_device_scans(
            device_id,
            today
        )

    remaining = max(
        0,
        7 - scans
    )

    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            "remaining": remaining
        }
    )

    if not device_id:

        device_id = str(
            uuid.uuid4()
        )

        response.set_cookie(
            key="device_id",
            value=device_id,
            max_age=31536000
        )

    return response


# PREMIUM ADMIN DASHBOARD

@app.get("/admin-leads")
async def admin_leads():

    conn = get_connection()
    cur = conn.cursor()

    stats = get_dashboard_stats()

    cur.execute(
        """
        SELECT
        name,
        phone,
        date,
        downloads
        FROM users
        ORDER BY id DESC
        """
    )

    leads = cur.fetchall()
    conn.close()

    html = f"""
    <html>
    <head>
    <title>CoreBuild Dashboard</title>

    <style>

    body{{
        font-family:Arial;
        background:#f5f0e8;
        padding:40px
    }}

    .card{{
        background:white;
        padding:22px;
        border-radius:18px;
        margin-bottom:18px;
        box-shadow:0 8px 25px rgba(0,0,0,.08)
    }}

    table{{
        width:100%;
        border-collapse:collapse;
        background:white;
        border-radius:16px;
        overflow:hidden
    }}

    th{{
        background:#111315;
        color:white;
        padding:14px
    }}

    td{{
        padding:12px;
        border:1px solid #ddd
    }}

    h1,h2{{
        color:#111315
    }}

    </style>
    </head>

    <body>

    <h1>
    CoreBuild AI Dashboard
    </h1>

    <div class='card'>

    <h3>Total AI Scans:
    {stats["total_scans"]}</h3>

    <h3>Today's Scans:
    {stats["today_scans"]}</h3>

    <h3>Unique Devices:
    {stats["unique_devices"]}</h3>

    <h3>Blocked Attempts:
    {stats["blocked_attempts"]}</h3>

    </div> <h2>
    Report Leads
    </h2>

    <table>

    <tr>
    <th>Name</th>
    <th>Phone</th>
    <th>Date</th>
    <th>Reports</th>
    </tr>
    """

    for row in leads:

        html += f"""
        <tr>
        <td>{row['name']}</td>
        <td>{row['phone']}</td>
        <td>{row['date']}</td>
        <td>{row['downloads']}</td>
        </tr>
        """

    html += """
    </table>
    </body>
    </html>
    """

    return HTMLResponse(html)


# ANALYZE ROUTE

@app.post("/analyze")
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    device_id: str | None = Cookie(default=None)
):

    global result_cache
    global image_cache

    today = datetime.now().strftime(
        "%d-%m-%Y"
    )

    if not device_id:

        device_id = str(
            uuid.uuid4()
        )

    scans_today = get_device_scans(
        device_id,
        today
    )

    if scans_today >= 7:

        log_ai_scan(
            device_id,
            "LIMIT_BLOCKED",
            blocked=True
        )

        response = HTMLResponse(
            """
            <h2 style='font-family:Arial;padding:40px'>
            Daily AI inspection limit reached.<br><br>
            Please contact CoreBuild technical support.
            </h2>
            """,
            status_code=403
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

    upload_path = (
        f"static/uploads/{filename}"
    )

    with open(
        upload_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    if upload_path.lower().endswith(
        (
            ".heic",
            ".heif"
        )
    ):

        jpg_path = (
            upload_path.rsplit(
                ".",
                1
            )[0]
            + ".jpg"
        )

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
    image_cache = upload_path

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
            "image": "/" + upload_path
        }
    )

    response.set_cookie(
        key="device_id",
        value=device_id,
        max_age=31536000
    )

    return response# CHAT BACKEND

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

    pdf_path = (
        f"{REPORT_FOLDER}/{report_id}.pdf"
    )

    doc = SimpleDocTemplate(
        pdf_path,
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
        "/static/reports/{report_id}.pdf";

        </script>
        """
    )
