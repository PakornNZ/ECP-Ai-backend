from core.fastapi import *
from pathlib import Path
from embedding import *

SAVE_FILE = Path() / "files_storage"
@app.get("/dashboard/user", tags=["Dashboard"])
def dashboard_user(session: SessionDep, user = Depends(get_user)):

    try :
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        get_user_data = session.exec(
            select(WebUsers)
            .options(
                selectinload(WebUsers.role),
                selectinload(WebUsers.account)
            )
            .order_by(asc(WebUsers.web_user_id))
        ).all()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": [{
                    "id": data.web_user_id,
                    "name": data.username,
                    "email": data.email,
                    "image": data.image,
                    "role": data.role.role,
                    "verified": data.email_verified,
                    "provider": data.account[0].provider if data.account else None,
                    "createdAt": data.create_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z")
                    } for data in get_user_data
                ]
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


@app.get("/dashboard/file", tags=["Dashboard"])
def dashboard_file(session: SessionDep, user = Depends(get_user)):

    try :
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        get_file_data = session.exec(
            select(RagFiles)
            .order_by(asc(RagFiles.rag_file_id))
        ).all()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": [{
                    "id": data.rag_file_id,
                    "name": data.name,
                    "detail": data.detail,
                    "type": data.type,
                    "chunk": data.chunk,
                    "user": data.web_user_id,
                    "updatedAt": data.update_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z"),
                    "createdAt": data.create_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z")
                    } for data in get_file_data
                ]
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


@app.get("/dashboard/chat", tags=["Dashboard"])
def dashboard_chat(session: SessionDep, user = Depends(get_user)):
    try :
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        get_chat_data = session.exec(
            select(
                WebChats.web_chat_id,
                WebChats.chat_name,
                WebChats.web_user_id,
                WebChats.update_at,
                WebChats.create_at,
                func.count(WebMessages.web_message_id).label("count")
            )
            .join(WebMessages, WebMessages.web_chat_id == WebChats.web_chat_id, isouter=True)
            .group_by(WebChats)
            .order_by(asc(WebChats.web_chat_id))
        ).all()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": [{
                    "id": data.web_chat_id,
                    "name": data.chat_name,
                    "count": data.count,
                    "user": data.web_user_id,
                    "updatedAt": data.update_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z"),
                    "createdAt": data.create_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z")
                    } for data in get_chat_data
                ]
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
    

@app.get("/dashboard/message", tags=["Dashboard"])
def dashboard_message(session: SessionDep, user = Depends(get_user)):
    try :
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        get_message_data = session.exec(
            select(WebMessages)
            .options(selectinload(WebMessages.webchat))
            .order_by(asc(WebMessages.web_message_id))
        ).all()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": [{
                    "id": data.web_message_id,
                    "query": data.query_message,
                    "answer": data.response_message,
                    "rating": int(data.rating),
                    "chat": data.web_chat_id,
                    "user":  data.webchat.web_user_id if data.webchat else None,
                    "updatedAt": data.update_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z"),
                    "createdAt": data.create_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z")
                    } for data in get_message_data
                ]
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


