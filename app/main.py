from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine
from app.routers import auth as auth_router
from app.routers import polls as polls_router
from app.routers import votes as votes_router

# テーブル作成
Base.metadata.create_all(bind=engine)

app = FastAPI(title="投票アプリ", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth_router.router)
app.include_router(polls_router.router)
app.include_router(votes_router.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    from app.database import SessionLocal
    from app.routers.auth import get_current_user

    db = SessionLocal()
    try:
        user = get_current_user(request, db)
    finally:
        db.close()

    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(request: Request):
    return RedirectResponse(url="/polls/")
