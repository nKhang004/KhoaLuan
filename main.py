from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.core.database import Base, engine
from app.routers import auth, subjects, questions, exams, attempts, reports
from app.routers import export, import_questions, admin_import

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Ngân Hàng Câu Hỏi", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(questions.router)
app.include_router(exams.router)
app.include_router(attempts.router)
app.include_router(reports.router)
app.include_router(export.router)
app.include_router(import_questions.router)
app.include_router(admin_import.router)

frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"CẢNH BÁO: Không tìm thấy thư mục frontend tại {frontend_path}")

@app.get("/api/health")
def health():
    return {"status": "ok"}