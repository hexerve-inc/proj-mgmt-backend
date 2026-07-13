from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from api.deps import get_db
from schemas.password_reset import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ValidateTokenRequest,
    PasswordResetResponse,
    TokenValidationResponse
)
from services.password_reset_service import PasswordResetService
from core.rate_limiter import forgot_password_email_limiter, forgot_password_ip_limiter

router = APIRouter()

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    
    # Check IP rate limit
    if not forgot_password_ip_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests from this IP. Please try again later.")
        
    # Check email rate limit
    if not forgot_password_email_limiter.is_allowed(request_data.email):
        raise HTTPException(status_code=429, detail="Too many reset requests for this email. Please try again later.")

    reset_service = PasswordResetService(db)
    
    # We use background tasks so the API responds immediately
    # Note: request_reset internally generates token and sends email
    background_tasks.add_task(reset_service.request_reset, request_data.email)
    
    return PasswordResetResponse(message="If an account exists with that email, a password reset link has been sent.")

@router.post("/validate-reset-token", response_model=TokenValidationResponse)
def validate_reset_token(
    request_data: ValidateTokenRequest,
    db: Session = Depends(get_db)
):
    reset_service = PasswordResetService(db)
    user = reset_service.validate_token(request_data.token)
    return TokenValidationResponse(valid=user is not None)

@router.post("/reset-password", response_model=PasswordResetResponse)
def reset_password(
    request_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    reset_service = PasswordResetService(db)
    success, message = reset_service.reset_password(request_data.token, request_data.new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return PasswordResetResponse(message="Password has been reset successfully.")
