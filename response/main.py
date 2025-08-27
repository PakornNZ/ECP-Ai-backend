from core.model import  *
from core.vec_database import *
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
import os
import re
load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
RESPONSE_URL = os.getenv("OLLAMA_URL")
RESPONSE_MODEL = os.getenv("RESPONSE_MODEL")
TOPIC_MODEL = os.getenv("TOPIC_MODEL")



# ! LlamaIndex Config
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore

embedding_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)

vector_store = QdrantVectorStore(
    collection_name=COLLECTION_NAME,
    client=client,
    text_key="content"
)

storage_ctx = StorageContext.from_defaults(vector_store=vector_store)
vector_index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    storage_context=storage_ctx,
    embed_model=embedding_model,
)

retriever = vector_index.as_retriever(
    similarity_top_k=5,
)

# query_engine = RetrieverQueryEngine.from_args(retriever)


# ! สร้างเวกเตอร์จากคำถาม

# def embedding_query(query: str) -> list[float]:
#     embedding = []
    # embedding = embedding_model.encode(query, normalize_embeddings=True)
    # return embedding
    # payload = {
    #     "model": EMBEDDING_MODEL,
    #     "prompt": query
    # }
    # response = requests.post(EMBEDDING_URL, json=payload)
    # response.raise_for_status()
    # embedding = np.array(response.json()["embedding"], dtype=np.float32)
    # norm = np.linalg.norm(embedding)
    # if norm > 0:
    #     embedding = embedding / norm

def retriever_context_with_llamaindex(
        user_query: str,
        add_day_hint: bool = True
) -> tuple[str, str] :
    
    query = user_query
    verify_date = query_search_day(user_query) if add_day_hint else ""

    if verify_date:
        query = f"{query}\n{verify_date}"
    
    nodes = retriever.retrieve(query)
    parts = []
    for i, n in enumerate(nodes, start=1):
        meta = n.node.metadata or {}
        text = meta.get("content", "-")
        name = meta.get("name", "-")
        detail = meta.get("detail", "")
        chunk_idx = meta.get("chunk_index", "")

        header = (
            f"#Document [{name}]\n"
            f"#Description [{detail if detail else '-'}]\n"
            f"#Chunk index [{chunk_idx}]\n"
        )
        parts.append(f"{header}\n{text}\n\n")
        print(f"[SCORE]: {getattr(n, 'score', 0):.4f}")
    vector_data = "\n\n".join(parts) if parts else ""

    return  vector_data, (verify_date or "")



# ! สร้างคำตอบจากโมเดล AI สำหรับผู้มาเยือน

# async def modelAi_response_guest(query: str) -> str:
#     vector_data, verify_date = search_retrieval(query)

    # message = [{"role": "system", "content": "คุณคือผู้ช่วยอัจฉริยะที่สามารถตอบคำถามจากข้อมูลที่ให้ คุณจะต้องตอบคำถามอย่างชัดเจนและกระชับ โดยอิงจากข้อมูลที่มีอยู่ คุณจะต้องตอบคำถามตามข้อมูลที่ให้มาและไม่ควรสร้างข้อมูลใหม่ขึ้นมา"}]
#     if verify_date and len(verify_date) > 0:
#         message.append({"role": "user", "content": f"""{verify_date}"""})
#     message.append({"role": "user", "content": f"""เอกสารจากระบบ:\n{vector_data}"""})
#     message.append({"role": "user", "content": f"""คำถามจากผู้ใช้: {query}"""})

    # return await model_generate_answer(message)



# ! สร้างคำถามจากโมเดล AI สำหรับผู้ใช้งาน

async def modelAi_response_guest_llamaindex(query: str) -> str:

    vector_data, verify_date = retriever_context_with_llamaindex(
        user_query=query
    )

    prompt = f"""
[ROLE]: You are an intelligent assistant that answers questions **only in Thai**.  
You must use only the information from [REFERENCE DATA].  
If no relevant information is found, respond with: "ไม่มีข้อมูลเพียงพอสำหรับคำถาม".

{"[DATE HINT]: " + verify_date if verify_date else ""}

-----
[REFERENCE DATA]:
{vector_data if vector_data else "-"}
-----

[QUESTION]:
{query}
"""

    answer = await model_generate_answer(prompt)
    return answer



