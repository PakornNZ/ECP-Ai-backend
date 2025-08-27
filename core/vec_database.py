from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, PointStruct
import os
from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "ecp-ai"
client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

# points = client.scroll(COLLECTION_NAME, with_vectors=True, with_payload=True, limit=10000)
# points_data = points[0]

# for point in points_data:
#     point_struct = PointStruct(
#         id=point.id,
#         vector=point.vector,
#         payload=point.payload
#     )
#     client.upsert(collection_name="vec-ecp-ai", points=[point_struct])