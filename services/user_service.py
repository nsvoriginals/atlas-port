# THIS SERVICE HANDLES USER CREATION AND RETRIEVAL FROM THE DATABASE
from schemas.userschema import UserCreate
from sqlalchemy.orm import Session
from models.user_model import User

# FUNCTION TO CREATE A NEW USER

def create_user(db:Session,user:UserCreate):
    new_user=User(
        username=user.username,
        email=user.email,
        password=user.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# FUNCTION TO GET USER BY ID

def get_user(db:Session,user_id:int):
    user=db.query(User).filter(User.id==user_id).first()
    return user

# FUNCTION TO GET USER BY EMAIL

def get_user_by_email(db:Session,email:str):
    return db.query(User).filter(User.email==email).first()