async def modelAi_response_user_llamaindex(
    query: str,
    recent_message_text: str | None = None
) -> str:
    
    vector_data, verify_date = retriever_context_with_llamaindex(
        user_query=query
    )

    prompt = f"""
[ROLE]: You are an intelligent assistant that answers questions **only in Thai**.  
You must use only the information from [REFERENCE DATA].  
If no relevant information is found, respond with: "ไม่มีข้อมูลเพียงพอสำหรับคำถาม".

{"[DATE HINT]: " + verify_date if verify_date else ""}
{f"""
-----
[HISTORY]:
{recent_message_text}
-----
""" if recent_message_text else "" }

-----
[REFERENCE DATA]:
{vector_data if vector_data else "-"}
-----

[QUESTION]:
{query}
"""

    answer = await model_generate_answer(prompt)
    return answer if answer else ""


# ! ค้นหาข้อมูลจากฐานข้อมูล Vector

# def search_retrieval(query: str) -> str:
#     verify_date = ""
#     verify_query = query
#     verify_date = query_search_day(query)
#     if verify_date and len(verify_date) > 0:
#         verify_query += verify_date

#     embed_query = embedding_query(verify_query)
#     if embed_query is None or len(embed_query) == 0:
#         return ""

    # session.execute(text("SET hnsw.ef_search = 100;"))
    # get_vector_data_pg = session.exec(
    #     select(RagChunks)
    #     .options(selectinload(RagChunks.ragfiles))
    #     .order_by(RagChunks.vector.op('<=>')(embed_query))
    #     .limit(5)
    # ).all()

    # * ค้นหาข้อมูลจากฐานข้อมูล Vector
    # get_vector_data = client.search(
    #     collection_name=COLLECTION_NAME,
    #     query_vector=embed_query.tolist(),
    #     limit=5,
    #     with_payload=True,
    # )
    # if not get_vector_data:
    #     return ""

    # vector_data_pg = ""
    # vector_data = ""
    # print(f"\n\nGet Vector Data <PG>\n\n")
    # for data in get_vector_data_pg:
    #     embed_query = np.array(embed_query, dtype=np.float32)
    #     score = np.dot(embed_query, data.vector)
    #     print(f"Score Id : {score:.4f}")
        # print(f"Score Id {data.id}: {data.score:.4f}")

        # if get_file_id != data.rag_file_id:
        #     vector_data += f"\nชื่อเอกสาร : {data.ragfiles.name}"
        #     vector_data += f"รายละเอียด : {data.ragfiles.detail if data.ragfiles.detail else '-'}"
        # vector_data_pg += f"{data.content}\n\n"
        # else:
        #     vector_data += f"\n{data.content}"
        # if data.payload:
        #     vector_data += f"{data.payload.get('content', '')}\n\n"

    # print(f"\n\nGet Vector Data <Qdrant>\n\n")
    # for data in get_vector_data:
    #     print(f"Score Id {data.id}: {data.score:.4f}")
    #     if data.payload:
    #         vector_data += f"{data.payload.get('content', '')}\n\n"

    # print(f"\n\nVector Data <PG>: \n{vector_data_pg}\n")
    # print(f"\n\nVector Data <Qdrant>: \n{vector_data}\n")
    # return vector_data, verify_date



# ! ค้นหาวันที่จากคำถาม

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



# ! สร้างคำตอบจากโมเดล AI

async def model_generate_answer(prompt: str) -> str:
    print("-------------------------------------------------------------------")
    print(f"Prompt: \n\n{prompt}")
    try:
        response = requests.post(
            RESPONSE_URL,
            json={
                "model": RESPONSE_MODEL,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "stream": False,
                "options": {
                    "temperature": 0.4,
                    "top_p": 1,
                }
            }
        )
        result = response.json()["message"]["content"]
        return result
    except Exception as e:
        print(f"Error in model_generate_answer: {e}")
        return ""



# ! สร้างหัวข้อบทสนทนา

async def modelAi_topic_chat(query: str) -> str :
    message = [
        {
            "role": "system",
            "content": (
                "You are an assistant that generates a short and concise conversation topic title "
                "based on the given question. "
                "You must always answer in **Thai language only**. "
                "Do not provide long sentences or unrelated content. "
                "The output must be short and meaningful.\n\n"
                "Examples:\n"
                "If the question is 'สวัสดี' respond 'การทักทาย'\n"
                "If the question is 'อธิบายการทำงานของ AI' respond 'AI ทำงานอย่างไร'\n"
            )
        },
        {
            "role": "user",
            "content": f"Question for topic title: {query}"
        }
    ]

    try:
        response = requests.post(
            RESPONSE_URL,
            json={
                "model": TOPIC_MODEL,
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
        result = re.sub(r'[^\w\s\u0E00-\u0E7F]', '', result)
        return result
    except Exception as e:
        return ""