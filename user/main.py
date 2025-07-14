from uuid import uuid4
from passlib.hash import bcrypt

from core.fastapi import *

@app.post("/sign_up", tags=["USER"])
def create_user(user: SignUpSchema, session: SessionDep):
    try :
        existing_user = session.exec(
            select(WebUsers).where(WebUsers.email == user.email)
        ).first()

        hashed_password = bcrypt.hash(user.password)
        email_verification_token = uuid4()
        email_verification_token_expires = datetime.now() + timedelta(minutes=5)

        if existing_user:
            if existing_user.email_verified:
                return JSONResponse(
                    status_code=409,
                    content={
                        "status": 0,
                        "message": "อีเมลนี้ได้ลงทะเบียนแล้ว",
                        "data": {}
                    }
                )
            else:
                existing_user.username = user.username
                existing_user.password = hashed_password
                existing_user.role_id = 1
                session.add(existing_user)
                session.commit()
                session.refresh(existing_user)

                new_token = EmailVerificationTokens(
                    email_verification_token=email_verification_token,
                    expires_at=email_verification_token_expires,
                    web_user_id=existing_user.web_user_id
                )
                session.add(new_token)
                session.commit()
                session.refresh(new_token)

                return JSONResponse(
                    status_code=200,
                    content={
                        "status": 1,
                        "message": "",
                        "data": {
                            "token": new_token.email_verification_token
                        }
                    }
                )

        new_user = WebUsers(
            username = user.username,
            email = user.email,
            password = hashed_password,
            role_id = 1
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        new_token = EmailVerificationTokens(
            email_verification_token = email_verification_token,
            expires_at = email_verification_token_expires,
            web_user_id = new_user.web_user_id
        )

        session.add(new_token)
        session.commit()
        session.refresh(new_token)

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "token": new_token.email_verification_token
                }
            }
        )
    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )


@app.put("/sign_up/resend_email", tags=["EMAIL"])
def resend_email_verification(user: ResendEmailVerificationSchema, session: SessionDep):
    try :
        existing_email = session.exec(
            select(WebUsers)
            .where(WebUsers.email == user.email)
        ).first()

        if not existing_email:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบผู้ใช้งาน",
                    "data": {}
                }
            )

        if existing_email.email_verified == True:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 2,
                    "message": "คุณได้ทำการยืนยันอีเมลแล้ว",
                    "data": {}
                }
            ) 

        existing_token = session.exec(
            select(EmailVerificationTokens)
            .where(EmailVerificationTokens.web_user_id == existing_email.web_user_id)
        ).first()

        email_verification_token = uuid4()
        
        email_verification_token_expires = datetime.now() + timedelta(minutes=5)

        if existing_token:
            existing_token.email_verification_token = email_verification_token
            existing_token.expires_at = email_verification_token_expires 
            existing_token.update_at = datetime.now()
        else:
            new_token = EmailVerificationTokens(
                email_verification_token = user.emailVerificationToken,
                expires_at = user.emailVerificationTokenExpires,
                web_user_id = existing_email.web_user_id
            )

        update_token = existing_token if existing_token else new_token

        session.add(update_token)
        session.commit()
        session.refresh(update_token)

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "ส่งอีเมลอีกครั้งแล้ว",
                "data": {
                    "token": update_token.email_verification_token
                }
            }
        )

    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )



@app.put("/email_verification", tags=["EMAIL"])
def verify_email(user: VerifyEmailSchema, session: SessionDep):
    try :
        existing_token = session.exec(
            select(EmailVerificationTokens)
            .where(EmailVerificationTokens.email_verification_token == user.emailVerificationToken)
        ).first()

        if not existing_token:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "รหัสยืนยันไม่ถูกต้อง",
                    "data": {}
                }
            ) 

        now = datetime.now(existing_token.expires_at.tzinfo)
        if existing_token.expires_at < now:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 0,
                    "message": "รหัสยืนยันหมดอายุแล้ว",
                    "data": {}
                }
            ) 

        get_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == existing_token.web_user_id)
        ).first()

        if not get_user:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบผู้ใช้งาน",
                    "data": {}
                }
            )

        get_user.email_verified = True

        session.add(get_user)
        existing_token.expires_at = datetime.now()
        session.add(existing_token)

        session.commit()
        session.refresh(get_user)

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "user": get_user.email_verified
                }
            }
        )
    
    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )



