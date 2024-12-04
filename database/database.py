import contextlib
import sqlite3
from typing import Generator


class SQLitePool:
    def __init__(self, filename: str, pool_size: int):
        self.filename = filename
        self.pool_size = pool_size
        self.connection_pool = self.make_connections(
            filename=filename, pool_size=pool_size
        )

    def make_connections(
        self, filename: str, pool_size: int
    ) -> list[sqlite3.Connection]:
        pool = []
        for _ in range(pool_size):
            connection = sqlite3.connect(filename, check_same_thread=False)
            pool.append(connection)
        return pool

    def aquire(self) -> sqlite3.Connection:
        if len(self.connection_pool) == 0:
            return sqlite3.connect(self.filename)
        return self.connection_pool.pop()

    def release(self, connection):
        if len(self.connection_pool) < 5:
            self.connection_pool.append(connection)


class SQLiteDatabase:
    def __init__(self, filename: str, pool_size: int = 5):
        self.filename = filename
        self.connection_pool = SQLitePool(filename=filename, pool_size=pool_size)

    @contextlib.contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        connection = self.connection_pool.aquire()
        cursor = connection.cursor()
        try:
            yield cursor
        except Exception as e:
            raise e
        finally:
            connection.commit()
            cursor.close()
            self.connection_pool.release(connection)

    def create_empty_tables(self, statements: list[str]):
        with self.get_cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)


if __name__ == '__main__':
    import json

    create_users_query = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        city TEXT,
        gender TEXT,
        preferences TEXT,
        description TEXT,
        active INTEGER CHECK(active in (0, 1)) DEFAULT 1,
        current_profile_idx INTEGER DEFAULT 0
    )
    '''

    create_likes_query = '''
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY,
        liker INTEGER,
        person INTEGER,
        FOREIGN KEY (liker) REFERENCES users(id),
        FOREIGN KEY (person) REFERENCES users(id)
    )
    '''
    db = SQLiteDatabase('./database/database.sqlite')
    with db.get_cursor() as cursor:
        cursor.execute(create_users_query)
        cursor.execute(create_likes_query)
        cursor.connection.commit()
        with open('./profiles/profiles.json', 'r', encoding='utf-8') as file:
            profiles = json.load(file)
            insert_profile_query = '''
            INSERT INTO users(
                name, age, city, gender,
                preferences, description
            )
            VALUES (?, ?, ?, ?, ?, ?)
            '''
            for profile in profiles:
                cursor.execute(
                    insert_profile_query,
                    [
                        profile['name'],
                        profile['age'],
                        profile['city'],
                        profile['gender'],
                        profile['preferences'],
                        profile['description'],
                    ],
                )
