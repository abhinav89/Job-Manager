from services.external_work import run_blocking
from services.sandbox import SandboxUnavailable
from limiter import limiter
from fastapi import APIRouter, HTTPException, Request
from dependencies import get_current_user_id
from models.schemas import (
    CodeRunRequest, CodeHintRequest,
    CodeReviewRequest, CodeExplainErrorRequest, CodeGenerateRequest
)
from services.code_service import (
    run_python_code, get_hint, review_code,
    explain_error, generate_problems_from_jd
)
from services.problems.code_problems import get_all_problems, get_problem_by_id

router = APIRouter(prefix="/code", tags=["code"])

@router.post("/run")
@limiter.limit("10/minute")
async def run_code(data: CodeRunRequest, request: Request):
    get_current_user_id(request)
    try:
        result = await run_blocking(run_python_code, data.code, data.stdin or "")
    except SandboxUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return result

@router.get("/problems")
@limiter.limit("10/minute")
async def list_problems(request: Request):
    get_current_user_id(request)
    return {"problems": get_all_problems()}

@router.get("/problems/{problem_id}")
@limiter.limit("10/minute")
async def get_problem(problem_id: int, request: Request):
    get_current_user_id(request)
    problem = get_problem_by_id(problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

@router.post("/hint")
@limiter.limit("10/minute")
async def hint(data: CodeHintRequest, request: Request):
    get_current_user_id(request)
    try:
        result = await run_blocking(get_hint, data.problem_title, data.problem_description, data.current_code, data.hint_level)
        return {"hint": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review")
@limiter.limit("10/minute")
async def review(data: CodeReviewRequest, request: Request):
    get_current_user_id(request)
    try:
        result = await run_blocking(review_code, data.problem_title, data.problem_description, data.code, data.output or "")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/explain-error")
@limiter.limit("10/minute")
async def explain(data: CodeExplainErrorRequest, request: Request):
    get_current_user_id(request)
    try:
        result = await run_blocking(explain_error, data.code, data.error, data.problem_title or "")
        return {"explanation": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
@limiter.limit("10/minute")
async def generate(data: CodeGenerateRequest, request: Request):
    get_current_user_id(request)
    try:
        problems = await run_blocking(generate_problems_from_jd, data.job_title, data.jd, data.difficulty, data.count)
        return {"problems": problems}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
