import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from routes import router

app = FastAPI(title="LinkSage Backend", version="0.1.0")


@app.middleware("http")
async def normalize_api_prefix(request: Request, call_next):
    if request.scope.get("path", "").startswith("/api/"):
        request.scope["path"] = request.scope["path"][4:] or "/"
    return await call_next(request)

app.include_router(router)

@app.get("/health", summary="Health check")
async def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse, summary="Landing page")
async def root():
    html = """
    <html>
    <head>
        <title>LinkSage API</title>
        <style>
            body { background-color: #111; color: #eee; font-family: Arial, Helvetica, sans-serif; padding: 2rem; }
            a { color: #4ea7ff; }
            table { border-collapse: collapse; margin-top: 1rem; }
            th, td { border: 1px solid #444; padding: 0.5rem 1rem; }
            th { background-color: #222; }
        </style>
    </head>
    <body>
        <h1>LinkSage API</h1>
        <p>Turn Links into Knowledge: Smart Organization, Instant Recall, and Connected Insights with AI.</p>
        <h2>Available Endpoints</h2>
        <table>
            <tr><th>Method</th><th>Path</th><th>Description</th></tr>
            <tr><td>GET</td><td>/health</td><td>Health check</td></tr>
            <tr><td>POST</td><td>/api/v1/bookmarks</td><td>Create a bookmark (AI summary & tags)</td></tr>
            <tr><td>GET</td><td>/api/v1/bookmarks/{id}</td><td>Retrieve bookmark details</td></tr>
            <tr><td>POST</td><td>/api/v1/summarize</td><td>Generate a summary for a URL</td></tr>
            <tr><td>POST</td><td>/api/v1/search</td><td>Smart search with AI query expansion</td></tr>
        </table>
        <p>Documentation: <a href="/docs">/docs</a> | <a href="/redoc">/redoc</a></p>
        <h2>Tech Stack</h2>
        <ul>
            <li>FastAPI 0.115.0</li>
            <li>PostgreSQL via SQLAlchemy 2.0.35</li>
            <li>DigitalOcean Serverless Inference (openai-gpt-oss-120b)</li>
            <li>Python 3.12+</li>
        </ul>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)
