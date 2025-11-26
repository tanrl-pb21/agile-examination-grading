import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import exams

app = FastAPI()
app.include_router(exams.router)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Serve static files (/static/style.css, /static/script.js)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

# HTML templates folder
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# Home page → return HTML instead of JSON
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


