import os

from fastapi import FastAPI 
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

from ollama import ChatResponse, chat

from sentence_transformers import SentenceTransformer

from core.database import *
from core.schemas import *
from core.models import *

from chatbot.services.llm import * 
from chatbot.services.rag import * 


app=FastAPI(
    title="ChatBot ECP Ai",
    description='',
    root_path="/ecp-ai",
    # docs_url=None, 
    # redoc_url=None
)

embedder=SentenceTransformer("all-mpnet-base-v2")


origins=[
    "http://localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/chatbot")
async def question(req: QuestionSchema, session: SessionDep):
    try:
        conversation_history=req.recent_conversation or ""
        print(conversation_history)

        context=get_relevant_context(req.query_message, 3, embedder, session)
        print(context)

        prompt=(
            "You are an AI assistant helping the user based on their past conversation and related documents.\n\n"
            "Conversation history:\n"
            f"{conversation_history}\n\n"
            "Relevant documents:\n"
            f"{context}\n\n"
            "Now, based on the conversation and the documents above, answer the following question:\n"
            f"{req.query_message}\n\n"
            "Answer:"
        )
        # print(prompt)
        
        response=large_language_model(prompt)
        # print(response)

        return JSONResponse(
            status_code=200,
            content={
                "status": 1,
                "message": "succeed",
                "data": {
                    "response": response
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


if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True) 