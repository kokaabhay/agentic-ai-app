from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from master_agent import handle_request
from approval import list_pending, approve_pending
from typing import Optional,List,Annotated
from doc_extractors import extract_uploaded_file
router = APIRouter()


class ApprovalRequest(BaseModel):
    kind: str
    name: str

@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/chat")
async def chat(
    message: str = Form(..., min_length=1, max_length=12000),
    files: List[UploadFile | str] | None= File(default=None),
):
    try:
        combined_message = message
        extracted_files = []

        # Process files only if the user uploaded any
        files = [
                file
                for file in (files or [])
                if not isinstance(file, str) and getattr(file, "filename", None)
                ]
        for uploaded_file in files or []:
            filename = uploaded_file.filename or ""

            if not filename:
                raise HTTPException(
                    status_code=400,
                    detail="Filename is required.",
                )

            file_content = await uploaded_file.read()

            if not file_content:
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{filename}' is empty.",
                )

            extracted_text = extract_uploaded_file(
                filename=filename,
                file_content=file_content,
            )

            extracted_files.append(
                f"Filename: {filename}\n"
                f"File content:\n{extracted_text}"
            )

        # Add extracted file contents to the user's message
        if extracted_files:
            combined_message += (
                "\n\nUploaded documents:\n\n"
                + "\n\n---\n\n".join(extracted_files)
            )

        # Send the message and any extracted file contents
        # to the existing agent
        return handle_request(combined_message)

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Request failed. Check application logs.",
        ) from exc

    finally:
        for uploaded_file in files or []:
            await uploaded_file.close()


                
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