@app.get("/dashboard/board", tags=["Dashboard"])
def dashboard_board(session: SessionDep, user = Depends(get_user)):
    try :
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        data_total_rating, data_avg_rating = session.exec(
            select(func.count(), func.avg(WebMessages.rating))
            .where(WebMessages.rating > 0)
        ).one()

        data_result_rating = session.exec(
            select(WebMessages.rating, func.count().label("count"))
            .where(WebMessages.rating > 0)
            .group_by(WebMessages.rating)
        ).all()

        rating_count_map = {int(rating): count for rating, count in data_result_rating}

        data_detail_rating = []
        for rating in range(5, 0, -1):
            count = rating_count_map.get(rating, 0) 
            percent = round((count / data_total_rating) * 100, 1) if data_total_rating else 0
            data_detail_rating.append({
                "rating": int(rating),
                "count": count,
                "percent": percent
            })

        data_rating = {
            "avg": float(round(data_avg_rating, 2) if data_avg_rating else 0),
            "total": data_total_rating,
            "detail": data_detail_rating
        }
        
        data_total_file = session.exec(
            select(RagFiles.type, func.count().label("count"))
            .group_by(RagFiles.type)
        ).all()

        file_types = ["pdf", "docx", "txt", "csv"]
        file_count_map = {type: count for type, count in data_total_file}

        data_detail_file = []
        for file_type in file_types:
            count = file_count_map.get(file_type, 0)
            data_detail_file.append({
                "type": file_type,
                "count": count
            })
        
        data_file = {
            "total": sum([count for _, count in data_total_file]),
            "detail": data_detail_file
        }

        data_total_user = session.exec(
            select(WebUsers.role_id, func.count().label("count"))
            .group_by(WebUsers.role_id)
        ).all()

        data_detail_user = []
        for role, count in sorted(data_total_user, reverse=False):
            data_detail_user.append({
                "role": role,
                "count": count
            })

        data_user = {
            "total":  sum([count for _, count in data_total_user]),
            "detail": data_detail_user
        }

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "rating": data_rating,
                    "file": data_file,
                    "user": data_user
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


@app.post("/dashboard/profile", tags=["Dashboard"])
def dashboard_profile(data: DashboardID, session: SessionDep, user = Depends(get_user)):
    try :
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        get_user = session.exec(
            select(WebUsers)
            .options(
                selectinload(WebUsers.role),
                selectinload(WebUsers.account)
            )
            .where(WebUsers.web_user_id == data.id)
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
        
        get_chat_data = session.exec(
            select(
                WebChats.web_chat_id,
                WebChats.chat_name,
                WebChats.web_user_id,
                WebChats.update_at,
                WebChats.create_at,
                func.count(WebMessages.web_message_id).label("count")
            )
            .where(WebChats.web_user_id == data.id)
            .join(WebMessages, WebMessages.web_chat_id == WebChats.web_chat_id, isouter=True)
            .group_by(WebChats)
            .order_by(desc(WebChats.update_at))
        ).all()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "id": get_user.web_user_id,
                    "name": get_user.username,
                    "email": get_user.email,
                    "image": get_user.image,
                    "role": get_user.role.role,
                    "provider": get_user.account[0].provider if get_user.account else None,
                    "verified": get_user.email_verified,
                    "createdAt": get_user.create_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z"),
                    "chatData": [{
                        "id": data.web_chat_id,
                        "name": data.chat_name,
                        "count": data.count,
                        "user": data.web_user_id,
                        "updatedAt": data.update_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z"),
                        "createdAt": data.create_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z")
                        } for data in get_chat_data
                    ]
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


@app.post("/dashboard/profile-chat", tags=["Dashboard"])
def dashboard_profile_chat(data: DashboardID, session: SessionDep, user = Depends(get_user)):
    try :
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        get_chat = session.exec(
            select(
                WebChats.web_chat_id,
                WebChats.chat_name,
                WebChats.web_user_id,
                WebChats.update_at,
                WebChats.create_at,
                func.count(WebMessages.web_message_id).label("count")
            )
            .where(WebChats.web_chat_id == data.id)
            .join(WebMessages, WebMessages.web_chat_id == WebChats.web_chat_id, isouter=True)
            .group_by(WebChats)
        ).first()

        if not get_chat:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0, 
                    "message": "ไม่พบห้องแชท", 
                    "data": {}
                }
            )

        get_message_data = session.exec(
            select(WebMessages)
            .options(selectinload(WebMessages.webchat))
            .where(WebMessages.web_chat_id == data.id)
            .order_by(asc(WebMessages.update_at))
        ).all()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "id": get_chat.web_chat_id,
                    "name": get_chat.chat_name,
                    "count": get_chat.count,
                    "user": get_chat.web_user_id,
                    "updatedAt": get_chat.update_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z"),
                    "createdAt": get_chat.create_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z"),
                    "messageData": [{
                        "id": data.web_message_id,
                        "query": data.query_message,
                        "answer": data.response_message,
                        "rating": int(data.rating),
                        "chat": data.web_chat_id,
                        "user": get_chat.web_user_id,
                        "updatedAt": data.update_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z"),
                        "createdAt": data.create_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z")
                        } for data in get_message_data
                    ]
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


