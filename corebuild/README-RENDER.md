# CoreBuild Construction Chemicals — Render Production Package

This ZIP is intentionally minimal and prepared for Render.

## Included

- FastAPI backend
- CoreBuild V5 frontend
- CoreBuild AI analysis and recommendations
- PDF reports
- Admin/history functionality
- `render.yaml` for Render Blueprint deployment
- Persistent Render disk configuration for database, uploads and reports

## Render deployment

1. Push the contents of this `corebuild` folder to a GitHub repository.
2. In Render choose **New > Blueprint** and select the repository.
3. Render reads `render.yaml` automatically.
4. When Render asks for `OPENAI_API_KEY`, enter the production OpenAI key once.
5. Deploy.

`CORE_BUILD_SECRET` is generated automatically by Render.
Runtime data is stored on the persistent disk at `/var/data`.

## Local test

From this folder:

    cd src
    pip install -r requirements.txt
    export OPENAI_API_KEY="YOUR_KEY"
    python -m uvicorn app:app --reload

Then open http://127.0.0.1:8000

Never commit an OpenAI API key to GitHub or place it inside this ZIP.
