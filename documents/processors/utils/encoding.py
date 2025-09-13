# documents/utils/encoding.py
import logging

import chardet
from typing import Tuple

logger = logging.getLogger(__name__)


class DocumentEncoder:
    """
    Utility class for handling document encoding, specially designed for
    Italian documents that may contain accented characters.
    """

    ITALIAN_ENCODINGS = [
        "utf-8",
        "iso-8859-1",  # Latin-1, common in older systems
        "iso-8859-15",  # Latin-9, better for Euro symbol
        "cp1252",  # Windows-1252, very common in Italian Windows systems
        "utf-16",  # Sometimes used in newer documents
        "macintosh",  # For documents from Mac systems
    ]

    @classmethod
    def decode_file_content(cls, file_content: bytes) -> Tuple[str, str]:
        """
        Intelligently decodes file content using multiple strategies.
        Returns both the decoded content and the encoding used.

        Args:
            file_content: The raw bytes from the file

        Returns:
            Tuple containing (decoded_content, encoding_used)

        Raises:
            UnicodeDecodeError: If content cannot be decoded with any encoding
        """
        # First try automatic detection with chardet
        detection = chardet.detect(file_content)
        detected_encoding = detection["encoding"]
        confidence = detection["confidence"]

        logger.debug(
            f"Detected encoding: {detected_encoding} (confidence: {confidence})"
        )

        # If detection is confident, try that first
        if confidence > 0.8:
            try:
                return cls._try_decode(file_content, detected_encoding)
            except UnicodeDecodeError:
                logger.debug(
                    f"Failed to decode with detected encoding {detected_encoding}"
                )

        # Try our list of known Italian encodings
        for encoding in cls.ITALIAN_ENCODINGS:
            try:
                return cls._try_decode(file_content, encoding)
            except UnicodeDecodeError:
                continue

        # If we get here, try a more aggressive approach with error handling
        for encoding in cls.ITALIAN_ENCODINGS:
            try:
                content = file_content.decode(encoding, errors="replace")
                logger.warning(
                    f"Had to use 'replace' error handling with {encoding}. "
                    "Some characters may be incorrect."
                )
                return content, encoding
            except Exception:
                continue

        raise UnicodeDecodeError(
            "utf-8",
            file_content,
            0,
            len(file_content),
            "Could not decode file with any known encoding",
        )

    @staticmethod
    def _try_decode(content: bytes, encoding: str) -> Tuple[str, str]:
        """
        Attempts to decode content with a specific encoding.
        Returns the decoded content and the successful encoding.
        """
        try:
            decoded = content.decode(encoding)
            logger.debug(f"Successfully decoded with {encoding}")
            return decoded, encoding
        except UnicodeDecodeError as e:
            logger.debug(f"Failed to decode with {encoding}: {str(e)}")
            raise
