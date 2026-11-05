import numpy as np
from sentence_transformers import SentenceTransformer

from config import METRICS_PATH


# =========================
# 1. 读取业务指标知识库
# =========================

with open(
    METRICS_PATH,
    "r",
    encoding="utf-8"
) as f:

    metrics_knowledge = f.read()


# =========================
# 2. 按 ## 标题拆分知识库
# =========================

chunks = metrics_knowledge.split("## ")

chunks = [
    chunk.strip()
    for chunk in chunks
    if chunk.strip()
]


# 去掉最前面的非知识块
if chunks and not chunks[0].startswith("#"):
    chunks = chunks[1:]


# =========================
# 3. 加载 Embedding 模型
# =========================

model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5"
)


# =========================
# 4. 对知识块进行向量化
# =========================

embeddings = model.encode(
    chunks
)


# =========================
# 5. RAG 检索
# =========================

def retrieved_knowledge(
    user_question,
    top_k=3
):
    """
    根据用户问题，从业务指标知识库中
    检索最相关的知识块。
    """

    # 用户问题向量
    query_embedding = model.encode(
        [user_question]
    )[0]

    # 用户问题向量归一化
    query_norm = (
        query_embedding
        / np.linalg.norm(query_embedding)
    )

    # 知识块向量归一化
    embedding_norms = (
        embeddings
        / np.linalg.norm(
            embeddings,
            axis=1,
            keepdims=True
        )
    )

    # 计算余弦相似度
    similarities = (
        embedding_norms
        @ query_norm
    )

    # 获取 Top K
    top_indices = np.argsort(
        similarities
    )[-top_k:][::-1]

    # 整理结果
    results = []

    for index in top_indices:

        results.append(
            {
                "chunk": chunks[index],
                "score": float(
                    similarities[index]
                )
            }
        )

    return results