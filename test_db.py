"""Проверки базы данных корпоративной библиотеки."""

import pytest

import db


@pytest.fixture
def database(tmp_path, monkeypatch):
    """Каждый тест использует новую отдельную временную базу."""
    test_path = tmp_path / "test_library.db"
    monkeypatch.setattr(db, "DB_PATH", test_path)
    db.init_db()
    return db


def test_empty_database(database):
    """Новая база не содержит записей."""
    assert database.get_books() == []
    assert database.get_employees() == []
    assert database.get_loans() == []

    assert database.get_statistics() == {
        "total_books": 0,
        "available_books": 0,
        "active_loans": 0,
        "total_employees": 0,
        "total_loans": 0,
        "returned_loans": 0,
        "genres": {},
    }


def test_add_book(database):
    """Книга сохраняется и получает ID."""
    book_id = database.add_book("  Книга  ", "  Автор  ", "РОМАН")

    assert book_id > 0
    assert database.get_books() == [
        {
            "id": book_id,
            "title": "Книга",
            "author": "Автор",
            "genre": "роман",
            "availability": "доступна",
        }
    ]


def test_add_employee(database):
    """Сотрудник сохраняется и получает ID."""
    employee_id = database.add_employee(" Иванов ", " Иван ")

    assert employee_id > 0
    assert database.get_employees() == [
        {
            "id": employee_id,
            "last_name": "Иванов",
            "first_name": "Иван",
        }
    ]


def test_issue_book(database):
    """Выдача связывает книгу с сотрудником."""
    book_id = database.add_book("Книга", "Автор", "Роман")
    employee_id = database.add_employee("Иванов", "Иван")

    loan_id = database.issue_book(book_id, employee_id)

    loans = database.get_loans(active_only=True)

    assert len(loans) == 1
    assert loans[0]["id"] == loan_id
    assert loans[0]["book_id"] == book_id
    assert loans[0]["employee_id"] == employee_id
    assert loans[0]["last_name"] == "Иванов"
    assert loans[0]["first_name"] == "Иван"
    assert loans[0]["issued_at"]
    assert loans[0]["returned_at"] is None
    assert database.get_books()[0]["availability"] == "выдана"


def test_duplicate_issue(database):
    """Выданную книгу нельзя выдать повторно."""
    book_id = database.add_book("Книга", "Автор", "Роман")
    first_employee = database.add_employee("Иванов", "Иван")
    second_employee = database.add_employee("Петров", "Пётр")

    database.issue_book(book_id, first_employee)

    with pytest.raises(ValueError):
        database.issue_book(book_id, second_employee)

    assert len(database.get_loans()) == 1


def test_missing_book(database):
    """Нельзя выдать несуществующую книгу."""
    employee_id = database.add_employee("Иванов", "Иван")

    with pytest.raises(ValueError):
        database.issue_book(999, employee_id)

    assert database.get_loans() == []


def test_missing_employee(database):
    """Нельзя выдать книгу несуществующему сотруднику."""
    book_id = database.add_book("Книга", "Автор", "Роман")

    with pytest.raises(ValueError):
        database.issue_book(book_id, 999)

    assert database.get_loans() == []


def test_return_and_reissue(database):
    """Возврат сохраняет историю и позволяет новую выдачу."""
    book_id = database.add_book("Книга", "Автор", "Роман")
    first_employee = database.add_employee("Иванов", "Иван")
    second_employee = database.add_employee("Петров", "Пётр")

    first_loan = database.issue_book(book_id, first_employee)
    database.return_book(first_loan)

    assert database.get_loans(active_only=True) == []
    assert database.get_books()[0]["availability"] == "доступна"

    history = database.get_loans()
    assert len(history) == 1
    assert history[0]["id"] == first_loan
    assert history[0]["returned_at"] is not None

    second_loan = database.issue_book(book_id, second_employee)

    assert second_loan != first_loan
    assert len(database.get_loans()) == 2

    active = database.get_loans(active_only=True)
    assert len(active) == 1
    assert active[0]["employee_id"] == second_employee


def test_duplicate_return(database):
    """Повторный возврат вызывает ошибку."""
    book_id = database.add_book("Книга", "Автор", "Роман")
    employee_id = database.add_employee("Иванов", "Иван")
    loan_id = database.issue_book(book_id, employee_id)

    database.return_book(loan_id)

    with pytest.raises(ValueError):
        database.return_book(loan_id)


def test_missing_return(database):
    """Нельзя вернуть несуществующую выдачу."""
    with pytest.raises(ValueError):
        database.return_book(999)


def test_statistics(database):
    """Статистика учитывает книги, сотрудников, выдачи и возвраты."""
    first_book = database.add_book("Первая книга", "Автор", "Роман")
    second_book = database.add_book("Вторая книга", "Автор", "Поэма")
    employee_id = database.add_employee("Иванов", "Иван")

    first_loan = database.issue_book(first_book, employee_id)
    database.return_book(first_loan)
    database.issue_book(second_book, employee_id)

    assert database.get_statistics() == {
        "total_books": 2,
        "available_books": 1,
        "active_loans": 1,
        "total_employees": 1,
        "total_loans": 2,
        "returned_loans": 1,
        "genres": {
            "роман": 1,
            "поэма": 1,
        },
    }


def test_init_preserves_data(database):
    """Повторная инициализация не удаляет записи."""
    book_id = database.add_book("Книга", "Автор", "Роман")

    database.init_db()

    books = database.get_books()
    assert len(books) == 1
    assert books[0]["id"] == book_id


def test_invalid_book_not_saved(database):
    """Книга с пустым названием не сохраняется."""
    with pytest.raises(ValueError):
        database.add_book(" ", "Автор", "Роман")

    assert database.get_books() == []


def test_sql_text_is_data(database):
    """SQL-подобное название сохраняется как обычный текст."""
    title = "Книга'); DROP TABLE books; --"

    book_id = database.add_book(title, "Автор", "Роман")
    books = database.get_books()

    assert len(books) == 1
    assert books[0]["id"] == book_id
    assert books[0]["title"] == title

    database.add_book("Другая книга", "Автор", "Роман")
    assert len(database.get_books()) == 2
