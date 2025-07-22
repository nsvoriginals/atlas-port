# THIS IS THE MAIN ENTRY POINT OF THE APPLICATION
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from routes.user_route import router as user_router
from routes.auth_route import auth_router
from config.db import Base, engine, recreate_tables
from routes.model_route import model_router
from routes.parser_route import parser_router
from routes.ats_route import ats_router
from routes.resume_route import resume_router

# CREATE FASTAPI APP INSTANCE
app = FastAPI()

# ADD CORS MIDDLEWARE TO ALLOW FRONTEND CONNECTIONS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# RECREATE ALL DATABASE TABLES ON STARTUP
recreate_tables()

# ROOT ENDPOINT
@app.get("/")
def index():
    return {"hello world"}

# INCLUDE ALL ROUTERS FOR DIFFERENT API ENDPOINTS
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(model_router, prefix="/api", tags=["Model"])
app.include_router(ats_router, prefix="/ats", tags=["ATS"])
app.include_router(parser_router, prefix="/resume", tags=["Parser"])
app.include_router(resume_router, prefix="/api/resumes", tags=["Resumes"])