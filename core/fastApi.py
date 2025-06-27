from fastapi import FastAPI, HTTPException, status, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse
from sqlmodel import select, asc, desc
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Annotated, List
from io import BytesIO
import urllib.parse
import jwt
from jwt import PyJWTError

# * dev
from core.database import *
from core.model import  *
from core.schema import *
# * prod
# from database import *
# from model import  *
# from schema import *

# ! API Setup
app = FastAPI(
                title="ChatBot ECP Ai",
                description='',
                root_path="/ecp-ai",
                # docs_url=None, 
                # redoc_url=None
            )
# * อนุญาติสิทธิ์ใช้งาน API
origins = [
    "http://localhost",
    # "http://172.25.11.63"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
security = HTTPBearer()
SECRET = os.getenv('NEXTAUTH_SECRET')
ALGORITHM = "HS256"

# * ตรวจสอบ token
def get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    error_raise = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        if not payload.get("email_verified") :
            raise error_raise
        return payload
    except PyJWTError:
        raise error_raise
    

# * สร้างตารางในฐานข้อมูล
# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()