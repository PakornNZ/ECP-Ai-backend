from sqlmodel import select

import numpy as np

from typing import List

from core.database import *
from core.models import * 


def get_relevant_context(query: str, rag_top_k: int, embedder, session: Session):
    query_embedding = embedder.encode(query).tolist()

    rag_query = session.exec(
        select(RagFiles)
    ).all()

    rag_similarities = []

    for record in rag_query:
        similarity = compute_similarity(
            np.array(query_embedding),
            np.array(record.embed_file)
        )
        rag_similarities.append((record.data_file, similarity))

    is_relevant = check_relevance(rag_similarities)

    if is_relevant:
        rag_context = sorted(rag_similarities, key=lambda x: x[1], reverse=True)[:rag_top_k]
        combined_context = "\n".join([ctx[0] for ctx in rag_context])
    else:
        combined_context = ""

    return combined_context


def compute_similarity(vector1: np.ndarray, vector2: np.ndarray):
    dot_product=np.dot(vector1, vector2)
    norm_vector1=np.linalg.norm(vector1)
    norm_vector2=np.linalg.norm(vector2)
    return dot_product/(norm_vector1*norm_vector2)


def check_relevance(rag_similarities: List[tuple[str, float]], threshold: float=0.6):
    return any(score>threshold for _, score in rag_similarities)