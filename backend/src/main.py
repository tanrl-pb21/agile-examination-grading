import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import exams
from routers import course

app = FastAPI()
app.include_router(exams.router)
app.include_router(course.router)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Serve static files (/static/style.css, /static/script.js)
app.mount(
    "/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static"
)

# HTML templates folder
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# Home page → return HTML instead of JSON
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("examManagement.html", {"request": request})


@app.get("/studentExam")
async def student_exam(request: Request):
    return templates.TemplateResponse("studentExam.html", {"request": request})


@app.get("/examDetail")
async def student_exam(request: Request):
    return templates.TemplateResponse("examDetails.html", {"request": request})

@app.get("/examGrading")
async def student_exam(request: Request):
    return templates.TemplateResponse("examGrading.html", {"request": request})

@app.get("/examManagement")
async def student_exam(request: Request):
    return templates.TemplateResponse("examManagement.html", {"request": request})


@app.get("/studentSubmissionList")
async def student_exam(request: Request):
    return templates.TemplateResponse("studentSubmissionList.html", {"request": request})


@app.get("/studentSubmissionReview")
async def student_exam(request: Request):
    return templates.TemplateResponse("studentSubmissionReview.html", {"request": request})



@app.get("/studentTakingExam")
async def student_exam(request: Request):
    return templates.TemplateResponse("studentTakingExam.html", {"request": request})

