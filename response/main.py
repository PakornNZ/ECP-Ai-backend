import numpy as np
from fastapi import Depends
from core.model import  *
from sqlmodel import select, text
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
import os
load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
RESPONSE_MODEL = os.getenv("RESPONSE_MODEL")
OLLAMA_URL = os.getenv("OLLAMA_URL")

def embedding_query(query: str) -> np.ndarray:
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": query
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    embedding = np.array(response.json()["embedding"], dtype=np.float32)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding

async def modelAi_response_guest(query: str, session) -> str:
    vector_data, verify_date = search_retrieval(query, session)

    message = [{"role": "system", "content": "คุณคือผู้ช่วยที่สามารถตอบคำถามตามข้อมูลที่ให้มา"}]
    if verify_date:
        message.append({"role": "user", "content": f"""{verify_date}"""})
    message.append({"role": "user", "content": f"""ประวัติการสนทนาก่อนหน้า: -\n\n"""})
    message.append({"role": "user", "content": f"""ข้อมูล:\n{vector_data}"""})
    message.append({"role": "user", "content": f"""คำถาม: {query}"""})

    return await model_generate_answer(message)


async def modelAi_response_user(query: str, recent_message_text: str, recent_message_embed: str, session) -> str:
    vector_data = ""
    verify_date = ""

    print(f"recent_message_embed: {recent_message_embed}")
    if recent_message_embed and len(recent_message_embed) > 0:
        vector_data, verify_date = search_retrieval(recent_message_embed, session)
    else:
        vector_data, verify_date = search_retrieval(query, session)

    print(f"recent_message_text: {recent_message_text}")
    print(f"vector_data: {vector_data}")

    message = [{"role": "system", "content": "คุณคือผู้ช่วยที่สามารถตอบคำถามตามเอกสารที่ให้มา"}]
    if verify_date:
        message.append({"role": "user", "content": f"""{verify_date}"""})
    message.append({"role": "user", "content": f"""ประวัติการสนทนาก่อนหน้า:\n{recent_message_text}\n\n"""})
    message.append({"role": "user", "content": f"""เอกสารข้อมูล:\n{vector_data}"""})
    message.append({"role": "user", "content": f"""คำถาม: {query}"""})

    return await model_generate_answer(message)


def search_retrieval(query: str, session) -> str:
    verify_query = query
    verify_date = query_search_day(query)
    if verify_date:
        verify_query += verify_date
        
    embed_query = embedding_query(verify_query)

    if embed_query is None or len(embed_query) == 0:
        return ""

    session.execute(text("SET hnsw.ef_search = 100;"))
    get_vector_data = session.exec(
        select(RagChunks)
        .options(selectinload(RagChunks.ragfiles))
        .order_by(RagChunks.vector.op('<=>')(embed_query))
        .limit(5)
    ).all()

    if not get_vector_data:
        return ""

    get_file_id = 0
    vector_data = ""
    for data in get_vector_data:
        # chunk_vector = np.array(data.vector)
        # cosine_score = float(np.dot(embed_query, chunk_vector))
        # score_info = f"\n\n[Cosine Similarity Score: {cosine_score:.4f}]"

        if get_file_id != data.rag_file_id:
            vector_data += f"\n\n\nข้อมูลจากเอกสาร : {data.ragfiles.name}"
            vector_data += f"\nรายละเอียดเอกสาร : {data.ragfiles.detail if data.ragfiles.detail else '-'}"
            vector_data += f"\n{data.content}"
            # vector_data += f"{score_info}\n{data.content}"
        else:
            vector_data += f"\n\n{data.content}"
            # vector_data += f"{score_info}\n\n{data.content}"
        get_file_id = data.rag_file_id
    return vector_data, verify_date


async def model_generate_answer(message: str) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": RESPONSE_MODEL,
                "messages": message,
                "stream": False,
                "options": {
                    "temperature": 0.4,
                    "top_p": 0.9,
                }
            }
        )
        result = response.json()["message"]["content"]
        return result
    except Exception as e:
        return ""


def query_search_day(query: str) -> str | None:
    now = datetime.now()

    thai_day = ["อาทิตย์", "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์"]
    thai_month = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    thai_year = now.year + 543
    today_keywords = ["วัน", "วันนี้", "ปัจจุบัน", "ตอนนี้", "เดี๋ยวนี้", "ขณะนี้", "เดือนนี้", "ปีนี้", "กี่โมง", "เวลา", "โมง", "นาที"]
    yesterday_keywords = ["เมื่อวาน", "วานนี้", "เมื่อวาน", "วันก่อน", "เมื่อวา"]
    tomorrow_keywords = ["พรุ่งนี้", "วันถัดไป", "วันต่อไป", "วันหน้า", "วันพรุ"]

    if any(keyword in query for keyword in yesterday_keywords):
        prev_day = now - timedelta(days=1)
        return f"\n\nเมื่อวาน วัน{thai_day[int(prev_day.strftime('%w'))]} ที่ {prev_day.day} {thai_month[prev_day.month - 1]} พ.ศ. {thai_year} เวลา {now.strftime('%H:%M')}"
    elif any(keyword in query for keyword in tomorrow_keywords):
        next_day = now + timedelta(days=1)
        return f"\n\nพรุ่งนี้ วัน{thai_day[int(next_day.strftime('%w'))]} ที่ {next_day.day} {thai_month[next_day.month - 1]} พ.ศ. {thai_year} เวลา {now.strftime('%H:%M')}"
    elif any(keyword in query for keyword in today_keywords):
        return f"\n\nวันนี้ วัน{thai_day[int(now.strftime('%w'))]} ที่ {now.day} {thai_month[now.month - 1]} พ.ศ. {thai_year} เวลา {now.strftime('%H:%M')}"
    
    return None


async def modelAi_topic_chat(query: str) -> str :
    message = [
        {"role": "system", "content": "คุณคือผู้ช่วยในการตั้งชื่อหัวข้อบทสนทนาจากคำถามที่ได้รับ คุณจะต้องตอบคำถามเป็นชื่อหัวข้อที่สั้นและกระชับ"},
        {"role": "user", "content": f"""คำถามเพื่อใช้ตั้งหัวข้อ: {query}"""}
    ]
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": RESPONSE_MODEL,
                "messages": message,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 1,
                    "max_tokens": 10,
                }
            }
        )
        result = response.json()["message"]["content"]
        return result
    except Exception as e:
        return ""