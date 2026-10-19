from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.psql_db import get_db
from app.services.user_service import (
    DuplicateEmailError,
    create_user_profile,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
email_validator = TypeAdapter(EmailStr)


@router.get("/", response_class=HTMLResponse)
def onboarding_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="onboarding.html",
        context={"error": None, "success": None},
    )


@router.post("/setup", response_class=HTMLResponse)
def create_profile(
    request: Request,
    email: str = Form(...),
    keywords: str = Form(""),
    description: str = Form(""),
    db: Annotated[Session, Depends(get_db)] = ...,
):
    try:
        # Normalize and validate the email before saving.
        validated_email = str(email_validator.validate_python(email)).lower()
    except ValidationError:
        return templates.TemplateResponse(
            request=request,
            name="onboarding.html",
            context={
                "error": "Please enter a valid email address.",
                "success": None,
                "email": email,
                "keywords": keywords,
                "description": description,
            },
            status_code=422,
        )

    try:
        user = create_user_profile(
            db=db,
            email=validated_email,
            raw_keywords=keywords,
            research_description=description,
        )
    except DuplicateEmailError as exc:
        return templates.TemplateResponse(
            request=request,
            name="onboarding.html",
            context={
                "error": str(exc),
                "success": None,
                "email": email,
                "keywords": keywords,
                "description": description,
            },
            status_code=409,
        )

    return templates.TemplateResponse(
        request=request,
        name="onboarding.html",
        context={
            "error": None,
            "success": f"Profile created for {user.email}.",
            "email": "",
            "keywords": "",
            "description": "",
        },
        status_code=201,
    )
