"""Проверки валидации и поиска корпоративной библиотеки."""

import pytest

import logic


def test_validate_book():
    """Поля книги очищаются, жанр приводится к нижнему регистру."""
    result = logic.validate_book(
        "  Моя   книга  ",
        "  Иван   Иванов  ",
        "  РОМАН  ",
    )

    assert result == {
        "title": "Моя книга",
        "author": "Иван Иванов",
        "genre": "роман",
    }


@pytest.mark.parametrize("field", ["title", "author", "genre"])
def test_empty_book_fields(field):
    """Пустые поля книги не принимаются."""
    fields = {
        "title": "Книга",
        "author": "Автор",
        "genre": "Роман",
    }
    fields[field] = "   "

    with pytest.raises(ValueError):
        logic.validate_book(**fields)


def test_validate_employee():
    """Фамилия и имя очищаются от лишних пробелов."""
    result = logic.validate_employee("  Иванов  ", "  Иван  ")

    assert result == {
        "last_name": "Иванов",
        "first_name": "Иван",
    }


@pytest.mark.parametrize("field", ["last_name", "first_name"])
def test_empty_employee_fields(field):
    """Пустые фамилия и имя не принимаются."""
    fields = {
        "last_name": "Иванов",
        "first_name": "Иван",
    }
    fields[field] = " "

    with pytest.raises(ValueError):
        logic.validate_employee(**fields)


def test_parse_id():
    """Корректный ID преобразуется в число."""
    assert logic.parse_id("12") == 12


@pytest.mark.parametrize("value", ["0", "-1", "abc", "1.5", "", None])
def test_invalid_id(value):
    """Некорректный ID вызывает ошибку."""
    with pytest.raises(ValueError):
        logic.parse_id(value)


def test_search_books():
    """Поиск работает по названию, автору и жанру без учёта регистра."""
    books = [
        {
            "id": 1,
            "title": "Капитанская дочка",
            "author": "Александр Пушкин",
            "genre": "роман",
        },
        {
            "id": 2,
            "title": "Мцыри",
            "author": "Михаил Лермонтов",
            "genre": "поэма",
        },
    ]

    assert logic.search_books(books, "ДОЧКА") == [books[0]]
    assert logic.search_books(books, "пушкин") == [books[0]]
    assert logic.search_books(books, "ПОЭМА") == [books[1]]
    assert logic.search_books(books, "несуществующая книга") == []
    assert len(books) == 2


def test_empty_search():
    """Пустой поисковый запрос не принимается."""
    with pytest.raises(ValueError):
        logic.search_books([], "   ")
