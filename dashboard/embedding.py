import os
from io import BytesIO
from pypdf import PdfReader
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
import json
from typhoon_ocr import ocr_document
import tempfile
import tiktoken
from sentence_transformers import SentenceTransformer
import re
from dotenv import load_dotenv
load_dotenv()


def get_data_chunk(data_text, max_tokens: int = 512, overlap: int = 50):
    encoding = tiktoken.get_encoding("cl100k_base")
    cleaned_text = clean_text(data_text)
    tokens = encoding.encode(cleaned_text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk = encoding.decode(tokens[start:end])
        chunks.append(chunk)
        start += max_tokens - overlap
    return chunks

def clean_text(text: str) -> str:
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ ]{2,}', ' ', text)
    text = re.sub(r'\t{2,}', '\t', text)
    return text.strip()

def model_embed(chunks: list[str]) -> list[list[float]]:
    model = SentenceTransformer(
        "./nomic-embed-text-v2-moe", 
        trust_remote_code=True
    )
    embeddings = model.encode(chunks, show_progress_bar=True, prompt_name="passage")
    return embeddings

async def extract_data_from_file(file_bytes: bytes, file_type: str) -> list[list[float]]:
    data_text = []

    match file_type :
        case 'txt':
            try:
                data_text.append(file_bytes.decode('utf-8'))
            except UnicodeDecodeError:
                data_text.append(file_bytes.decode('latin1'))
            data_text = "\n".join(data_text)
            chunks = get_data_chunk(data_text)
        case 'pdf':
            with BytesIO(file_bytes) as pdf_stream:
                contents = PdfReader(pdf_stream)
                for page in enumerate(contents.pages):
                    text = page[1].extract_text()
                    if text:
                        data_text.append(text.strip())
                if not data_text:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(file_bytes)
                        tmp_file_path = tmp_file.name
                        
                    for page_num in range(1, len(contents.pages) + 1):
                        ocr_text = ocr_document(
                            pdf_or_image_path=tmp_file_path,
                            task_type="default",
                            page_num=page_num
                        )
                        data_text.append(ocr_text)
                    os.unlink(tmp_file_path)
            data_text = "\n".join(data_text)
            chunks = get_data_chunk(data_text)
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
            chunks = get_data_chunk(data_text)
        case 'json':
            json_data = json.loads(file_bytes.decode('utf-8'))
            data_text = json.dumps(json_data, indent=2)
            chunks = get_data_chunk(data_text)
    
    if not data_text:
        return []
    
    return model_embed(chunks)