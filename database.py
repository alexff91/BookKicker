import psycopg2

import tokens


class DataBase:
    """work with DataBase"""

    def __init__(self):
        # Create table and DB if they does not exists
        # conn = sqlite3.connect('books_pos_table.sqlite')
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
            CREATE TABLE IF NOT EXISTS books_pos_table (
            userId INTEGER, 
            bookName TEXT UNIQUE,
            pos INTEGER);
            """
        cursor.execute(sql)
        sql2 = """
            CREATE TABLE IF NOT EXISTS curent_book_table (
            userId INTEGER PRIMARY KEY, 
            chatId INTEGER,
            bookName TEXT UNIQUE,
            isAutoSend INTEGER,
            lang TEXT);
            """
        cursor.execute(sql2)
        cursor.close()
        conn.close()

    def update_book_pos(self, user_id, book_name, newpos):
        # Update pos value for user and book
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
        INSERT INTO books_pos_table (userId, bookName, pos) VALUES({0}, '{1}', {2})
        ON CONFLICT (bookName) 
        DO 
         UPDATE SET pos={2} ;
        UPDATE books_pos_table SET pos={2} WHERE userId={0} and bookName='{1}';
        """.format(user_id, book_name, newpos)
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        return 0

    def update_current_book(self, user_id, chat_id, book_name, lang):
        # Update book currently reading by user
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
        INSERT INTO curent_book_table (userId, chatId, bookName, isAutoSend, lang) VALUES({0}, {1}, '{2}', {3},'{4}')
        ON CONFLICT (userId) 
        DO 
         UPDATE SET chatId={1}, bookName='{2}', isAutoSend={3},lang='{4}';
        UPDATE curent_book_table SET bookName='{2}', isAutoSend=1, lang ='{4}'  WHERE userId={0};
        """.format(user_id, chat_id, book_name, 1, lang)
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        return 0

    def update_auto_status(self, user_id):
        # change status of auto-sending
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()

        sql = """
        INSERT INTO curent_book_table (isAutoSend, userId)
        VALUES(1,{0}) 
        ON CONFLICT (userId) 
        DO 
        UPDATE SET isAutoSend=(select 1-isAutoSend from curent_book_table where userId = {0});
         """.format(user_id)
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        return 0

    def update_lang(self, user_id, lang):
        # change lang for user
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
        INSERT INTO curent_book_table (lang, userId)
        VALUES('{0}',{1}) 
        ON CONFLICT (userId) 
        DO 
         UPDATE SET lang='{2}';
         """.format(lang, user_id, lang)
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        return 0

    def get_current_book(self, user_id):
        # get current book of user
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
        SELECT bookname FROM curent_book_table WHERE userId={0};
        """.format(user_id)
        cursor.execute(sql)
        fetchone = cursor.fetchone()
        cursor.close()
        conn.close()
        if fetchone is None or None in fetchone:
            return None
        return str(fetchone[0])

    def get_auto_status(self, user_id):
        # return status of auto-sending
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
            SELECT isAutoSend FROM curent_book_table WHERE userId={0};
            """.format(user_id)
        cursor.execute(sql)
        fetchone = cursor.fetchone()
        cursor.close()
        conn.close()
        if fetchone is None or None in fetchone:
            res = -1
        else:
            res = int(fetchone[0])
        return res

    def get_user_books(self, user_id):
        # Return all user's books
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
        SELECT bookName FROM books_pos_table WHERE userId={0};
        """.format(user_id)
        cursor.execute(sql)
        select_res = cursor.fetchall()
        cursor.close()
        conn.close()
        res = list()
        for item in select_res:
            res.append(item[0])
        return res

    def get_users_for_autosend(self):
        # Return all user with auto-sending ON
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
        SELECT userId, chatId FROM curent_book_table WHERE isAutoSend=1;
        """
        cursor.execute(sql)
        select_res = cursor.fetchall()
        cursor.close()
        conn.close()
        return select_res

    def get_pos(self, user_id, book_name):
        # Return pos value for user and book
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
        SELECT pos FROM books_pos_table WHERE userId={0} and bookName='{1}';
        """.format(user_id, book_name)
        cursor.execute(sql)
        fetchone = cursor.fetchone()
        if fetchone is None or None in fetchone:
            res = -1
        else:
            res = int(fetchone[0])
        cursor.close()
        conn.close()
        return res

    def get_lang(self, user_id):
        # Return lang for user
        conn = psycopg2.connect(user=tokens.user,
                                password=tokens.password,
                                host=tokens.host,
                                port="5432",
                                database=tokens.db)
        cursor = conn.cursor()
        sql = """
        SELECT lang FROM curent_book_table WHERE userId={0};
        """.format(user_id)
        cursor.execute(sql)
        fetchone = cursor.fetchone()
        if fetchone is None or None in fetchone:
            res = None
        else:
            res = fetchone[0]
        cursor.close()
        conn.close()
        return res
