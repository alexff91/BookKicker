"""
Improved Book Reader with enhanced tracking
"""

import os
import config
from txt_file import TxtFile
from typing import Tuple, Optional


class ImprovedBookReader:
    """Enhanced book reader with character and line tracking"""

    def __init__(self):
        self.txt_file = TxtFile()

    def read_portion(self, book_name: str, pos: int, chunk_size: int = 893) -> Tuple[str, int, int]:
        """
        Read a portion of text from a book

        Args:
            book_name: Name of the book file
            pos: Current position (line number)
            chunk_size: Size of chunk to read (characters)

        Returns:
            Tuple of (text, new_position, characters_read)
        """
        try:
            file_path = os.path.join(config.path_for_save, book_name)

            if not os.path.exists(file_path):
                return "", pos, 0

            # Read text piece
            text_piece, new_pos = self.txt_file.read_piece(file_path, pos, chunk_size)

            if not text_piece:
                return "", pos, 0

            # Count characters (excluding whitespace for better accuracy)
            chars_read = len(text_piece.strip())

            return text_piece, new_pos, chars_read

        except Exception as e:
            print(f"Error reading book portion: {e}")
            return "", pos, 0

    def get_book_length(self, book_name: str) -> int:
        """
        Get total number of lines in a book

        Args:
            book_name: Name of the book file

        Returns:
            Total number of lines
        """
        try:
            file_path = os.path.join(config.path_for_save, book_name)

            if not os.path.exists(file_path):
                return 0

            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)

        except Exception as e:
            print(f"Error getting book length: {e}")
            return 0

    def get_book_info(self, book_name: str) -> dict:
        """
        Get detailed information about a book

        Args:
            book_name: Name of the book file

        Returns:
            Dictionary with book information
        """
        try:
            file_path = os.path.join(config.path_for_save, book_name)

            if not os.path.exists(file_path):
                return {}

            # Get file size
            file_size = os.path.getsize(file_path)

            # Read entire file for analysis
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            total_chars = len(content)
            total_words = len(content.split())
            total_lines = content.count('\n')

            # Estimate reading time (average 200 words per minute)
            estimated_minutes = total_words / 200

            return {
                'file_size': file_size,
                'total_chars': total_chars,
                'total_words': total_words,
                'total_lines': total_lines,
                'estimated_minutes': int(estimated_minutes)
            }

        except Exception as e:
            print(f"Error getting book info: {e}")
            return {}

    def read_lines(self, book_name: str, start_line: int, num_lines: int = 10) -> Tuple[str, int]:
        """
        Read specific number of lines from a book

        Args:
            book_name: Name of the book file
            start_line: Line number to start from
            num_lines: Number of lines to read

        Returns:
            Tuple of (text, lines_read)
        """
        try:
            file_path = os.path.join(config.path_for_save, book_name)

            if not os.path.exists(file_path):
                return "", 0

            lines = []
            with open(file_path, 'r', encoding='utf-8') as f:
                # Skip to start line
                for _ in range(start_line):
                    next(f, None)

                # Read num_lines
                for i in range(num_lines):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)

            text = ''.join(lines)
            return text, len(lines)

        except Exception as e:
            print(f"Error reading lines: {e}")
            return "", 0

    def search_in_book(self, book_name: str, search_term: str,
                      max_results: int = 10) -> list:
        """
        Search for a term in a book

        Args:
            book_name: Name of the book file
            search_term: Term to search for
            max_results: Maximum number of results to return

        Returns:
            List of tuples (line_number, line_text)
        """
        try:
            file_path = os.path.join(config.path_for_save, book_name)

            if not os.path.exists(file_path):
                return []

            results = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if search_term.lower() in line.lower():
                        results.append((line_num, line.strip()))
                        if len(results) >= max_results:
                            break

            return results

        except Exception as e:
            print(f"Error searching in book: {e}")
            return []

    def get_context(self, book_name: str, position: int,
                   before: int = 2, after: int = 2) -> str:
        """
        Get context around a specific position

        Args:
            book_name: Name of the book file
            position: Line number
            before: Lines to include before
            after: Lines to include after

        Returns:
            Text with context
        """
        try:
            start = max(0, position - before)
            total_lines = before + 1 + after

            text, _ = self.read_lines(book_name, start, total_lines)
            return text

        except Exception as e:
            print(f"Error getting context: {e}")
            return ""
