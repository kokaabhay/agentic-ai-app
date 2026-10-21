from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from master_agent import handle_request
from approval import list_pending, approve_pending

router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)

class ApprovalRequest(BaseModel):
    kind: str
    name: str

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/chat")
def chat(request: ChatRequest):
    try:
        return handle_request(request.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Request failed. Check application logs.") from exc

@router.get("/approvals")
def approvals():
    return {"pending": list_pending()}

@router.post("/approvals/approve")
def approve(request: ApprovalRequest):
    try:
        return approve_pending(request.kind, request.name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
