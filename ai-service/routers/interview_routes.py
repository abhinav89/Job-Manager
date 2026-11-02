from services.external_work import run_blocking
from limiter import limiter
from fastapi import APIRouter, HTTPException, Request
from dependencies import get_current_user_id
from models.schemas import InterviewAnalyzeRequest
from services.interview_service import get_questions, analyze_answer
from pydantic import BaseModel, Field

router = APIRouter(prefix="/interview", tags=["interview"])

class QuestionsRequest(BaseModel):
    job_title: str = Field(default="", max_length=150)
    jd: str = Field(default="", max_length=100_000)

@router.post("/questions")
@limiter.limit("10/minute")
async def contextual_questions(data: QuestionsRequest, request: Request):
    get_current_user_id(request)
    return {"questions": get_questions(job_title=data.job_title, jd=data.jd)}

@router.get("/questions")
@limiter.limit("10/minute")
async def questions(request: Request, job_title: str = "", jd: str = ""):
    get_current_user_id(request)
    return {"questions": get_questions(job_title=job_title, jd=jd)}

@router.post("/analyze")
@limiter.limit("10/minute")
async def analyze(data: InterviewAnalyzeRequest, request: Request):
    get_current_user_id(request)
    try:
        result = await run_blocking(analyze_answer,
            question=data.question,
            answer=data.answer,
            job_title=data.job_title,
            jd=data.jd or "",
            delivery=data.delivery,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"INTERVIEW ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
