from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from sqlalchemy.orm import Session
from config.db import SessionLocal, get_db
from services.user_service import create_user,get_user
from schemas.userschema import UserCreate,UserResponse

router = APIRouter()

@router.post('/',response_model=UserResponse)
def register_user(user:UserCreate,db:Session=Depends(get_db)):
    return create_user(db,user)

@router.get("/{user_id}",response_model=UserResponse)
def get_userinfo(user_id:int,db:Session=Depends(get_db)):
    db_user=get_user(db,user_id)
    if not db_user:
        raise HTTPException(status_code=404,detail="User not found")
    
    return db_user
