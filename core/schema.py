from sqlmodel import SQLModel

class SignUpSchema(SQLModel):
    username: str
    email: str
    password: str

class CheckEmail(SQLModel):
    email: str

class ResendEmailVerificationSchema(SQLModel):
    email: str

class VerifyEmailSchema(SQLModel):
    emailVerificationToken: str

class ForgotPasswordSchema(SQLModel):
    email: str

class checkUserByUpdatePasswordTokenSchema(SQLModel):
    updatePasswordToken: str

class UpdatePasswordSchema(SQLModel):
    updatePasswordToken: str
    password: str

class SignInSchema(SQLModel):
    email: str
    password: str

class ChangePasswordSchema(SQLModel):
    email: str
    password: str
    newpassword: str

class ResponeChatSchema(SQLModel):
    chat_id: int
    query: str

class ResponeChatEditSchema(SQLModel):
    msg_id: int
    query: str

class GuestResponeChatSchema(SQLModel):
    message: str

class NewRatingSchema(SQLModel):
    msg_id: int
    rating: int

class ChatNameSchema(SQLModel):
    chat_id: int
    chat_name: str

class ChatDeleteSchema(SQLModel):
    chat_id: int

class DashboardID(SQLModel):
    id: int

class DashboardEditUser(SQLModel):
    id: int
    name: str | None
    email: str | None
    provider: str | None
    role: int | None
    verified: bool | None

class DashboardEditChat(SQLModel):
    id: int
    name: str
    user: int

class DashboardEditFile(SQLModel):
    id: int
    name: str
    detail: str | None
    type: str