@app.post("/dashboard/upload_file", tags=["Dashboard"])
async def dashboard_upload_file(
        files: Annotated[List[UploadFile], File()],
        session: SessionDep,
        user = Depends(get_user),
        name: Annotated[Optional[str], Form()] = None,
        detail: Annotated[Optional[str], Form()] = None,
        chunk: Annotated[Optional[str], Form()] = None,
        start: Annotated[Optional[str], Form()] = None,
        stop: Annotated[Optional[str], Form()] = None
    ):

    try:
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        return_upload_file = []
        allowed_type = ['csv', 'pdf', 'txt', 'docx']

        for file in files:
            data_file = await file.read()
            type_file = file.filename.split('.')
            name = type_file[0] if len(files) > 1 else name
            detail = None if len(files) > 1 else detail

            if type_file in allowed_type:
                return JSONResponse(
                    status_code=422,
                    content={
                        "status": 0,
                        "message": "ประเภทเอกสารไม่ถูกต้อง",
                        "data": {}
                    }
                )
            
            file_name_research = session.exec(
                select(RagFiles)
                .where(RagFiles.name == name, RagFiles.type == type_file[1])
            ).first()

            if file_name_research:
                return JSONResponse(
                    status_code=422,
                    content={
                        "status": 0,
                        "message": "มีเอกสารชื่อนี้แล้ว",
                        "data": {}
                    }
                )
            if type_file[1] != "csv":
                if type_file[1] == "pdf" and int(chunk) == 0:
                    data_chunk = await extract_data_from_pdf(data_file, start, stop)
                else:
                    data_text = await extract_data_from_file(data_file, type_file[1], start, stop)

                    if not data_text or data_text == "":
                        return JSONResponse(
                            status_code=422,
                            content={
                                "status": 0,
                                "message": "ไม่พบข้อมูลในเอกสาร",
                                "data": {}
                            }
                        )
                    data_chunk = get_data_chunk(data_text, int(chunk), type_file[1])
            else:
                data_dict = extract_data_from_csv(data_file)

                if not data_dict or len(data_dict) == 0:
                    return JSONResponse(
                        status_code=422,
                        content={
                            "status": 0,
                            "message": "ไม่พบข้อมูลในเอกสาร CSV",
                            "data": {}
                        }
                    )
                lists = convert_record_to_text(data_dict)
                data_chunk = []
                for list_data in lists:
                    chunk_text = get_data_chunk(list_data, int(chunk), type_file[1])
                    data_chunk.extend(chunk_text)

            data_vector = model_embed(data_chunk)

            if data_vector is None or len(data_vector) == 0:
                return JSONResponse(
                    status_code=422,
                    content={
                        "status": 0,
                        "message": "ไม่สามารถสร้างเวกเตอร์จากเอกสารได้",
                        "data": {}
                    }
                )
            
            save_file = SAVE_FILE / f"{name}.{type_file[1]}"
            with open(save_file, "wb") as f:
                f.write(data_file)

            upload_file = RagFiles(
                web_user_id=user["id"],
                name=name,
                detail=detail,
                type=type_file[1],
                chunk=chunk,
                file_path=str(save_file),
                update_at=datetime.now(),
                create_at=datetime.now()
            )

            session.add(upload_file)
            session.commit()
            session.refresh(upload_file)

            for idx, (chunk_text, vector) in enumerate(zip(data_chunk, data_vector)):
                upload_chunk = RagChunks(
                    rag_file_id=upload_file.rag_file_id,
                    content=chunk_text,
                    vector=vector.tolist(),
                    chunk_index=idx
                )
                session.add(upload_chunk)
            session.commit()

            return_file = {
                "id": upload_file.rag_file_id,
                "name": upload_file.name,
                "detail": upload_file.detail,
                "type": upload_file.type,
                "chunk": upload_file.chunk,
                "user": upload_file.web_user_id,
                "updatedAt": upload_file.update_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z"),
                "createdAt": upload_file.create_at.astimezone().isoformat(timespec="minutes").replace("+00:00", "Z")
            }

            return_upload_file.append(return_file)
        return JSONResponse(
            status_code=200,
            content={
                "status": 1, 
                "message": "", 
                "data": return_upload_file
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
    

@app.put("/dashboard/edit_user", tags=["Dashboard"])
def dashboard_edit_user(data: DashboardEditUser, session: SessionDep, user = Depends(get_user)):
    print(f"ID {user["id"]} Edit User ID {data.id}")

    try :
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        update_user = session.exec(
            select(WebUsers)
            .options(selectinload(WebUsers.account))
            .where(WebUsers.web_user_id == data.id)
        ).first()
        
        if not update_user:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบผู้ใช้งาน",
                    "data": {}
                }
            )
        
        update_user.role_id = data.role
        update_user.username = data.name
        update_user.email = data.email
        update_user.email_verified = data.verified
        update_user.update_at = datetime.now()

        if update_user.account and len(update_user.account) > 0:
            update_user.account[0].provider = data.provider
            if (data.provider == "credentials"):
                update_user.account[0].account_type = "credentials"
            else :
                update_user.account[0].account_type = "oauth"

        session.add(update_user)
        session.commit()

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


