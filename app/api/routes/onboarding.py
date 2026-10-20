from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr, TypeAdapter
from sqlalchemy.orm import Session

from app.auth.google import oauth
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
        context={
            "error": None,
            "success": None,
            "email": request.session.get("google_email", ""),
        },
    )


@router.get("/login/google", name="login_google")
async def login_google(request: Request):
    callback_url = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(
        request,
        callback_url,
    )


@router.get("/auth/google/callback", name="google_callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    google_user = token.get("userinfo")

    if not google_user or not google_user.get("email_verified"):
        return templates.TemplateResponse(
            request=request,
            name="onboarding.html",
            context={
                "error": "Google could not verify your email. Please try another account.",
                "success": None,
                "email": "",
            },
            status_code=403,
        )

    # Clear temporary session data, then store the verified identity.
    request.session.clear()
    request.session["google_email"] = google_user["email"].strip().lower()
    request.session["google_sub"] = google_user["sub"]

    return RedirectResponse(url="/", status_code=303)


@router.post("/setup", response_class=HTMLResponse)
def create_profile(
    request: Request,
    keywords: str = Form(""),
    description: str = Form(""),
    db: Annotated[Session, Depends(get_db)] = ...,
):
    # Never trust an email submitted by the HTML form.
    verified_email = request.session.get("google_email")

    if not verified_email:
        return RedirectResponse(
            url="/login/google",
            status_code=303,
        )

    try:
        user = create_user_profile(
            db=db,
            email=verified_email,
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
                "email": verified_email,
            },
            status_code=409,
        )

    return templates.TemplateResponse(
        request=request,
        name="onboarding.html",
        context={
            "error": None,
            "success": f"Profile created for {user.email}.",
            "email": verified_email,
        },
        status_code=201,
    )
