import os
from io import BytesIO
from pypdf import PdfReader
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
import pandas as pd
import json
import requests
import numpy as np
from collections import defaultdict
from typhoon_ocr import ocr_document
import tempfile
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import re
from dotenv import load_dotenv
load_dotenv()

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# OLLAMA_URL = os.getenv("OLLAMA_URL")
# EMBEDDING_URL = f"{OLLAMA_URL}/embeddings"



# ! แยกข้อความเป็นบล็อก

def split_blocks(text: str) -> list[str]:
    pattern = r'\*\*(.*?)\*\*'
    parts = re.split(pattern, text)
    blocks = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i+1].strip() if i + 1 < len(parts) else ""
        combined = f"**{title}**\n{content}".strip()
        blocks.append(combined)

    if not blocks:
        blocks = [text.strip()]
    blocks = [b for b in blocks if b.strip()]
    return blocks



#  ! แยกข้อความเป็นชิ้นส่วนย่อย Chunking

def get_data_chunk(data_text: str, max_tokens: int, file_type: str, overlap: int = 50) -> list[str]:
    cleaned_text = clean_text(data_text)
    blocks = split_blocks(cleaned_text) if file_type == 'txt' else [cleaned_text]
    blocks = [block for block in blocks if block.strip()]
    chunks = []
    for block in blocks:
        block = block.replace('\n', '[EOL]')
        tokens = tokenizer.encode(block, add_special_tokens=False)
        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk = tokenizer.decode(tokens[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start += max_tokens - overlap
    return chunks



# ! ทำความสะอาดข้อความ

def clean_text(text: str) -> str:
    text = re.sub(r'\n{4,}', '\n\n', text)
    text = re.sub(r'[ ]{2,}', ' ', text)
    text = re.sub(r'\.\.{2,}', '', text)
    text = re.sub(r'\t{2,}', '\t', text)
    text = re.sub(r'-{2,}', ' ', text)
    text = re.sub(r'(\|\s*)+', '', text)
    text = re.sub(r'<td>\s*</td>', '-', text)
    text = re.sub(r'[\u200b\u200c\u200d]', '', text)
    # text = re.sub(r'<td>\s*(.*?)\s*</td>', r'| \1 ', text)
    # text = re.sub(r'(?:\| [^\n]+)+', lambda m: m.group(0) + '', text)
    return text.strip()



#  ! ทำความสะอาดข้อความ Chunk

def clean_chunks(text: str) -> str:
    # text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text) 
    text = text.replace('"', '')
    return text



# ! สร้างเวกเตอร์จากข้อความ Chunk (Embedding)

def model_embed(chunks: list[str]) -> list[list[float]]:
    cleaned_chunks = [clean_chunks(chunk) for chunk in chunks]
    embeddings = embedding_model.encode(cleaned_chunks, normalize_embeddings=True)
    return embeddings.tolist()
        # payload = {
        #     "model": EMBEDDING_MODEL,
        #     "prompt": chunk
        # }
        # response = requests.post(EMBEDDING_URL, json=payload)
        # response.raise_for_status()
        # embedding = np.array(response.json()["embedding"], dtype=np.float32)
        # norm = np.linalg.norm(embedding)
        # if norm > 0:
        #     embedding = embedding / norm
        # embeddings.append(embedding.tolist())



# ! ดึงข้อมูลจากไฟลเป็นข้อความ

def extract_data_from_file(file_bytes: bytes, file_type: str, start: str, stop: str) -> str:
    data_text = []
    match file_type :
        case 'txt':
            try:
                data_text.append(file_bytes.decode('utf-8'))
            except UnicodeDecodeError:
                data_text.append(file_bytes.decode('latin1'))
        case 'pdf':
            with BytesIO(file_bytes) as pdf_stream:
                contents = PdfReader(pdf_stream)
                total_pages = len(contents.pages)

                stop_page = total_pages if not stop or stop == "" or stop == "0" or int(stop) >= total_pages else int(stop)
                start_page = 1 if not start or start == "" or start == "0" else int(start)

                if stop_page < start_page or start_page < 1 or stop_page > total_pages or start_page > total_pages:
                    return ""

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(file_bytes)
                    tmp_file_path = tmp_file.name

                for page_num in range(start_page, stop_page + 1):
                    page = contents.pages[page_num - 1]
                    text = page.extract_text()
                    if text and not is_bad_thai_text(text):
                        data_text.append(text.strip())
                    else:
                        ocr_text = ocr_document(
                            pdf_or_image_path=tmp_file_path,
                            task_type="default",
                            page_num=page_num
                        )
                        data_text.append(ocr_text)
                os.unlink(tmp_file_path)
        case 'docx':
            with BytesIO(file_bytes) as doc_stream:
                contents = Document(doc_stream)
                for element in contents.element.body:
                    if isinstance(element, CT_P):
                        paragraph = Paragraph(element, contents)
                        if paragraph.text.strip():
                            data_text.append(paragraph.text.strip())
                    elif isinstance(element, CT_Tbl):
                        table = Table(element, contents)
                        for row in table.rows:
                            row_data = []
                            for cell in row.cells:
                                cell_text = cell.text.strip()
                                if cell_text:
                                    row_data.append(cell_text)
                            if row_data:
                                data_text.append("\t".join(row_data))
    
    data_text = "\n".join(data_text)
    if not data_text.strip():
        return ""
    return data_text



# ! ดึงข้อมูลจากไฟล์ pdf แยกเป็นหน้า

def extract_data_from_pdf(file_bytes: bytes, start: str, stop: str) -> list[str]:
    chunks = []
    with BytesIO(file_bytes) as pdf_stream:
        contents = PdfReader(pdf_stream)
        total_pages = len(contents.pages)

        stop_page = total_pages if not stop or stop == "" or stop == "0" or int(stop) >= total_pages else int(stop)
        start_page = 1 if not start or start == "" or start == "0" else int(start)

        if stop_page < start_page or start_page < 1 or stop_page > total_pages or start_page > total_pages:
            return ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_file_path = tmp_file.name

        for page_num in range(start_page, stop_page + 1):
            page = contents.pages[page_num - 1]
            text = clean_text(page.extract_text())

            if text and not is_bad_thai_text(text):
                chunk_text = text.strip()
            else:
                ocr_text = ocr_document(
                    pdf_or_image_path=tmp_file_path,
                    task_type="default",
                    page_num=page_num
                )
                chunk_text = ocr_text
            if chunk_text:
                chunks.append(clean_text(chunk_text))
        os.unlink(tmp_file_path)
    return chunks



# ! ค้นหาข้อความที่ผิดพลาดจากการดึงข้อมูลจากไฟล์ pdf

def is_bad_thai_text(text: str) -> bool:
    if not text or len(text.strip()) < 30:
        return True

    suspicious_patterns = [
        r'[^\s]N',
        r'[^\s]J',
        r'[\u0E00-\u0E7F][`~^]', 
        r'[a-zA-Z]\u0E00',
    ]

    suspicious_chars = [
        '\ufffd', '\u200b', '\u200c', '\u200d', '\u202a', '\u202c', '\ufeff',
        '`', '^', 'N', 'J', '~'
    ]

    if any(char in text for char in suspicious_chars):
        return True

    if any(re.search(p, text) for p in suspicious_patterns):
        return True

    return False



# ! ดึงข้อมูลจากไฟล์ csv

def extract_data_from_csv(file_bytes: bytes) -> list[dict]:
    df = pd.read_csv(BytesIO(file_bytes), encoding='utf-8')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.ffill(inplace=True)
    records = df.to_dict(orient='records')

    list_field = ['สาขา' ,'ชั้นและห้อง']
    valid_list_fields = [f for f in list_field if f in df.columns]
    if valid_list_fields:
        return merge_records_by_shared_fields(records, valid_list_fields)
    elif 'ประเภทรายการ' in df.columns:
        return group_nested_records(records, 'ประเภทรายการ', ['รายการ', 'ค่าธรรมเนียมฉบับละ', 'เพิ่มเติม'])
    elif 'ตารางสอน' in df.columns:
        return group_nested_records(records, 'ตารางสอน', ['วันสอน', 'เวลาสอน', 'ชื่อวิชา', 'ห้องสอน', 'ชั้น'])
    else:
        return records



# ! ข้อมูลที่ได้จาก csv จัดกลุ่มตามฟิลด์

def group_nested_records(records: list[dict], group_field: str, detail_fields: list[str]) -> list[dict]:
    grouped = defaultdict(list)

    for record in records:
        group_key = record.get(group_field, "")
        detail = {k: record[k] for k in detail_fields if k in record}
        grouped[group_key].append(detail)

    result = []
    for group_value, details in grouped.items():
        result.append({
            group_field: group_value,
            "รายการทั้งหมด": details
        })
    return result



# ! ข้อมูลที่ได้จาก csv จัดกลุ่มตามฟิลด์

def merge_records_by_shared_fields(records, list_field) -> list[dict]:
    grouped = defaultdict(list)
    
    for record in records:
        key_fields = {k: v for k, v in record.items() if k not in list_field}
        key_tuple = tuple(key_fields.items())
        
        value_fields = {k: record[k] for k in list_field}
        grouped[key_tuple].append(value_fields)

    result = []
    for key_tuple, value_dicts in grouped.items():
        base = dict(key_tuple)
        for field in list_field:
            base[field] = list({v[field] for v in value_dicts if field in v})
        result.append(base)
    return result



# ! แปลงข้อมูลให้อยู่ในรุปแบบข้อความ

def convert_record_to_text(record: list[dict]) -> list[str]:
    first_key = list(record[0].keys())[0] if record else None
    texts = []
    text = ""
    match first_key:
        # case 'การศึกษา':
        #     first_group = ""
        #     for rec in record:
        #         if rec.get('การศึกษา', '-') == 'ปริญญาตรี':
        #             if first_group == rec.get('คณะ', '-'):
        #                 text += f"\n*คณะ: {rec.get('คณะ', '-')}*"
        #                 text += f"\nหลักสูตร: {rec.get('หลักสูตร', '-')}"
        #                 text += f"\nระยะเวลาหลักสูตร: {rec.get('ระยะเวลาหลักสูตร', '-')}"
        #                 text += f"\nสำเร็จการศึกษา: {rec.get('สำเร็จการศึกษา', '-')}"
        #                 text += f"\nสาขา: "
        #                 for field in rec.get('สาขา', []):
        #                     text += f"{field}, "
        #             else:
        #                 if first_group != "":
        #                     texts.append(text.strip())
        #                 text = f"การศึกษา: {rec.get('การศึกษา', '-')}"
        #                 text += f"\n*คณะ: {rec.get('คณะ', '-')}*"
        #                 text += f"\nหลักสูตร: {rec.get('หลักสูตร', '-')}"
        #                 text += f"\nระยะเวลาหลักสูตร: {rec.get('ระยะเวลาหลักสูตร', '-')}"
        #                 text += f"\nสำเร็จการศึกษา: {rec.get('สำเร็จการศึกษา', '-')}"
        #                 text += f"\nสาขา: "
        #                 for field in rec.get('สาขา', []):
        #                     text += f"{field}, "
                        
        #             first_group = rec.get('คณะ', '-')
        #         else:
        #             if first_group == "":
        #                 text += f"\n*คณะ: {rec.get('คณะ', '-')}*"
        #                 text += f"\nหลักสูตร: {rec.get('หลักสูตร', '-')}"
        #                 text += f"\nระยะเวลาหลักสูตร: {rec.get('ระยะเวลาหลักสูตร', '-')}"
        #                 text += f"\nสำเร็จการศึกษา: {rec.get('สำเร็จการศึกษา', '-')}"
        #                 text += f"\nสาขา: "
        #                 for field in rec.get('สาขา', []):
        #                     text += f"{field}, "
        #             else:
        #                 if first_group != "":
        #                     texts.append(text.strip())
        #                 text = f"การศึกษา: {rec.get('การศึกษา', '-')}"
        #                 text += f"\n*คณะ: {rec.get('คณะ', '-')}*"
        #                 text += f"\nหลักสูตร: {rec.get('หลักสูตร', '-')}"
        #                 text += f"\nระยะเวลาหลักสูตร: {rec.get('ระยะเวลาหลักสูตร', '-')}"
        #                 text += f"\nสำเร็จการศึกษา: {rec.get('สำเร็จการศึกษา', '-')}"
        #                 text += f"\nสาขา: "
        #                 for field in rec.get('สาขา', []):
        #                     text += f"{field}, "
        #                 first_group = ""
        case 'อาจารย์สาขา':
            text = f"**รายชื่ออาจารย์ประจำสาขาวิศวกรรมคอมพิวเตอร์**\n"
            for rec in record:
                text += f"ชื่อ {rec.get('ชื่อ', '-')}"
                text += f"\nตำแหน่ง: {rec.get('ตำแหน่ง', '-')}"
                if rec.get('ที่ปรึกษา', '-') != '-':
                    text += f"\nที่ปรึกษาชั้น: {rec.get('ที่ปรึกษา', '-')}"
                text += "\n\n"
            texts.append(text.strip())
        case 'วันหยุดราชการ':
            text = f"**วันหยุดราชการ/วันหยุดสำคัญ**\n"
            for rec in record:
                date = rec.get('วัน', '-')
                date = re.sub(r'-6\d', '', str(date))
                date = re.sub(r'-', ' ', str(date))
                text += f"(หยุด) {date} / "
                text += f"{rec.get('วันที่', '-')} {rec.get('เดือน', '-')} "
                text += f"{rec.get('วันหยุดราชการ', '-')}\n"
            texts.append(text.strip())
        case 'ประเภทรายการ':
            for rec in record:
                text = f"**รายการขอ {rec.get('ประเภทรายการ', '-')}**\n"
                for field in rec.get('รายการทั้งหมด', []):
                    text += f"รายการ: {field.get('รายการ', '-')}"
                    text += f"\nค่าธรรมเนียม/ฉบับ: {field.get('ค่าธรรมเนียมฉบับละ', '-')}"
                    text += f"\nเพิ่มเติม: {field.get('เพิ่มเติม', '-')}\n\n"
                texts.append(text.strip())
        case 'รหัสแบบฟอร์ม':
            for rec in record:
                text = f"**รหัสแบบฟอร์ม {rec.get('รหัสแบบฟอร์ม', '-')}**"
                text += f"\nแบบฟอร์ม {rec.get('ชื่อแบบฟอร์ม', '-')}"
                text += f"\nสิ่งที่ต้องกรอก: {rec.get('สิ่งที่ต้องกรอก', '-')}"
                text += f"\nลำดับการดำเนินการและติดต่อ: {rec.get('ลำดับขั้นตอนการดำเนินการและติดต่อ', '-')}"
                text += f"\nส่งเอกสารที่: {rec.get('ส่งเอกสาร', '-')}"
                text += f"\nเอกสารแนบ: {rec.get('เอกสารที่ต้องการ', '-')}"
                text += f"\nหมายเหตุ: {rec.get('หมายเหตุ', '-')}\n\n"
                texts.append(text.strip())
        case 'ตารางสอน':
            for rec in record:
                text = f"**ตารางสอน {rec.get('ตารางสอน', '-')}**"
                for field in rec.get('รายการทั้งหมด', []):
                    text += f"\nวัน{field.get('วันสอน', '-')}"
                    text += f"\nเวลา: {field.get('เวลาสอน', '-')}"
                    text += f"\nวิชา: {field.get('ชื่อวิชา', '-')}"
                    text += f"\nห้อง: {field.get('ห้องสอน', '-')}"
                    text += f"\nชั้น: {field.get('ชั้น', '-')}\n"
                texts.append(text.strip())
        case 'อาคาร/ตึก':
            for rec in record:
                text = f"**อาคาร {rec.get('อาคาร/ตึก', '-')} / ตึก {rec.get('อาคาร/ตึก', '-')}**"
                text += f"\n{rec.get('ชื่ออาคาร', '-')}"
                text += f"\nรายละเอียด: {rec.get('รายละเอียดอาคาร', '-')}"
                for field in rec.get('ชั้นและห้อง', []):
                    text += f"\nชั้นและห้อง: {field}"
                text += f"\nลิ้งแผนที่: {rec.get('ที่อยู่แผนที่', '-')}\n\n"
                texts.append(text.strip())
        case 'ปฏิทินการศึกษา' :
            text = f"**ปฏิทินการศึกษา{record[0].get('ปฏิทินการศึกษา')}**\n"
            for rec in record:
                text += f"{rec.get('กิจกรรม', '-')}"
                text += "\nภาคการศึกษา / เทอม"
                text += f"\nที่1 : {rec.get('วันที่ (ภาคการศึกษาที่ 1)', '-')}"
                if rec.get('วันที่ (ภาคการศึกษาที่ 2)', '-') != '-':
                    text += f"\nที่2 : {rec.get('วันที่ (ภาคการศึกษาที่ 2)', '-')}"
                if rec.get('วันที่ (ภาคการศึกษาฤดูร้อน)', '-') != '-':
                    text += f"\nฤดูร้อน : {rec.get('วันที่ (ภาคการศึกษาฤดูร้อน)', '-')}"
                text += "\n"
            texts.append(text.strip())

    return texts