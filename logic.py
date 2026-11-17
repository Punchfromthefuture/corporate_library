"""Проверка данных и поиск по каталогу корпоративной библиотеки."""


def clean_text(value: str, field: str) -> str:
    """Возвращает текст без лишних пробелов.

    Raises:
        ValueError: Если значение не является непустой строкой.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Поле «{field}» не должно быть пустым.")

    return " ".join(value.split())


def parse_id(value: str) -> int:
    """Преобразует текст в положительный целочисленный ID.

    Raises:
        ValueError: Если ID не является положительным целым числом.
    """
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValueError("ID должен быть положительным целым числом.") from None

    if result <= 0:
        raise ValueError("ID должен быть положительным целым числом.")

    return result


def validate_book(title: str, author: str, genre: str) -> dict:
    """Проверяет поля книги и возвращает нормализованный словарь."""
    return {
        "title": clean_text(title, "Название"),
        "author": clean_text(author, "Автор"),
        "genre": clean_text(genre, "Жанр").casefold(),
    }


def validate_employee(last_name: str, first_name: str) -> dict:
    """Проверяет фамилию и имя сотрудника."""
    return {
        "last_name": clean_text(last_name, "Фамилия"),
        "first_name": clean_text(first_name, "Имя"),
    }


def search_books(books: list, keyword: str) -> list:
    """Ищет фрагмент текста в названии, авторе или жанре.

    Регистр не учитывается. Исходный список не изменяется.
    Пустой запрос вызывает ValueError.
    """
    keyword = clean_text(keyword, "Поисковый запрос").casefold()

    return [
        book
        for book in books
        if any(
            keyword in book[field].casefold()
            for field in ("title", "author", "genre")
        )
    ]
