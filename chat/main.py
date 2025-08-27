from core.fastapi import *
from response.main import *
from core.vec_database import *



# ! สร้างห้องการสนทนาเพื่อตอบกลับไอดี

@app.post("/chat/new_chat", tags=["CHAT"])
def user_new_chat(session: SessionDep, user = Depends(get_user)):

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
                    "chat_id": new_chat.web_chat_id
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



# ! สร้างชื่อหัวข้อการสนทนาใหม่

@app.put("/chat/new_topic", tags=["CHAT"])
async def user_new_topic(data: ResponeChatSchema, session: SessionDep, user = Depends(get_user)):
    
    try :
        update_topic_chat = session.exec(
            select(WebChats)
            .where(WebChats.web_chat_id == data.chat_id)
        ).first()

        if not update_topic_chat or update_topic_chat.web_user_id != user["id"]:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบห้องแชท",
                    "data": {}
                }
            )
        
        response = await modelAi_topic_chat(data.query)
        if response == "":
            return JSONResponse(
                status_code=500,
                content={
                    "status": 0,
                    "message": "เกิดข้อผิดพลาดในการตอบคำถาม",
                    "data": {}
                }
            )

        update_topic_chat.chat_name = response
        update_topic_chat.update_at = datetime.now()

        session.add(update_topic_chat)
        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "id": data.chat_id,
                    "chat_history": response,
                    "date": update_topic_chat.update_at.replace(microsecond=0).isoformat()
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



# ! สร้างคำตอบจากโมเดล AI สำหรับผู้ใช้งาน

@app.post("/chat/respone", tags=["CHAT"])
async def respone_answer (data: ResponeChatSchema, session: SessionDep, user = Depends(get_user)):

    try :
        update_chat_at = session.exec(
            select(WebChats)
            .where(WebChats.web_chat_id == data.chat_id)
        ).first()

        if not update_chat_at or update_chat_at.web_user_id != user["id"]:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบห้องแชท",
                    "data": {}
                }
            )
            
        recent_messages=session.exec(
            select(WebMessages)
            .where(WebMessages.web_chat_id==update_chat_at.web_chat_id)
            .order_by(desc(WebMessages.create_at))
            .limit(5)
        ).all()
        
        recent_message_text = ""
        if recent_messages:
            for index, msg in enumerate(recent_messages[::-1], 1):
                recent_message_text += f"Q{index}: {msg.query_message}\n"
                recent_message_text += f"A{index}: {msg.response_message}\n\n"
        response = await modelAi_response_user_llamaindex(data.query, recent_message_text) 
        if response == "":
            return JSONResponse(
                status_code=500,
                content={
                    "status": 0,
                    "message": "เกิดข้อผิดพลาดในการตอบคำถาม",
                    "data": {}
                }
            )
        new_message = WebMessages(
            web_chat_id=data.chat_id,
            query_message=data.query,
            response_message=response,
            rating=0
        )

        session.add(new_message)
        session.commit()
        session.refresh(new_message)

        update_chat_at.update_at = datetime.now()
        session.add(update_chat_at)
        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "id": new_message.web_message_id,
                    "answer": new_message.response_message
                }
            }
        )
    except Exception as error :
        return JSONResponse(
            status_code=500,
            content=str(error)
        )



# ! สร้างคำตอบจากโมเดล AI สำหรับผู้ใช้งาน เมื่อแก้ไขคำถาม

@app.put("/chat/edit_respone", tags=["CHAT"])
async def edit_respone_answer (data: ResponeChatEditSchema, session: SessionDep, user = Depends(get_user)):

    try :
        update_message = session.exec(
            select(WebMessages)
            .where(WebMessages.web_message_id == data.msg_id)
        ).first()

        if not update_message:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบข้อความ",
                    "data": {}
                }
            )
        
        update_chat_at = session.exec(
            select(WebChats)
            .where(WebChats.web_chat_id == update_message.web_chat_id)
        ).first()

        if not update_chat_at or update_chat_at.web_user_id != user["id"]:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 0,
                    "message": "ไม่พบห้องแชท",
                    "data": {}
                }
            )

        recent_messages=session.exec(
            select(WebMessages.query_message, WebMessages.response_message)
            .where(WebMessages.web_chat_id==update_chat_at.web_chat_id)
            .order_by(desc(WebMessages.create_at))
            .limit(6)
        ).all()

        recent_message_text = ""
        if recent_messages:
            recent_messages.pop(0)
            if len(recent_messages) > 0:
                for index, msg in enumerate(recent_messages[::-1], 1):
                    recent_message_text += f"Q{index}: {msg.query_message}\n"
                    recent_message_text += f"A{index}: {msg.response_message}\n\n"
        response = await modelAi_response_user_llamaindex(data.query, recent_message_text) 
        
        if response == "":
            return JSONResponse(
                status_code=500,
                content={
                    "status": 0,
                    "message": "เกิดข้อผิดพลาดในการตอบคำถาม",
                    "data": {}
                }
            )
        
        update_message.query_message = data.query
        update_message.response_message = response
        update_message.rating = 0
        update_message.update_at = datetime.now()

        session.add(update_message)
        session.commit()
        print(f"Update Message: {update_message}")
        update_chat_at.update_at = datetime.now()

        session.add(update_chat_at)
        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "id": data.msg_id,
                    "answer": response
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



# ! สร้างคำตอบจากโมเดล AI สำหรับผู้มาเยือน

@app.post("/chat/guest_response", tags=["CHAT"])
async def guest_response_answer (data: GuestResponeChatSchema):
        
    try :
        response = await modelAi_response_guest_llamaindex(data.message)
        if response == "":
            return JSONResponse(
                status_code=500,
                content={
                    "status": 0,
                    "message": "เกิดข้อผิดพลาดในการตอบคำถาม",
                    "data": {}
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "answer": response
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