@app.post("/forgot_password", tags=["USER"])
def forgot_password(user: ForgotPasswordSchema, session: SessionDep):
    try :
        existing_email = session.exec(
            select(WebUsers)
            .where(WebUsers.email == user.email)
        ).first()

        if not existing_email:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบผู้ใช้งาน",
                    "data": {}
                }
            )
    

        update_password_token = str(uuid4())
        
        update_password_token_expires = datetime.now() + timedelta(minutes=5)
        
        existing_token = session.exec(
            select(UpdatePasswordTokens)
            .where(UpdatePasswordTokens.web_user_id == existing_email.web_user_id)
        ).first()

        if existing_token:
            now = datetime.now(existing_token.expires_at.tzinfo)
            if existing_token.expires_at > now:
                return JSONResponse(
                    status_code=409,
                    content={
                        "status": 0,
                        "message": "การยืนยันตัวตนถูกส่งแล้ว",
                        "data": {}
                    }
                )
            existing_token.update_password_token = update_password_token 
            existing_token.update_at = datetime.now()
            existing_token.expires_at = update_password_token_expires
        else:
            new_token = UpdatePasswordTokens(
                update_password_token = update_password_token,
                create_at = datetime.now(),
                update_at = datetime.now(),
                expires_at = update_password_token_expires,
                web_user_id = existing_email.web_user_id
            )

        update_token = existing_token if existing_token else new_token

        session.merge(update_token)
        session.commit()
        session.refresh(update_token)
        return JSONResponse(
                    status_code=200,
                    content={
                        "status": 1,
                        "message": f"ส่งจดหมายไปยัง {user.email}",
                        "data": {
                            "token": update_token.update_password_token
                        }
                    }
                )

    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )



@app.post("/check_user_by_update_password_token")
def check_user_by_update_token(user: checkUserByUpdatePasswordTokenSchema, session: SessionDep):
    try :
        existing_token = session.exec(
            select(UpdatePasswordTokens)
            .where(UpdatePasswordTokens.update_password_token == user.updatePasswordToken)
        ).first()

        if not existing_token:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "รหัสยืนยันไม่ถูกต้อง",
                    "data": {}
                }
            ) 
        
        now = datetime.now(existing_token.expires_at.tzinfo)
        if existing_token.expires_at < now:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 0,
                    "message": "รหัสยืนยันหมดอายุแล้ว",
                    "data": {}
                }
            ) 

        get_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == existing_token.web_user_id)
        ).first()

        if not get_user:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบผู้ใช้งาน",
                    "data": {}
                }
            )

        session.add(get_user)
        session.commit()
        session.refresh(get_user)

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {}
            }
        )

    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )


@app.put("/update_password", tags=["USER"])
def update_password(user: UpdatePasswordSchema, session: SessionDep):
    try :
        existing_token = session.exec(
            select(UpdatePasswordTokens)
            .where(UpdatePasswordTokens.update_password_token == user.updatePasswordToken)
        ).first()

        if not existing_token:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "รหัสยืนยันไม่ถูกต้อง",
                    "data": {}
                }
            ) 

        now = datetime.now(existing_token.expires_at.tzinfo)
        if existing_token.expires_at < now:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 0,
                    "message": "รหัสยืนยันหมดอายุแล้ว",
                    "data": {}
                }
            ) 

        get_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == existing_token.web_user_id)
        ).first()

        if not get_user:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบผู้ใช้งาน",
                    "data": {}
                }
            )

        hashed_password = bcrypt.hash(user.password)
        if get_user:
            get_user.password = hashed_password 
            get_user.update_at = datetime.now()
            existing_token.expires_at = datetime.now()

        session.add(get_user)
        session.commit()
        session.refresh(get_user)

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "บันทึกรหัสผ่านสำเร็จ",
                "data": {}
            }
        )
    
    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )


