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
    emailverificationtoken: List["EmailVerificationTokens"] = Relationship(back_populates="webuser", sa_relationship_kwargs={"passive_deletes": True})
    updatepasswordtoken: List["UpdatePasswordTokens"] = Relationship(back_populates="webuser", sa_relationship_kwargs={"passive_deletes": True})
    account: List["Accounts"] = Relationship(back_populates="webuser", sa_relationship_kwargs={"passive_deletes": True})
    ragfiles: List["RagFiles"] = Relationship(back_populates="webuser", sa_relationship_kwargs={"passive_deletes": True})
    webchats: List["WebChats"] = Relationship(back_populates="webuser", sa_relationship_kwargs={"passive_deletes": True})


class EmailVerificationTokens(SQLModel, table=True):
    __tablename__="email_verification_tokens"
    email_verification_token_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="CASCADE")
    email_verification_token: Optional[str] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    webuser: Optional[WebUsers] = Relationship(back_populates="emailverificationtoken", sa_relationship_kwargs={"passive_deletes": True})


class UpdatePasswordTokens(SQLModel, table=True):
    __tablename__="update_password_tokens" 
    update_password_token_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="CASCADE")
    update_password_token: Optional[str] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    webuser: Optional[WebUsers] = Relationship(back_populates="updatepasswordtoken", sa_relationship_kwargs={"passive_deletes": True})


class Accounts(SQLModel, table = True):
    __tablename__ = "accounts"
    account_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="CASCADE")
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
    webuser: Optional[WebUsers] = Relationship(back_populates="account", sa_relationship_kwargs={"passive_deletes": True})


class RagFiles(SQLModel, table = True):
    __tablename__ = "rag_files"
    rag_file_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="CASCADE")
    name: Optional[str] = None
    detail: Optional[str] = None
    type: Optional[str] = None
    chunk: Optional[str] = None
    file_path: Optional[str] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    webuser: Optional[WebUsers] = Relationship(back_populates="ragfiles", sa_relationship_kwargs={"passive_deletes": True})
    ragchunks: List["RagChunks"] = Relationship(back_populates="ragfiles", sa_relationship_kwargs={"passive_deletes": True})


class RagChunks(SQLModel, table = True):
    __tablename__ = "rag_chunks"
    chunk_id: int | None = Field(default=None, primary_key=True)
    rag_file_id: Optional[int] = Field(default=None, foreign_key="rag_files.rag_file_id", ondelete="CASCADE")
    content: Optional[str] = None
    vector: Optional[List[float]] = Field(
        sa_column=Column(Vector(1024))
    )
    chunk_index: Optional[int] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    ragfiles: Optional[RagFiles] = Relationship(back_populates="ragchunks", sa_relationship_kwargs={"passive_deletes": True})


class WebChats(SQLModel, table = True):
    __tablename__ = "web_chats"
    web_chat_id: int | None = Field(default=None, primary_key=True)
    web_user_id: Optional[int] = Field(default=None, foreign_key="web_users.web_user_id", ondelete="CASCADE")
    chat_name: Optional[str] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    webmessage: List["WebMessages"] = Relationship(back_populates="webchat", sa_relationship_kwargs={"passive_deletes": True})
    webuser: Optional[WebUsers] = Relationship(back_populates="webchats", sa_relationship_kwargs={"passive_deletes": True})


class WebMessages(SQLModel, table = True):
    __tablename__ = "web_messages"
    web_message_id: int | None = Field(default=None, primary_key=True)
    web_chat_id: Optional[int] = Field(default=None, foreign_key="web_chats.web_chat_id", ondelete="CASCADE")
    query_message: Optional[str] = None
    response_message: Optional[str] = None
    rating: Optional[int] = None
    create_at: Optional[datetime] = Field(default_factory=datetime.now)
    update_at: Optional[datetime] = Field(default_factory=datetime.now)
    webchat: Optional[WebChats] = Relationship(back_populates="webmessage", sa_relationship_kwargs={"passive_deletes": True})
