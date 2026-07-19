"""素材去重工具 —— embedding 相似度判重 + 簇内保留规则"""
import numpy as np
from typing import Optional


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """计算两个向量的余弦相似度"""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def deduplicate(
    embeddings: list[np.ndarray],
    threshold: float = 0.85,
) -> list[Optional[str]]:
    """根据 embedding 相似度判重

    返回：每个素材的相似素材 ID，None 表示不重复
    相似度 ≥ threshold 的判定为重复簇

    Args:
        embeddings: 素材 embedding 向量列表
        threshold: 相似度阈值（默认 0.85）
    """
    n = len(embeddings)
    similar_to: list[Optional[str]] = [None] * n

    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= threshold:
                # j 标记为与 i 相似（优先保留 i）
                if similar_to[j] is None:
                    similar_to[j] = f"mt-{i:03d}"

    return similar_to


def cluster_keep(
    cluster: list[dict],
) -> list[dict]:
    """在重复簇内按信息密度 + 发布时间择优保留

    规则：
    1. 信息密度分高者优先
    2. 同分保留发布更早者（原创概率高）

    Args:
        cluster: 重复簇中的素材列表，每个含 info_density 和 publish_time

    Returns:
        排序后的素材列表（第一位是最优）
    """
    return sorted(
        cluster,
        key=lambda m: (
            -m.get("info_density", {}).get("score", 0),
            m.get("publish_time", "9999-12-31"),
        ),
    )
