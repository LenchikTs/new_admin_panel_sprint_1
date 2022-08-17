import logging
import sqlite3
from contextlib import contextmanager
import os

from dotenv import load_dotenv

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
import uuid
from dataclasses import dataclass, field
from datetime import datetime

load_dotenv()

@dataclass
class FilmWork:
    title: str
    file_path: str
    creation_date: str
    description: str = field(default='.')
    type: str = field(default='movie')
    rating: float = field(default=0.0)
    created: datetime = field(default=datetime.now())
    modified: datetime = field(default=datetime.now())
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class PersonFilmWork:
    role: str = field(default='actor')
    created_at: datetime = field(default=datetime.now())
    person_id: uuid.UUID = field(default_factory=uuid.uuid4)
    film_work_id: uuid.UUID = field(default_factory=uuid.uuid4)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class Person:
    full_name: str
    created_at: datetime = field(default=datetime.now())
    updated_at: datetime = field(default=datetime.now())
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class Genre:
    name: str
    description: str = field(default='.')
    created: datetime = field(default=datetime.now())
    modified: datetime = field(default=datetime.now())
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class GenreFilmWork:
    created_at: datetime = field(default=datetime.now())
    genre_id: uuid.UUID = field(default_factory=uuid.uuid4)
    film_work_id: uuid.UUID = field(default_factory=uuid.uuid4)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

class PostgresSaver:
    def __init__(self, pg_conn):
        self.pg_connection = pg_conn

    def save_movies_data(self, data):
        curs = self.pg_connection.cursor()
        for movies_data in data:
            curs.execute(
                    "INSERT INTO film_work (id, title, description, creation_date, rating, type, created,"
                    "modified, certificate, file_path) VALUES ('{id}', '{title}', '{description}', NULL,{rating},"
                    "'{type}', NOW(), NOW(), NULL, NULL) ON CONFLICT (id) DO NOTHING;".format(
                        id=movies_data.id, title=movies_data.title.replace('\'', '&#39;'), type=movies_data.type,
                        description=movies_data.description.replace('\'', '&#39;'), rating=movies_data.rating,
                    ))

    def save_persons_data(self, data):
        curs = self.pg_connection.cursor()
        for str_num, persons_data in enumerate(data):
            if str_num % 3000 == 0:
                curs.execute("BEGIN;")
            curs.execute(
                        "INSERT INTO person (id, full_name, created, modified) "
                        "VALUES ('{id}', '{full_name}', NOW(), NOW()) ON CONFLICT (id) DO NOTHING;".format(
                            id=persons_data.id, full_name=persons_data.full_name.replace('\'', '&#39;'), ))
            if str_num % 3000 == 0 or str_num == len(data):
                curs.execute("COMMIT;")

    def save_person_fms_data(self, data):
        curs = self.pg_connection.cursor()
        for str_num, person_fms_data in enumerate(data):
            if str_num % 3000 == 0:
                curs.execute("BEGIN;")
            curs.execute(
            "INSERT INTO person_film_work (id, film_work_id, person_id, role, created) "
            "VALUES ('{id}', '{film_work_id}', '{person_id}', '{role}', NOW()) ON CONFLICT (id) DO NOTHING;".format(
                id=person_fms_data.id, film_work_id=person_fms_data.film_work_id,
                person_id=person_fms_data.person_id, role=person_fms_data.role, ))
            if str_num % 3000 == 0 or str_num == len(data):
                curs.execute("COMMIT;")

    def save_genres_data(self, data):
        curs = self.pg_connection.cursor()
        for genre_data in data:
            curs.execute(
            "INSERT INTO genre (id, name, description, created, modified) "
            "VALUES ('{id}', '{name}', '{description}', NOW(), NOW()) ON CONFLICT (id) DO NOTHING;".format(
                id=genre_data.id, name=genre_data.name, description=genre_data.description))

    def save_genre_fms_data(self, data):
        curs = self.pg_connection.cursor()
        for genre_fms_data in data:
            curs.execute(
            "INSERT INTO genre_film_work (id, film_work_id, genre_id, created) "
            "VALUES ('{id}', '{film_work_id}', '{genre_id}', NOW()) ON CONFLICT (id) DO NOTHING;".format(
                id=genre_fms_data.id, film_work_id=genre_fms_data.film_work_id, genre_id=genre_fms_data.genre_id, ))

class SQLiteLoader:
    def __init__(self, connection):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    def load_movies(self, table_bd):
        film_class = []
        curs = self.connection.cursor()
        curs.execute("SELECT * FROM {} ;".format(table_bd))
        while True:
            data = curs.fetchmany(3000)
            if data:
                for film in range(len(data)):
                    universal_dict = dict(data[film])
                    if table_bd == 'film_work':
                        info = FilmWork(title=universal_dict['title'], file_path=universal_dict['file_path'],
                                    description=universal_dict['description'] if universal_dict['description'] else '',
                                    rating=universal_dict['rating'] if universal_dict['rating'] else 0.0,
                                    type=universal_dict['type'], id=universal_dict['id'],
                                    creation_date=universal_dict['creation_date'])
                    elif table_bd == 'person':
                        info = Person(**universal_dict)
                    elif table_bd == 'person_film_work':
                        info = PersonFilmWork(**universal_dict)
                    elif table_bd == 'genre':
                        info = Genre(name=universal_dict['name'], id=universal_dict['id'],
                                description=universal_dict['description'] if universal_dict['description'] else '')
                    elif table_bd == 'genre_film_work':
                        info = GenreFilmWork(**universal_dict)
                    film_class.append(info)
            else:
                break
        return film_class

def load_from_sqlite(connection: _connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)

    data_movies = sqlite_loader.load_movies('film_work')
    postgres_saver.save_movies_data(data_movies)
    data_persons = sqlite_loader.load_movies('person')
    postgres_saver.save_persons_data(data_persons)
    data_person_fms = sqlite_loader.load_movies('person_film_work')
    postgres_saver.save_person_fms_data(data_person_fms)
    data_genres = sqlite_loader.load_movies('genre')
    postgres_saver.save_genres_data(data_genres)
    data_genre_fms = sqlite_loader.load_movies('genre_film_work')
    postgres_saver.save_genre_fms_data(data_genre_fms)

class SQLite:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.connection = sqlite3.connect(self.file_name)

    def __enter__(self):
        logging.info("Calling __enter__")
        return self.connection

    def __exit__(self, error: Exception, value: object, traceback: object):
        logging.info("Calling __exit__")
        self.connection.commit()
        self.connection.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dsl = {'dbname': os.environ.get('DB_NAME'), 'user': os.environ.get('DB_USER'),
           'password': os.environ.get('DB_PASSWORD'), 'host': '127.0.0.1', 'port': 5432}
    with SQLite(file_name='db.sqlite') as sqlite_conn, psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
