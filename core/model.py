from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship, SQLModel, LargeBinary
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column


class Roles(SQLModel, table=True):
    __tablename__ = "roles"
    role_id: int | None = Field(default=None, primary_key=True)
    role: str = Field(default="user")
    webuser: List["WebUsers"] = Relationship(back_populates="role")


class WebUsers(SQLModel, table=True):
    __tablename__="web_users"
    web_user_id: int | None = Field(default=None, primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="roles.role_id")
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    image: Optional[str] = None
    email_verified: Optional[bool] = False
    create_at: datetime = Field(default_factory=datetime.now)
    update_at: datetime = Field(default_factory=datetime.now) 
    role: Optional[Roles] = Relationship(back_populates="webuser")
    emailverificationtoken: List["EmailVerificationTokens"] = Relationship(back_populates="webuser")
    updatepasswordtoken: List["UpdatePasswordTokens"] = Relationship(back_populates="webuser")
    account: List["Accounts"] = Relationship(back_populates="webuser")
    ragfiles: List["RagFiles"] = Relationship(back_populates="webuser")
    webchats: List["WebChats"] = Relationship(back_populates="webuser")


class EmailVerificationTokens(SQLModel, table=True):
    __tablename__="email_verification_tokens"
    email_verification_token_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="SET NULL")
    email_verification_token: Optional[str] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    webuser: Optional[WebUsers] = Relationship(back_populates="emailverificationtoken")


class UpdatePasswordTokens(SQLModel, table=True):
    __tablename__="update_password_tokens" 
    update_password_token_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="SET NULL")
    update_password_token: Optional[str] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    webuser: Optional[WebUsers] = Relationship(back_populates="updatepasswordtoken")


class Accounts(SQLModel, table = True):
    __tablename__ = "accounts"
    account_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="SET NULL")
    account_type: Optional[str] = None
    provider: Optional[str] = None
    provider_account_id: Optional[str] = None
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    session_state: Optional[str] = None
    webuser: Optional[WebUsers] = Relationship(back_populates="account")


class RagFiles(SQLModel, table = True):
    __tablename__ = "rag_files"
    rag_file_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="SET NULL")
    name: Optional[str] = None
    detail: Optional[str] = None
    type: Optional[str] = None
    file_path: Optional[str] = None
    vector_data: Optional[List[float]] = Field(
        sa_column=Column(Vector(768))
    )
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    webuser: Optional[WebUsers] = Relationship(back_populates="ragfiles")


class WebChats(SQLModel, table = True):
    __tablename__ = "web_chats"
    web_chat_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="SET NULL")
    chat_name: Optional[str] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    webmessage: List["WebMessages"] = Relationship(back_populates="webchat")
    webuser: Optional[WebUsers] = Relationship(back_populates="webchats")


class WebMessages(SQLModel, table = True):
    __tablename__ = "web_messages"
    web_message_id: int | None = Field(default=None, primary_key=True)
    web_chat_id: Optional[int] = Field(default=None, foreign_key="web_chats.web_chat_id", ondelete="SET NULL")
    query_message: Optional[str] = None
    response_message: Optional[str] = None
    rating: Optional[int] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    webchat: Optional[WebChats] = Relationship(back_populates="webmessage")
