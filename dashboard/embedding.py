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
from collections import defaultdict
from typhoon_ocr import ocr_document
import tempfile
from sentence_transformers import SentenceTransformer

from transformers import AutoTokenizer
import re
from dotenv import load_dotenv
load_dotenv()

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")
model = SentenceTransformer("./models/bge-m3")

def split_blocks(text: str) -> list[str]:
    pattern = r'\*\*(.*?)\*\*'
    parts = re.split(pattern, text)
    blocks = []
    
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i+1].strip() if i + 1 < len(parts) else ""
        combined = f"{title}\n{content}"
        blocks.append(combined)

    if not blocks:
        blocks = [text.strip()]
    return blocks

def get_data_chunk(data_text: str, max_tokens: int, file_type: str, overlap: int = 50) -> list[str]:
    cleaned_text = clean_text(data_text)
    blocks = split_blocks(cleaned_text) if file_type == 'txt' else [cleaned_text]

    chunks = []
    for block in blocks:
        tokens = tokenizer.encode(block, add_special_tokens=False)
        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            chunk = tokenizer.decode(tokens[start:end])
            chunks.append(chunk)
            start += max_tokens - overlap
    return chunks


def clean_text(text: str) -> str:
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ ]{2,}', ' ', text)
    text = re.sub(r'[\u200b\u200c\u200d]', '', text)
    text = re.sub(r'\t{2,}', '\t', text)
    text = re.sub(r'-{2,}', ' ', text)
    text = re.sub(r'(\|\s*)+', '', text)
    text = re.sub(r'<td>\s*</td>', '-', text)
    text = re.sub(r'<td>\s*(.*?)\s*</td>', r'| \1 ', text)
    text = re.sub(r'(?:\| [^\n]+)+', lambda m: m.group(0) + '|', text)
    return text.strip()

def clean_chunks(text: str) -> str:
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text) 
    text = text.replace('"', '')
    return text

def model_embed(chunks: list[str]) -> list[list[float]]:
    cleaned_chunk = [clean_chunks(chunk) for chunk in chunks]
    embeddings = model.encode(cleaned_chunk, show_progress_bar=True, normalize_embeddings=True)
    return embeddings

async def extract_data_from_file(file_bytes: bytes, file_type: str, start: str, stop: str) -> str:
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

async def extract_data_from_pdf(file_bytes: bytes, start: str, stop: str) -> list[str]:
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
                chunks.append(chunk_text)
        os.unlink(tmp_file_path)
        print(chunks)
    return chunks


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


def extract_data_from_csv(file_bytes: bytes) -> list[dict]:
    df = pd.read_csv(BytesIO(file_bytes), encoding='utf-8')
    df.ffill(inplace=True)
    records = df.to_dict(orient='records')

    list_field = ['สาขา']
    valid_list_fields = [f for f in list_field if f in df.columns]
    if valid_list_fields:
        result = merge_records_by_shared_fields(records, list_field)
    elif 'ประเภทรายการ' in df.columns:
        result = group_nested_records(records, 'ประเภทรายการ', ['รายการ', 'ค่าธรรมเนียมฉบับละ', 'เพิ่มเติม'])
    else:
        result = records
    return result

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

def convert_record_to_text(record: list[dict]) -> list[str]:
    first_key = list(record[0].keys())[0] if record else None
    texts = []
    text = ""
    match first_key:
        case 'การศึกษา':
            first_group = ""
            for rec in record:
                if rec.get('การศึกษา', '-') == 'ปริญญาตรี':
                    if first_group == rec.get('คณะ', '-'):
                        text += f"""หลักสูตร: {rec.get('หลักสูตร', '-')}
ระยะเวลาหลักสูตร: {rec.get('ระยะเวลาหลักสูตร', '-')}
สำเร็จการศึกษา: {rec.get('สำเร็จการศึกษา', '-')}
สาขา: """
                        for field in rec.get('สาขา', []):
                            text += f"{field}, "
                    else:
                        if first_group != "":
                            texts.append(text.strip())
                        text = f"""การศึกษา: {rec.get('การศึกษา', '-')}
คณะ: {rec.get('คณะ', '-')}
\nหลักสูตร: {rec.get('หลักสูตร', '-')}
ระยะเวลาหลักสูตร: {rec.get('ระยะเวลาหลักสูตร', '-')}
สำเร็จการศึกษา: {rec.get('สำเร็จการศึกษา', '-')}
สาขา: """
                        for field in rec.get('สาขา', []):
                            text += f"{field}, "
                        
                    first_group = rec.get('คณะ', '-')
                else:
                    if first_group == "":
                        text += f"""\nคณะ: {rec.get('คณะ', '-')}
หลักสูตร: {rec.get('หลักสูตร', '-')}
ระยะเวลาหลักสูตร: {rec.get('ระยะเวลาหลักสูตร', '-')}
สำเร็จการศึกษา: {rec.get('สำเร็จการศึกษา', '-')}
สาขา: """
                        for field in rec.get('สาขา', []):
                            text += f"{field}, "
                    else:
                        if first_group != "":
                            texts.append(text.strip())
                        text = f"""การศึกษา: {rec.get('การศึกษา', '-')}
\nคณะ: {rec.get('คณะ', '-')}
หลักสูตร: {rec.get('หลักสูตร', '-')}
ระยะเวลาหลักสูตร: {rec.get('ระยะเวลาหลักสูตร', '-')}
สำเร็จการศึกษา: {rec.get('สำเร็จการศึกษา', '-')}
สาขา: """
                        for field in rec.get('สาขา', []):
                            text += f"{field}, "
                        first_group = ""
        case 'อาจารย์สาขา':
            text = f"**อาจารย์ประจำสาขาวิศวกรรมคอมพิวเตอร์**"
            for rec in record:
                text += f"\nชื่ออาจาร์: {rec.get('ชื่อ', '-')}"
                text += f"\nตำแหน่ง: {rec.get('ตำแหน่ง', '-')}"
        case 'วันหยุดราชการ':
            text = f"**วันหยุดราชการ/วันหยุดสำคัญ**"
            for rec in record:
                text += f"**วันที่ {rec.get('วัน', '-')} /"
                text += f"{rec.get('วันที่', '-')} {rec.get('เดือน', '-')}"
                text += f" เป็นวันหยุดของ{rec.get('วันหยุดราชการ', '-')}**, "
        case 'ประเภทรายการ':
            text = f"**รายการสำหรับขอหนังสือรับรองต่าง ๆ**"
            for rec in record:
                text += f"\n\n*ประเภทรายการ: {rec.get('ประเภทรายการ', '-')}*"
                for field in rec.get('รายการทั้งหมด', []):
                    text += f"\n\"รายการ: {field.get('รายการ', '-')}"
                    text += f"\nค่าธรรมเนียมฉบับละ: {field.get('ค่าธรรมเนียมฉบับละ', '-')}"
                    text += f" เพิ่มเติม: {field.get('เพิ่มเติม', '-')}\"\n"
    if text.strip():
        texts.append(text.strip())
    return texts