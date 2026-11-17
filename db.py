"""Хранение книг, сотрудников и выдач в SQLite."""

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import logic

DB_PATH = Path(__file__).resolve().with_name("corporate_library.db")


def get_connection():
    """Открывает соединение и включает проверку внешних ключей."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Создаёт таблицы и индекс без удаления существующих данных."""
    with closing(get_connection()) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(trim(title)) > 0),
                author TEXT NOT NULL CHECK(length(trim(author)) > 0),
                genre TEXT NOT NULL CHECK(length(trim(genre)) > 0)
            );

            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name TEXT NOT NULL CHECK(length(trim(last_name)) > 0),
                first_name TEXT NOT NULL CHECK(length(trim(first_name)) > 0)
            );

            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL REFERENCES books(id),
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                issued_at TEXT NOT NULL,
                returned_at TEXT
            );

            CREATE UNIQUE INDEX IF NOT EXISTS one_active_loan
            ON loans(book_id)
            WHERE returned_at IS NULL;
            """
        )


def add_book(title: str, author: str, genre: str) -> int:
    """Добавляет экземпляр книги и возвращает его ID."""
    book = logic.validate_book(title, author, genre)

    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO books (title, author, genre) VALUES (?, ?, ?)",
            (book["title"], book["author"], book["genre"]),
        )
        return cursor.lastrowid


def get_books() -> list:
    """Возвращает книги с вычисляемым состоянием: доступна или выдана."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT b.*,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM loans AS l
                       WHERE l.book_id = b.id AND l.returned_at IS NULL
                   ) THEN 'выдана' ELSE 'доступна' END AS availability
            FROM books AS b
            ORDER BY b.id
            """
        ).fetchall()

        return [dict(row) for row in rows]


def add_employee(last_name: str, first_name: str) -> int:
    """Добавляет сотрудника и возвращает ID.

    Совпадение фамилии и имени допустимо: различение выполняется по ID.
    """
    employee = logic.validate_employee(last_name, first_name)

    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO employees (last_name, first_name) VALUES (?, ?)",
            (employee["last_name"], employee["first_name"]),
        )
        return cursor.lastrowid


def get_employees() -> list:
    """Возвращает сотрудников с их идентификаторами."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT * FROM employees ORDER BY id"
        ).fetchall()

        return [dict(row) for row in rows]


def issue_book(book_id: int, employee_id: int) -> int:
    """Выдаёт доступную книгу сотруднику и возвращает ID выдачи.

    Raises:
        ValueError: Если ID некорректны, записи отсутствуют
            или книга уже выдана.
    """
    book_id = logic.parse_id(str(book_id))
    employee_id = logic.parse_id(str(employee_id))

    with closing(get_connection()) as connection, connection:
        book = connection.execute(
            "SELECT id FROM books WHERE id = ?", (book_id,)
        ).fetchone()

        if book is None:
            raise ValueError("Книга с таким ID не найдена.")

        employee = connection.execute(
            "SELECT id FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()

        if employee is None:
            raise ValueError("Сотрудник с таким ID не найден.")

        issued_at = datetime.now().isoformat(timespec="seconds")

        try:
            cursor = connection.execute(
                """
                INSERT INTO loans (book_id, employee_id, issued_at)
                VALUES (?, ?, ?)
                """,
                (book_id, employee_id, issued_at),
            )
        except sqlite3.IntegrityError as error:
            active = connection.execute(
                """
                SELECT id FROM loans
                WHERE book_id = ? AND returned_at IS NULL
                """,
                (book_id,),
            ).fetchone()

            if active is not None:
                raise ValueError("Эта книга уже находится на руках.") from error

            raise

        return cursor.lastrowid


def return_book(loan_id: int):
    """Оформляет возврат по ID выдачи, сохраняя историю.

    Raises:
        ValueError: Если выдача отсутствует или уже закрыта.
    """
    loan_id = logic.parse_id(str(loan_id))
    returned_at = datetime.now().isoformat(timespec="seconds")

    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            """
            UPDATE loans
            SET returned_at = ?
            WHERE id = ? AND returned_at IS NULL
            """,
            (returned_at, loan_id),
        )

        if cursor.rowcount == 0:
            raise ValueError("Выдача не найдена или книга уже возвращена.")


def get_loans(active_only: bool = False) -> list:
    """Возвращает историю или только книги на руках с данными сотрудников."""
    query = """
        SELECT l.id, l.book_id, l.employee_id,
               b.title, e.last_name, e.first_name,
               l.issued_at, l.returned_at
        FROM loans AS l
        JOIN books AS b ON b.id = l.book_id
        JOIN employees AS e ON e.id = l.employee_id
    """

    if active_only:
        query += " WHERE l.returned_at IS NULL"

    query += " ORDER BY l.id DESC"

    with closing(get_connection()) as connection:
        rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]


def get_statistics() -> dict:
    """Возвращает количества книг, сотрудников, выдач и распределение жанров."""
    with closing(get_connection()) as connection:
        total_books = connection.execute(
            "SELECT COUNT(*) FROM books"
        ).fetchone()[0]

        active_loans = connection.execute(
            "SELECT COUNT(*) FROM loans WHERE returned_at IS NULL"
        ).fetchone()[0]

        total_employees = connection.execute(
            "SELECT COUNT(*) FROM employees"
        ).fetchone()[0]

        total_loans = connection.execute(
            "SELECT COUNT(*) FROM loans"
        ).fetchone()[0]

        genres = connection.execute(
            """
            SELECT genre, COUNT(*) AS amount
            FROM books GROUP BY genre ORDER BY genre
            """
        ).fetchall()

        return {
            "total_books": total_books,
            "available_books": total_books - active_loans,
            "active_loans": active_loans,
            "total_employees": total_employees,
            "total_loans": total_loans,
            "returned_loans": total_loans - active_loans,
            "genres": {row["genre"]: row["amount"] for row in genres},
        }