@app.put("/change_password", tags=["USER"])
def change_password(user: ChangePasswordSchema, session: SessionDep):
    try :
        find_user_by_email = session.exec(
            select(WebUsers).where(WebUsers.email == user.email)
        ).first()

        if not find_user_by_email:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0, 
                    "message": "ไม่พบผู้ใช้งาน", 
                    "data": {}
                }
            )

        if not bcrypt.verify(user.password, find_user_by_email.password):
            return JSONResponse(
                status_code=480,
                content={
                    "status": 0, 
                    "message": "รหัสผ่านไม่ถูกต้อง", 
                    "data": {}
                }
            )
    
        hashed_new_password = bcrypt.hash(user.newpassword)
        find_user_by_email.password = hashed_new_password

        session.add(find_user_by_email)
        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "บันทึกรหัสผ่านสำเร็จ",
                "data": {}
            }
        )
    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )


@app.post("/check_email", tags=["USER"])
def check_email(user: CheckEmail, session: SessionDep):
    try :
        find_user_by_email = session.exec(
            select(WebUsers).where(WebUsers.email == user.email)
        ).first()

        if not find_user_by_email:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0, 
                    "message": "ไม่พบผู้ใช้งาน", 
                    "data": {}
                }
            )

        google_account = session.exec(
            select(Accounts)
            .where(Accounts.web_user_id == find_user_by_email.web_user_id)
            .where(Accounts.provider == "google")
        ).first()

        if google_account:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 0, 
                    "message": "อีเมลนี้ลงทะเบียนด้วย Google Login แล้ว", 
                    "data": {}
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 1, 
                "message": "", 
                "data": {}
            }
        )
    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )

@app.post("/sign_in", tags=["USER"])
def sign_in(user: SignInSchema, session: SessionDep):
    try :
        find_user_by_email = session.exec(
            select(WebUsers).where(WebUsers.email == user.email)
        ).first()

        if not find_user_by_email:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0, 
                    "message": "ไม่พบผู้ใช้งาน", 
                    "data": {}
                }
            )

        if not bcrypt.verify(user.password, find_user_by_email.password):
            return JSONResponse(
                status_code=480,
                content={
                    "status": 0, 
                    "message": "รหัสผ่านไม่ถูกต้อง", 
                    "data": {}
                }
            )

        if not find_user_by_email.email_verified:
            find_token_by_id = session.exec(
                select(EmailVerificationTokens)
                .where(EmailVerificationTokens.web_user_id == find_user_by_email.web_user_id)
            ).first()

            now = datetime.now(find_token_by_id.expires_at.tzinfo)
            if not find_token_by_id or find_token_by_id.expires_at < now:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": 0, 
                        "message": "รหัสยืนยันหมดอายุ", 
                        "data": {}
                    }
                )

            return JSONResponse(
                status_code=400,
                content={
                    "status": 0, 
                    "message": "กรุณายืนยันอีเมลก่อนเข้าสู่ระบบ", 
                    "data": {}
                }
            )

        find_account = session.exec(
            select(Accounts)
            .where(Accounts.web_user_id == find_user_by_email.web_user_id)
        ).first()

        if not find_account:
            new_account = Accounts(
                provider="credentials",
                provider_account_id=find_user_by_email.web_user_id,
                web_user_id=find_user_by_email.web_user_id,
                account_type="credentials",
            )
            session.add(new_account)
            session.commit()

            return JSONResponse(
                status_code=200,
                content={
                    "status": 1, 
                    "message": "", 
                    "data": {
                        "user": {
                            "web_user_id": find_user_by_email.web_user_id,
                            "email": find_user_by_email.email,
                            "role_id": find_user_by_email.role_id,
                            "email_verified": find_user_by_email.email_verified,
                            "username": find_user_by_email.username,
                            "image": find_user_by_email.image,
                            "provider": new_account.provider,
                            "create_at": find_user_by_email.create_at.replace(microsecond=0).isoformat()
                        }
                    }
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": 1, 
                "message": "", 
                "data": {
                    "user": {
                        "web_user_id": find_user_by_email.web_user_id,
                        "email": find_user_by_email.email,
                        "role_id": find_user_by_email.role_id,
                        "email_verified": find_user_by_email.email_verified,
                        "username": find_user_by_email.username,
                        "image": find_user_by_email.image,
                        "provider": find_account.provider,
                        "create_at": find_user_by_email.create_at.replace(microsecond=0).isoformat()
                    }
                }
            }
        )
    
    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )

