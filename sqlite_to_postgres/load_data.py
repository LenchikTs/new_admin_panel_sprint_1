import sqlite3
from contextlib import contextmanager

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
import uuid
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class FilmWork:
    title: str
    # certificate: str = field(default=None)
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
    created: datetime = field(default=datetime.now())
    person_id: uuid.UUID = field(default_factory=uuid.uuid4)
    film_work_id: uuid.UUID = field(default_factory=uuid.uuid4)
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class Person:
    full_name: str
    created: datetime = field(default=datetime.now())
    modified: datetime = field(default=datetime.now())
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
    created: datetime = field(default=datetime.now())
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
                        id=movies_data.id, title=movies_data.title.replace('\'', '\\\''), type=movies_data.type,
                        description=movies_data.description.replace('\'', '\\\''), rating=movies_data.rating,
                    ))

    def save_persons_data(self, data):
        curs = self.pg_connection.cursor()
        for str_num, persons_data in enumerate(data):
            if str_num % 3000 == 0:
                curs.execute("BEGIN;")
            curs.execute(
                        "INSERT INTO person (id, full_name, created, modified) "
                        "VALUES ('{id}', '{full_name}', NOW(), NOW()) ON CONFLICT (id) DO NOTHING;".format(
                            id=persons_data.id, full_name=persons_data.full_name.replace('\'', '\\\''), ))
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

    def load_movies(self):
        film_class = []
        curs = self.connection.cursor()
        curs.execute("SELECT * FROM film_work ;")
        data = curs.fetchall()
        for film in range(len(data)):
            film_dict = dict(data[film])
            info = FilmWork(title=film_dict['title'], file_path=film_dict['file_path'],
                            description=film_dict['description'] if film_dict['description'] else '',
                            rating=film_dict['rating'] if film_dict['rating'] else 0.0,
                            type=film_dict['type'], id=film_dict['id'], creation_date=film_dict['creation_date'])
            film_class.append(info)
        return film_class

    def load_persons(self):
        person_class = []
        curs = self.connection.cursor()
        curs.execute("SELECT * FROM person;")
        data = curs.fetchall()
        for person in range(len(data)):
            person_dict = dict(data[person])
            info = Person(full_name=person_dict['full_name'], id=person_dict['id'])
            person_class.append(info)
        return person_class

    def load_person_film_works(self):
        person_fm_class = []
        curs = self.connection.cursor()
        curs.execute("SELECT * FROM person_film_work;")
        data = curs.fetchall()
        for person_fm in range(len(data)):
            person_fm_dict = dict(data[person_fm])
            info = PersonFilmWork(role=person_fm_dict['role'], id=person_fm_dict['id'],
                                  film_work_id=person_fm_dict['film_work_id'], person_id=person_fm_dict['person_id'])
            person_fm_class.append(info)
        return person_fm_class

    def load_genres(self):
        genre_class = []
        curs = self.connection.cursor()
        curs.execute("SELECT * FROM genre;")
        data = curs.fetchall()
        for genre in range(len(data)):
            genre_dict = dict(data[genre])
            info = Genre(name=genre_dict['name'], id=genre_dict['id'],
                         description=genre_dict['description'] if genre_dict['description'] else '')
            genre_class.append(info)
        return genre_class

    def load_genre_film_works(self):
        genre_fm_class = []
        curs = self.connection.cursor()
        curs.execute("SELECT * FROM genre_film_work;")
        data = curs.fetchall()
        for genre_fm in range(len(data)):
            genre_fm_dict = dict(data[genre_fm])
            info = GenreFilmWork(film_work_id=genre_fm_dict['film_work_id'], id=genre_fm_dict['id'],
                                 genre_id=genre_fm_dict['genre_id'])
            genre_fm_class.append(info)
        return genre_fm_class

def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)

    data_movies = sqlite_loader.load_movies()
    postgres_saver.save_movies_data(data_movies)
    data_persons = sqlite_loader.load_persons()
    postgres_saver.save_persons_data(data_persons)
    data_person_fms = sqlite_loader.load_person_film_works()
    postgres_saver.save_person_fms_data(data_person_fms)
    data_genres = sqlite_loader.load_genres()
    postgres_saver.save_genres_data(data_genres)
    data_genre_fms = sqlite_loader.load_genre_film_works()
    postgres_saver.save_genre_fms_data(data_genre_fms)

#def save_film_work_to_postgres(conn: psycopg2.extensions.connection, film_work: FilmWork):
    #genre, film_work, person, genre_film_work, person_film_work


if __name__ == '__main__':
    dsl = {'dbname': 'movies_db', 'user': 'app', 'password': '123qwe', 'host': '127.0.0.1', 'port': 5432}
    with sqlite3.connect('db.sqlite') as sqlite_conn, psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
        load_from_sqlite(sqlite_conn, pg_conn)
