import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"

APP_NAME = "Defenderse Solo en EE. UU."
APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_ok = INDEX_FILE.is_file()
    yield


app = FastAPI(
    title=APP_NAME,
    description=(
        "Aplicación educativa para comprender conceptos legales, "
        "organizar documentos y consultar recursos oficiales. "
        "No sustituye asesoramiento jurídico profesional."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    return response


@app.get("/", include_in_schema=False)
async def home():
    if not INDEX_FILE.is_file():
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": (
                    "No se encontró index.html. "
                    "Coloca index.html en la misma carpeta que main.py."
                ),
            },
        )

    return FileResponse(
        path=INDEX_FILE,
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/health", include_in_schema=False)
async def health():
    html_exists = INDEX_FILE.is_file()

    return JSONResponse(
        status_code=200 if html_exists else 503,
        content={
            "status": "ok" if html_exists else "error",
            "service": APP_NAME,
            "version": APP_VERSION,
            "online": html_exists,
            "html_found": html_exists,
        },
    )


@app.get("/api", include_in_schema=False)
async def api_info():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "purpose": "Legal education and official-resource navigation",
        "disclaimer": (
            "Educational information only; not legal advice "
            "and not a substitute for a qualified attorney."
        ),
        "available_endpoints": [
            "/",
            "/health",
            "/api",
            "/api/health",
            "/api/disclaimer",
            "/api/docs",
        ],
    }


@app.get("/api/health", include_in_schema=False)
async def api_health():
    return await health()


@app.get("/api/disclaimer", include_in_schema=False)
async def disclaimer():
    return {
        "title": "Aviso educativo",
        "message_es": (
            "Esta aplicación ofrece información educativa general "
            "y herramientas de organización. No es un bufete de abogados, "
            "no establece una relación abogado-cliente y no sustituye "
            "asesoramiento jurídico. Las leyes, los procedimientos y los "
            "plazos pueden variar según la jurisdicción y el caso. "
            "Verifica la información con fuentes oficiales y consulta "
            "a un abogado cuando sea necesario."
        ),
        "message_en": (
            "This application provides general educational information "
            "and organizational tools. It is not a law firm, does not "
            "create an attorney-client relationship, and does not replace "
            "legal advice. Laws, procedures, and deadlines may vary by "
            "jurisdiction and case. Verify information with official "
            "sources and consult an attorney when appropriate."
        ),
    }


@app.get("/robots.txt", include_in_schema=False)
async def robots():
    return PlainTextResponse(
        "User-agent: *\nAllow: /\n",
        media_type="text/plain",
    )


@app.get("/{path:path}", include_in_schema=False)
async def not_found(path: str):
    return JSONResponse(
        status_code=404,
        content={
            "status": "not_found",
            "message": "La página o el recurso solicitado no existe.",
        },
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
