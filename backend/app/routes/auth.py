from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.utils.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account"
)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new student with name, unique email, and hashed password.
    """
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_in.password)
    user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip(),
        password_hash=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login", 
    response_model=TokenResponse,
    summary="Login and obtain a JWT access token"
)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a user via email and password and returns a bearer JWT access token.
    """
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.get(
    "/me", 
    response_model=UserResponse,
    summary="Get details of currently authenticated user"
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of the logged-in student.
    """
    return current_user
