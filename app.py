from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from routes.user_route import router as user_router
from routes.auth_route import auth_router
from config.db import Base, engine, recreate_tables
from routes.model_route import model_router
from routes.parser_route import parser_router
from routes.ats_route import ats_router
from routes.resume_route import resume_router

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Recreate all tables on startup
recreate_tables()

@app.get("/")
def index():
    return {"hello world"}

# Include routers with proper prefixes
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(model_router, prefix="/api", tags=["Model"])
app.include_router(ats_router, prefix="/ats", tags=["ATS"])
app.include_router(parser_router, prefix="/resume", tags=["Parser"])
app.include_router(resume_router, prefix="/api/resumes", tags=["Resumes"])