@app.put("/dashboard/edit_chat", tags=["Dashboard"])
def dashboard_edit_chat(data: DashboardEditChat, session: SessionDep, user = Depends(get_user)):
    print(f"ID {user["id"]} Edit Chat ID {data.id}")

    try :
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=401,
                content={
                    "status": 0, 
                    "message": "Unauthorized", 
                    "data": {}
                }
            )
        
        update_chat = session.exec(
            select(WebChats)
            .where(WebChats.web_chat_id == data.id)
        ).first()
        
        if not update_chat:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบห้องสนทนา",
                    "data": {}
                }
            )
        
        update_chat.chat_name = data.name
        update_chat.web_user_id = data.user
        update_chat.update_at = datetime.now()

        session.add(update_chat)
        session.commit()

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


@app.put("/dashboard/edit_file", tags=["Dashboard"])
def dashboard_edit_file(data: DashboardEditFile, session: SessionDep, user = Depends(get_user)):
    print(f"ID {user["id"]} Edit File ID {data.id}")

    verify_user = session.exec(
        select(WebUsers)
        .where(WebUsers.web_user_id == user["id"])
    ).first()

    if not verify_user or verify_user.role_id != 2:
        return JSONResponse(
            status_code=401,
            content={
                "status": 0, 
                "message": "Unauthorized", 
                "data": {}
            }
        )
    
    update_file = session.exec(
        select(RagFiles)
        .where(RagFiles.rag_file_id == data.id)
    ).first()
    
    if not update_file:
        return JSONResponse(
            status_code=404,
            content={
                "status": 0,
                "message": "ไม่พบเอกสาร",
                "data": {}
            }
        )
    
    file_name_research = session.exec(
        select(RagFiles)
        .where(RagFiles.name == data.name, RagFiles.type == data.type)
    ).first()

    if file_name_research:
        return JSONResponse(
            status_code=422,
            content={
                "status": 0,
                "message": "มีเอกสารชื่อนี้แล้ว",
                "data": {}
            }
        )
    
    old_path = update_file.file_path
    dir_path = Path(old_path)
    new_path = dir_path.parent / f"{data.name}.{data.type}"

    try :
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            update_file.name = data.name
            update_file.detail = data.detail
            update_file.type = data.type
            update_file.file_path = str(new_path)
            update_file.update_at = datetime.now()
            session.add(update_file)
            session.commit()
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบเอกสาร",
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


