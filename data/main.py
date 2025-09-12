from core.fastapi import *

@app.get("/user/verification_chat", tags=["USER"])
def verification_chat(chat_id: int, session: SessionDep, user = Depends(get_user)):

    try :
        find_chat = session.exec(
            select(WebChats).where(WebChats.web_chat_id == chat_id)
        ).first()
    
        if not find_chat or find_chat.web_user_id != user["id"]:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบห้องแชท",
                    "data": {}
                }
            )
        
        find_chat_data = session.exec(
            select(WebMessages)
            .where(WebMessages.web_chat_id == find_chat.web_chat_id)
            .order_by(asc(WebMessages.create_at))
        ).all()

        if not find_chat_data:
            return JSONResponse(
                status_code=200,
                content={
                    "status": 2, 
                    "message": "ห้องแชทว่าง", 
                    "data": {
                        "chat_id": find_chat.web_chat_id
                    }
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "chat_id": find_chat.web_chat_id,
                    "chat": [
                        {
                            "id": msg.web_message_id,
                            "query": msg.query_message,
                            "answer": msg.response_message,
                            "rating": int(msg.rating)
                        } for msg in find_chat_data
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


@app.get("/user/history", tags=["USER"])
def history_chat(session: SessionDep, user = Depends(get_user)):

    try :
        find_history_chat = session.exec(
            select(WebChats)
            .where(WebChats.web_user_id == user["id"])
            .order_by(desc(WebChats.update_at))
        ).all()

        if not find_history_chat:
            return JSONResponse(
                status_code=200,
                content={
                    "status": 1,
                    "message": "",
                    "data": {}
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": [{
                    "id": chat.web_chat_id,
                    "chat_history": chat.chat_name,
                    "date": chat.update_at.replace(microsecond=0).isoformat()
                    } for chat in find_history_chat
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


@app.put("/data/rating", tags=["DATA"])
def respone_rating(data: NewRatingSchema, session: SessionDep, user = Depends(get_user)):

    try:
        find_message = session.exec(
            select(WebMessages)
            .where(WebMessages.web_message_id == data.msg_id)
        ).first()

        if not find_message:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบข้อมูล",
                    "data": {}
                }
            )
        
        find_message.rating = data.rating
        find_message.update_at = datetime.now()

        session.add(find_message)
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


@app.put("/data/chat_name", tags=["DATA"])
def chat_name(data: ChatNameSchema, session: SessionDep, user = Depends(get_user)):

    try :
        find_chat_topic = session.exec(
            select(WebChats)
            .where(WebChats.web_chat_id == data.chat_id)
        ).first()

        if not find_chat_topic or find_chat_topic.web_user_id != user["id"]:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0, 
                    "message": "ไม่พบห้องแชท", 
                    "data": {}
                }
            )
        
        find_chat_topic.chat_name = data.chat_name
        find_chat_topic.update_at = datetime.now()

        session.add(find_chat_topic)
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


@app.put("/data/chat_delete", tags=["DATA"])
def chat_delete(data: ChatDeleteSchema, session: SessionDep, user = Depends(get_user)):

    try :
        find_chat_topic = session.exec(
            select(WebChats)
            .where(WebChats.web_chat_id == data.chat_id)
        ).first()

        if not find_chat_topic or find_chat_topic.web_user_id != user["id"]:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0, 
                    "message": "ไม่พบห้องแชท", 
                    "data": {}
                }
            )
        
        find_chat_topic.web_user_id = None

        session.add(find_chat_topic)
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



# ! สร้างห้องการสนทนาเพื่อตอบกลับไอดี

@app.post("/chat/new_chat", tags=["CHAT"])
async def user_new_chat(session: SessionDep, user = Depends(get_user)):

    try :
        new_chat = WebChats(
            web_user_id=user["id"],
            chat_name="[ห้องสนทนาใหม่]",
            create_at=datetime.now(),
            update_at=datetime.now()
        )

        session.add(new_chat)
        session.commit()
        session.refresh(new_chat)

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "id": new_chat.web_chat_id,
                    "chat_history": new_chat.chat_name,
                    "date": new_chat.create_at.replace(microsecond=0).isoformat()
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