import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.routers import exams
from src.routers import course
from src.routers import question
from src.routers import submission

app = FastAPI()
app.include_router(exams.router)
app.include_router(course.router)
app.include_router(question.router)
app.include_router(submission.router)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Serve static files (/static/style.css, /static/script.js)
app.mount(
    "/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static"
)

# HTML templates folder
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# Home page → return HTML instead of JSON
@app.get("/examManagement", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("examManagement.html", {"request": request})


@app.get("/examDetails", response_class=HTMLResponse)
def exam_details(request: Request, id: int):
    return templates.TemplateResponse(
        "examDetails.html", {"request": request, "exam_id": id}
    )


# http://127.0.0.1:8000/examDetails?id=1
@app.get("/examGrading", response_class=HTMLResponse)
def exam_grading(request: Request, submissionId: str, examId: int):
    return templates.TemplateResponse(
        "examGrading.html",
        {"request": request, "submissionId": submissionId, "examId": examId},
    )


# http://127.0.0.1:8000/examGrading?submissionId=sub1001&examId=1


# Student: exam list
@app.get("/studentExam", response_class=HTMLResponse)
def student_exam_list(request: Request):
    return templates.TemplateResponse("studentExam.html", {"request": request})


# Student: exam taking
@app.get("/studentTakingExam", response_class=HTMLResponse)
def student_taking_exam(request: Request):
    return templates.TemplateResponse("studentTakingExam.html", {"request": request})


# Student: submission list
@app.get("/studentSubmissionList", response_class=HTMLResponse)
def student_submission_list(request: Request):
    return templates.TemplateResponse(
        "studentSubmissionList.html", {"request": request}
    )


# Student: submission review
@app.get("/studentSubmissionReview", response_class=HTMLResponse)
def student_submission_review(request: Request, id: int, userId: int):
    return templates.TemplateResponse(
        "studentSubmissionReview.html",
        {"request": request, "submissionId": id, "userId": userId},
    )


# Teacher: exam management page (same as home but separate URL)
@app.get("/examManagement", response_class=HTMLResponse)
def exam_management(request: Request):
    return templates.TemplateResponse("examManagement.html", {"request": request})