@app.post("/auth/oauth", tags=["USER"])
def oauth_login(data: dict, session: SessionDep):
    try:
        account = data.get("account", {})
        user = data.get("user", {})

        provider = account.get("provider", None)
        provider_account_id = str(account.get("providerAccountId", None))
        access_token = account.get("access_token", None)
        refresh_token = account.get("refresh_token", None)
        account_type = account.get("type", None)
        expires_at = account.get("expires_at", None)
        if expires_at:
            expires_at = datetime.fromtimestamp(expires_at)
        token_type = account.get("token_type", None)
        scope = account.get("scope", None)
        id_token = account.get("id_token", None)
        session_state = account.get("session_state", None)

        if not provider or not provider_account_id:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 0,
                    "message": "เกิดข้อผิดพลาดขณะเข้าสู่ระบบ", 
                    "data": {}
                }
            )
        
        existing_account = session.exec(
            select(Accounts).where(
                Accounts.provider == provider,
                Accounts.provider_account_id == provider_account_id
            )
        ).first()

        if existing_account:
            existing_account.access_token = access_token
            existing_account.refresh_token = refresh_token
            existing_account.expires_at = expires_at
            existing_account.session_state = session_state
            existing_account.id_token = id_token
            session.add(existing_account)
            session.commit()
            
            user_old = session.exec(select(WebUsers).where(WebUsers.web_user_id == existing_account.web_user_id)).first()
            if user_old:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": 1,
                        "message": "",
                        "data": {
                            "user": {
                                "web_user_id": user_old.web_user_id,
                                "email": user_old.email,
                                "role_id": user_old.role_id,
                                "email_verified": user_old.email_verified,
                                "username": user_old.username,
                                "image": user_old.image,
                                "provider": existing_account.provider,
                                "create_at": user_old.create_at.replace(microsecond=0).isoformat()
                            }
                        }
                    }
                )

        email = user.get("email")
        name = user.get("name")
        image = user.get("image")

        if email and provider in ["credentials", "google"]:
            conflict = session.exec(
                select(WebUsers, Accounts)
                .join(Accounts, Accounts.web_user_id == WebUsers.web_user_id)
                .where(
                    WebUsers.email == email,
                    Accounts.provider.in_(["credentials", "google"])
                )
            ).first()

            if conflict:
                conflict_provider = conflict[1].provider
                if (conflict_provider == "credentials"):
                    conflict_provider = "ระบบเว็บไซต์"
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": 0, 
                        "message": f"อีเมลนี้ลงทะเบียนด้วย {conflict_provider} แล้ว", 
                        "data": {}
                    }
                )
        
        user_obj = session.exec(select(WebUsers).where(WebUsers.email == email)).first()
        if not user_obj:
            user_obj = WebUsers(
                email=email,
                username=name,
                image=image,
                role_id=1,
                email_verified=True
            )
            session.add(user_obj)
            session.commit()
            session.refresh(user_obj)

        new_account = Accounts(
            provider=provider,
            provider_account_id=provider_account_id,
            web_user_id=user_obj.web_user_id,
            account_type=account_type,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            token_type=token_type,
            scope=scope,
            id_token=id_token,
            session_state=session_state
        )

        session.add(new_account)
        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1, 
                "message": "", 
                "data": {
                    "user": {
                        "web_user_id": user_obj.web_user_id,
                        "email": user_obj.email,
                        "role_id": user_obj.role_id,
                        "email_verified": user_obj.email_verified,
                        "username": user_obj.username,
                        "image": user_obj.image,
                        "provider": provider,
                        "create_at": user_obj.create_at.replace(microsecond=0).isoformat()
                    }
                }
            }
        )

    except Exception as error :
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )

# ! รัน FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)