#!/usr/bin/env python3
"""
Database Migration Script
Migrates data from old database schema to new improved schema
"""

import sys
import logging
from database import DataBase as OldDatabase
from database_improved import ImprovedDatabase
import psycopg2
import tokens

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigration:
    """Handles migration from old to new database schema"""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.old_db = None
        self.new_db = None

    def connect_old_db(self):
        """Connect to old database"""
        try:
            conn = psycopg2.connect(
                user=tokens.user,
                password=tokens.password,
                host=tokens.host,
                port="5432",
                database=tokens.db
            )
            logger.info("Connected to old database")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to old database: {e}")
            raise

    def check_old_tables_exist(self):
        """Check if old tables exist"""
        try:
            conn = self.connect_old_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('books_pos_table', 'curent_book_table')
            """)

            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()

            if 'books_pos_table' not in tables:
                logger.warning("Old books_pos_table not found")
                return False
            if 'curent_book_table' not in tables:
                logger.warning("Old curent_book_table not found")
                return False

            logger.info("Old tables found")
            return True
        except Exception as e:
            logger.error(f"Error checking old tables: {e}")
            return False

    def migrate_books_positions(self):
        """Migrate books_pos_table data"""
        logger.info("Migrating books position data...")

        try:
            conn = self.connect_old_db()
            cursor = conn.cursor()

            # Get old data
            cursor.execute("SELECT userId, bookName, pos FROM books_pos_table")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            logger.info(f"Found {len(rows)} book position records")

            if self.dry_run:
                logger.info("DRY RUN: Would migrate book positions")
                for row in rows[:5]:  # Show first 5
                    logger.info(f"  - User {row[0]}: {row[1]} at position {row[2]}")
                if len(rows) > 5:
                    logger.info(f"  ... and {len(rows) - 5} more")
                return True

            # Insert into new database
            new_db = ImprovedDatabase()
            success_count = 0

            for user_id, book_name, pos in rows:
                try:
                    new_db.update_book_pos(user_id, book_name, pos)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to migrate position for user {user_id}, book {book_name}: {e}")

            logger.info(f"Successfully migrated {success_count}/{len(rows)} book position records")
            return True

        except Exception as e:
            logger.error(f"Error migrating book positions: {e}")
            return False

    def migrate_current_books(self):
        """Migrate curent_book_table data"""
        logger.info("Migrating current book data...")

        try:
            conn = self.connect_old_db()
            cursor = conn.cursor()

            # Get old data
            cursor.execute("""
                SELECT userId, chatId, bookName, isAutoSend, lang, audio, rare
                FROM curent_book_table
            """)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            logger.info(f"Found {len(rows)} user settings records")

            if self.dry_run:
                logger.info("DRY RUN: Would migrate user settings")
                for row in rows[:5]:
                    logger.info(f"  - User {row[0]}: lang={row[4]}, auto={row[3]}, rare={row[6]}")
                if len(rows) > 5:
                    logger.info(f"  ... and {len(rows) - 5} more")
                return True

            # Insert into new database
            new_db = ImprovedDatabase()
            success_count = 0

            for user_id, chat_id, book_name, is_auto, lang, audio, rare in rows:
                try:
                    # Use context manager to update all fields at once
                    with new_db.get_cursor() as cur:
                        # Convert old format to new
                        audio_bool = audio if isinstance(audio, bool) else False
                        rare_int = int(rare) if rare else 12
                        lang_str = lang if lang else 'ru'
                        is_auto_bool = bool(is_auto) if is_auto is not None else False

                        cur.execute("""
                            INSERT INTO current_book_table
                                (user_id, chat_id, book_name, is_auto_send, lang, audio, rare)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (user_id) DO UPDATE SET
                                chat_id = %s,
                                book_name = %s,
                                is_auto_send = %s,
                                lang = %s,
                                audio = %s,
                                rare = %s
                        """, (user_id, chat_id, book_name, is_auto_bool, lang_str, audio_bool, rare_int,
                              chat_id, book_name, is_auto_bool, lang_str, audio_bool, rare_int))

                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to migrate settings for user {user_id}: {e}")

            logger.info(f"Successfully migrated {success_count}/{len(rows)} user settings records")
            return True

        except Exception as e:
            logger.error(f"Error migrating current books: {e}")
            return False

    def calculate_book_metadata(self):
        """Calculate and add metadata for existing books"""
        logger.info("Calculating book metadata...")

        if self.dry_run:
            logger.info("DRY RUN: Would calculate metadata for books")
            return True

        try:
            import os
            from pathlib import Path

            new_db = ImprovedDatabase()

            # Get all unique books from books_pos_table
            conn = self.connect_old_db()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT userId, bookName FROM books_pos_table")
            books = cursor.fetchall()
            cursor.close()
            conn.close()

            logger.info(f"Calculating metadata for {len(books)} books")

            success_count = 0
            for user_id, book_name in books:
                try:
                    # Try to find and analyze the book file
                    file_path = Path(f"files/{book_name}")

                    if file_path.exists():
                        # Get file size
                        file_size = file_path.stat().st_size

                        # Count lines
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            total_lines = len(lines)
                            total_chars = sum(len(line) for line in lines)

                        # Estimate reading time (200 words per minute, ~5 chars per word)
                        estimated_minutes = (total_chars // 5) // 200

                        # Extract format from filename
                        file_format = 'txt'

                        # Try to extract title from filename
                        title = book_name.replace(f"{user_id}_", "").replace(".txt", "")

                        # Add metadata
                        new_db.add_book_metadata(
                            user_id=user_id,
                            book_name=book_name,
                            title=title,
                            file_format=file_format,
                            file_size=file_size,
                            total_characters=total_chars,
                            estimated_time=estimated_minutes
                        )

                        # Update total_lines in books_pos_table
                        new_db.update_book_pos(user_id, book_name, 0, total_lines)

                        success_count += 1
                    else:
                        logger.warning(f"Book file not found: {file_path}")

                except Exception as e:
                    logger.error(f"Failed to calculate metadata for {book_name}: {e}")

            logger.info(f"Successfully calculated metadata for {success_count}/{len(books)} books")
            return True

        except Exception as e:
            logger.error(f"Error calculating book metadata: {e}")
            return False

    def backup_old_tables(self):
        """Backup old tables before migration"""
        if self.dry_run:
            logger.info("DRY RUN: Would backup old tables")
            return True

        logger.info("Backing up old tables...")

        try:
            conn = self.connect_old_db()
            cursor = conn.cursor()

            # Create backup tables
            cursor.execute("""
                DROP TABLE IF EXISTS books_pos_table_backup;
                CREATE TABLE books_pos_table_backup AS SELECT * FROM books_pos_table;
            """)

            cursor.execute("""
                DROP TABLE IF EXISTS curent_book_table_backup;
                CREATE TABLE curent_book_table_backup AS SELECT * FROM curent_book_table;
            """)

            conn.commit()
            cursor.close()
            conn.close()

            logger.info("Successfully backed up old tables")
            return True

        except Exception as e:
            logger.error(f"Error backing up tables: {e}")
            return False

    def run_migration(self, backup=True):
        """Run full migration"""
        logger.info("=" * 60)
        logger.info("Starting Database Migration")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")

        # Check if old tables exist
        if not self.check_old_tables_exist():
            logger.error("Old tables not found. Migration cannot proceed.")
            return False

        # Backup old tables
        if backup and not self.dry_run:
            if not self.backup_old_tables():
                logger.error("Backup failed. Aborting migration.")
                return False

        # Initialize new database (creates new tables)
        if not self.dry_run:
            logger.info("Initializing new database schema...")
            ImprovedDatabase()
            logger.info("New database schema initialized")

        # Migrate data
        steps = [
            ("Book Positions", self.migrate_books_positions),
            ("User Settings", self.migrate_current_books),
            ("Book Metadata", self.calculate_book_metadata)
        ]

        for step_name, step_func in steps:
            logger.info(f"\n--- {step_name} ---")
            try:
                if not step_func():
                    logger.error(f"Failed to migrate {step_name}")
                    return False
            except Exception as e:
                logger.error(f"Error during {step_name}: {e}")
                return False

        logger.info("\n" + "=" * 60)
        if self.dry_run:
            logger.info("DRY RUN COMPLETED - Run without --dry-run to apply changes")
        else:
            logger.info("MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        return True


def main():
    """Main migration entry point"""
    dry_run = '--dry-run' in sys.argv
    no_backup = '--no-backup' in sys.argv

    migration = DatabaseMigration(dry_run=dry_run)

    try:
        success = migration.run_migration(backup=not no_backup)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
