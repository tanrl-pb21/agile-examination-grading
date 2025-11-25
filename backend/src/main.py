from fastapi import FastAPI
from routers import exams

app = FastAPI()

# Register routes
app.include_router(exams.router)

@app.get("/")
def root():
    return {"message": "Exam system backend is running"}