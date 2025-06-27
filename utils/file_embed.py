from typing import Annotated, List
from fastapi import UploadFile, File
from pypdf import PdfReader

async def file_embed(files: Annotated[List[UploadFile], File()]):
    for file in files:

        # *text
        # contents = await file.read()
        # read = contents.decode("utf-8")
        # print(read)

        # *pdf
        contents = PdfReader(file)