"""
Batch Chunker — groups reviews into batches of N for LLM calls.

ARCHITECTURE: batch size 50 for LLM context window.
"""

from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_BATCH_SIZE = 50


def chunk(
    reviews: List[Dict[str, Any]],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> List[List[Dict[str, Any]]]:
    """
    Split reviews into batches of at most batch_size.

    Args:
        reviews: List of review dicts.
        batch_size: Max reviews per batch (default 50).

    Returns:
        List of batches, each a list of review dicts.
    """
    batches = []
    for i in range(0, len(reviews), batch_size):
        batches.append(reviews[i : i + batch_size])
    logger.info(
        f"Batch chunker: {len(reviews)} reviews -> {len(batches)} batches "
        f"(batch_size={batch_size})"
    )
    return batches
