from core.fastapi import *
from response.main import *
from core.vec_database import *



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
        response = modelAi_response_user_llamaindex(data.query, recent_message_text) 
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
        response = modelAi_response_user_llamaindex(data.query, recent_message_text) 
        
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
        response = modelAi_response_guest_llamaindex(data.message)
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
    

# ! สร้างคำตอบจากโมเดล AI จากระบบไลน์

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage, FlexMessage, FlexContainer
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent, VideoMessageContent, AudioMessageContent, LocationMessageContent

from chat.building import get_building_flex_message

configuration=Configuration(access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler=WebhookHandler(channel_secret = os.getenv("LINE_CHANNEL_SECRET"))


@app.post("/chat/webhook", tags=["CHAT"])
async def webhook_endpoint(request: Request, x_line_signature: str=Header(None)):
    body_str=(await request.body()).decode("utf-8")
    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError:
        print("InvalidSignatureError: Check your Channel Secret.")
        raise HTTPException(status_code=400, detail="Invalid signature.")
    except Exception as e:
        print(f"Unhandled error in webhook_endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred while processing webhook.")
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    user_id = event.source.user_id
    user_message = event.message.text
    flex_message_content = get_building_flex_message()

    if user_message == "แผนที่อาคาร":
        try:
            flex_container = FlexContainer.from_dict(flex_message_content)
            with ApiClient(configuration) as api_client:
                MessagingApi(api_client).reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[FlexMessage(alt_text="แผนที่อาคาร", contents=flex_container)]
                    )
                )
            print("Flex Message sent successfully.")
        except Exception as e:
            print(f"Error sending Flex Message: {e}")
            try:
                with ApiClient(configuration) as fallback_api_client:
                    MessagingApi(fallback_api_client).reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text="ไม่สามารถแสดงเมนูได้ในขณะนี้")]
                        )
                    )
            except Exception as fallback_e:
                print(f"Fallback message failed: {fallback_e}")
        return


    with Session(engine) as session:
        response = ""
        try:
            get_user_by_id = session.exec(
                select(LineUsers).where(LineUsers.user_id == user_id)
            ).first()

            if not get_user_by_id:
                new_user = LineUsers(user_id=user_id)
                session.add(new_user)
                session.commit()

            recent_messages = session.exec(
                select(LineMessages)
                .where(LineMessages.line_user_id == get_user_by_id.line_user_id)
                .order_by(desc(LineMessages.create_at))
                .limit(5)
            ).all()

            recent_message_text = ""
            if recent_messages:
                for index, msg in enumerate(recent_messages[::-1], 1):
                    recent_message_text += f"Q{index}: {msg.query_message}\n"
                    recent_message_text += f"A{index}: {msg.response_message}\n\n"

            response = modelAi_response_user_llamaindex(user_message, recent_message_text)
            
            if response == "":
                response = "ระบบตอบคำถามไม่พร้อมใช้งานในขณะนี้"
            else:
                response = re.sub(r'<.*?>', '', response)
                response = re.sub(r'\s+', '', response).strip()
                response = re.sub(r'[^\w\s\u0E00-\u0E7F:/?&=._,@!()\-+]', '', response)
                new_message = LineMessages(
                    line_user_id=get_user_by_id.line_user_id,
                    query_message=user_message,
                    response_message=response
                )
                session.add(new_message)
                session.commit()

        except Exception as e:
            print(f"Error processing message from user '{user_id}': {e}")
            response = "ระบบไม่พร้อมใช้งานในขณะนี้"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response)]
            )
        )

@handler.add(MessageEvent, message=ImageMessageContent)
async def handle_image(event: MessageEvent):
    response_message = "ระบบรองรับเฉพาะข้อความเท่านั้น"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response_message)]
            )
        )

@handler.add(MessageEvent, message=VideoMessageContent)
def handle_image(event: MessageEvent):
    response_message = "ระบบรองรับเฉพาะข้อความเท่านั้น"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response_message)]
            )
        )


@handler.add(MessageEvent, message=AudioMessageContent)
def handle_image(event: MessageEvent):
    response_message = "ระบบรองรับเฉพาะข้อความเท่านั้น"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response_message)]
            )
        )


@handler.add(MessageEvent, message=LocationMessageContent)
def handle_image(event: MessageEvent):
    response_message = "ระบบรองรับเฉพาะข้อความเท่านั้น"

    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response_message)]
            )
        )





# ! ใข้สำหรับทดสอบ

@app.post("/chat/testing", tags=["TEST"])
def testing (data: GuestResponeChatSchema):
    try :
        respone = modelAi_response_testing_llamaindex(data.message)
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