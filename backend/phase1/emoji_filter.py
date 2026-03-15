"""
Emoji Filter — removes reviews that contain emoji characters.

Emoji-heavy reviews tend to be low-signal noise (e.g. "👍👍👍", "🔥🔥 best app").
Uses regex-based Unicode emoji detection.
"""

import re
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# Comprehensive Unicode emoji pattern covering:
# - Emoticons, Dingbats, Symbols, Transport/Map symbols
# - Supplemental symbols, Flags, Enclosed characters
# - Various emoji modifiers and components
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc symbols & pictographs
    "\U0001F680-\U0001F6FF"  # Transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Enclosed characters
    "\U0001F900-\U0001F9FF"  # Supplemental symbols
    "\U0001FA00-\U0001FA6F"  # Chess symbols
    "\U0001FA70-\U0001FAFF"  # Symbols extended-A
    "\U00002600-\U000026FF"  # Misc symbols
    "\U0000FE00-\U0000FE0F"  # Variation selectors
    "\U0000200D"             # Zero-width joiner
    "\U00000023\U0000FE0F\U000020E3"  # Keycap #
    "]+",
    flags=re.UNICODE,
)


def contains_emoji(text: str) -> bool:
    """Check if text contains any emoji characters."""
    return bool(EMOJI_PATTERN.search(text))


def remove(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove reviews that contain emoji characters in their text.

    Args:
        reviews: List of review dictionaries (must have 'content' field).

    Returns:
        List of reviews with no emoji characters in text.
    """
    filtered = []
    removed_count = 0

    for review in reviews:
        text = review.get("content", "")
        if text and contains_emoji(text):
            removed_count += 1
        else:
            filtered.append(review)

    logger.info(
        f"Emoji filter: {removed_count}/{len(reviews)} reviews removed "
        f"({len(filtered)} remaining)"
    )
    return filtered