# ! delete user
@app.delete("/dashboard/delete_user", tags=["Dashboard"])
async def dashboard_delete_user(request: Request, session: SessionDep, user = Depends(get_user)):
    data = await request.json()
    id = data.get("id")

    print(f"ID {user["id"]} Delete User ID {id}")
    
    try:
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=403,
                content={
                    "status": 0,
                    "message": "Unauthorized",
                    "data": {}
                }
            )

        delete_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == id)
        ).first()

        if not delete_user:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบผู้ใช้งาน",
                    "data": {}
                }
            )

        session.delete(delete_user)
        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {}
            }
        )

    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )


# ! delete chat
@app.delete("/dashboard/delete_chat", tags=["Dashboard"])
async def dashboard_delete_chat(request: Request, session: SessionDep, user = Depends(get_user)):
    data = await request.json()
    id = data.get("id")

    print(f"ID {user["id"]} Delete Chat ID {id}")
    
    try:
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=403,
                content={
                    "status": 0,
                    "message": "Unauthorized",
                    "data": {}
                }
            )

        delete_chat = session.exec(
            select(WebChats)
            .where(WebChats.web_chat_id == id)
        ).first()

        if not delete_chat:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบห้องสนทนา",
                    "data": {}
                }
            )

        session.delete(delete_chat)
        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {}
            }
        )

    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )
    
# ! delete message
@app.delete("/dashboard/delete_message", tags=["Dashboard"])
async def dashboard_delete_message(request: Request, session: SessionDep, user = Depends(get_user)):
    data = await request.json()
    id = data.get("id")

    print(f"ID {user["id"]} Delete Message ID {id}")
    
    try:
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=403,
                content={
                    "status": 0,
                    "message": "Unauthorized",
                    "data": {}
                }
            )

        delete_message = session.exec(
            select(WebMessages)
            .where(WebMessages.web_message_id == id)
        ).first()

        if not delete_message:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบข้อความ",
                    "data": {}
                }
            )

        session.delete(delete_message)
        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {}
            }
        )

    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )


# ! delete file
@app.delete("/dashboard/delete_file", tags=["Dashboard"])
async def dashboard_delete_file(request: Request, session: SessionDep, user = Depends(get_user)):
    data = await request.json()
    id = data.get("id")

    print(f"ID {user["id"]} Delete File ID {id}")   
    
    verify_user = session.exec(
        select(WebUsers)
        .where(WebUsers.web_user_id == user["id"])
    ).first()

    if not verify_user or verify_user.role_id != 2:
        return JSONResponse(
            status_code=403,
            content={
                "status": 0,
                "message": "Unauthorized",
                "data": {}
            }
        )

    delete_file = session.exec(
        select(RagFiles)
        .where(RagFiles.rag_file_id == id)
    ).first()

    if not delete_file:
        return JSONResponse(
            status_code=404,
            content={
                "status": 0,
                "message": "ไม่พบเอกสาร",
                "data": {}
            }
        )

    try:
        file_path = delete_file.file_path
        if os.path.exists(file_path):
            os.remove(file_path)
            session.delete(delete_file)
            session.commit()
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบเอกสาร",
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

    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={
                "status": 0,
                "message": str(error),
                "data": {}
            }
        )


# * download file
@app.post("/dashboard/download_file", tags=["Dashboard"])
async def dashboard_download_file(data: DashboardID, session: SessionDep, user = Depends(get_user)):

    print(f"ID {user["id"]} Download File ID {data.id}")
    
    try:
        verify_user = session.exec(
            select(WebUsers)
            .where(WebUsers.web_user_id == user["id"])
        ).first()

        if not verify_user or verify_user.role_id != 2:
            return JSONResponse(
                status_code=403,
                content={
                    "status": 0,
                    "message": "Unauthorized",
                    "data": {}
                }
            )

        download_file = session.exec(
            select(RagFiles)
            .where(RagFiles.rag_file_id == data.id)
        ).first()

        if not download_file:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบเอกสาร",
                    "data": {}
                }
            )

        file_name = download_file.name + '.' + download_file.type
        encoded_filename = urllib.parse.quote(file_name.encode('utf-8'))
        file_path = download_file.file_path
        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบเอกสาร",
                    "data": {}
                }
            )

        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )

    except Exception as error:
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
    uvicorn.run(app, host="0.0.0.0", port=8030)