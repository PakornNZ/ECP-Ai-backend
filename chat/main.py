from core.fastApi import *
from modelAi.model import *


@app.post("/chat/new_chat", tags=["CHAT"])
def user_new_chat(session: SessionDep, user = Depends(get_user)):

    try :
        new_chat = WebChats(
            web_user_id=user["id"],
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


@app.put("/chat/new_topic", tags=["CHAT"])
def user_new_topic(data: ResponeChatSchema, session: SessionDep, user = Depends(get_user)):
    
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
        
        response = ModelAi_Topic_Chat(data.query)

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


@app.post("/chat/respone", tags=["CHAT"])
def respone_answer (data: ResponeChatSchema, session: SessionDep, user = Depends(get_user)):

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

        respone = ModelAi_Response(data.query)
        newMessage = WebMessages(
            web_chat_id=data.chat_id,
            query_message=data.query,
            response_message=respone,
            rating=0
        )

        session.add(newMessage)
        session.commit()
        session.refresh(newMessage)

        update_chat_at.update_at = datetime.now()
        session.add(update_chat_at)
        session.commit()

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "id": newMessage.web_message_id,
                    "answer": newMessage.response_message
                }
            }
        )
    except Exception as error :
        return JSONResponse(
            status_code=500,
            content=str(error)
        )
    

@app.post("/chat/guest_response", tags=["CHAT"])
def guest_response_answer (data: GuestResponeChatSchema):
        
    try :
        respone = ModelAi_Response(data.message)

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "",
                "data": {
                    "answer": respone
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



@app.put("/chat/edit_respone", tags=["CHAT"])
def edit_respone_answer (data: ResponeChatEditSchema, session: SessionDep, user = Depends(get_user)):

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

        respone = ModelAi_Response(data.query)
        
        update_message.query_message = data.query
        update_message.response_message = respone
        update_message.rating = 0
        update_message.update_at = datetime.now()

        session.add(update_message)
        session.commit()

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
                    "answer": respone
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
    uvicorn.run(app, host="0.0.0.0", port=8020)