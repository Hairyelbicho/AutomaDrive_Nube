from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="AutomaDrive API")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def admin_root(request: Request):
 return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/index", response_class=HTMLResponse)
async def index(request: Request):
 return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/status")
async def status():
 return {"status": "ok"}
