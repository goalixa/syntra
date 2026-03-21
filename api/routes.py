from fastapi import APIRouter

from api.schemas import AIRequest, AIResponse
from orchestration.crew_runner import run_ai_task

router = APIRouter()

@router.post("/ask", response_model=AIResponse)
def ask_ai(request: AIRequest):

    result = run_ai_task(request.prompt)

    return AIResponse(
        result=result
    )
