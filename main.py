"""Консольный интерфейс прототипа корпоративной библиотеки."""

import sqlite3

import db
import logic


def show_books(books: list):
    """Выводит каталог с ID и доступностью экземпляров."""
    if not books:
        print("Книги не найдены.")
        return

    for book in books:
        print(
            f"ID книги: {book['id']} | {book['title']} | "
            f"{book['author']} | {book['genre']} | "
            f"{book['availability']}"
        )


def add_book():
    """Запрашивает поля и добавляет экземпляр книги."""
    title = input("Название: ")
    author = input("Автор: ")
    genre = input("Жанр: ")

    book_id = db.add_book(title, author, genre)
    print(f"Книга добавлена. ID книги: {book_id}")


def find_books():
    """Выполняет поиск по названию, автору или жанру."""
    keyword = input("Введите текст для поиска: ")
    books = logic.search_books(db.get_books(), keyword)
    show_books(books)


def add_employee():
    """Регистрирует сотрудника по фамилии и имени."""
    last_name = input("Фамилия: ")
    first_name = input("Имя: ")

    employee_id = db.add_employee(last_name, first_name)
    print(f"Сотрудник добавлен. ID сотрудника: {employee_id}")


def show_employees():
    """Показывает зарегистрированных сотрудников."""
    employees = db.get_employees()

    if not employees:
        print("Сотрудники не найдены.")
        return

    for employee in employees:
        print(
            f"ID сотрудника: {employee['id']} | "
            f"{employee['last_name']} {employee['first_name']}"
        )


def issue_book():
    """Запрашивает ID книги и сотрудника, оформляет выдачу."""
    book_id = logic.parse_id(input("ID книги: "))
    employee_id = logic.parse_id(input("ID сотрудника: "))

    loan_id = db.issue_book(book_id, employee_id)
    print(f"Книга выдана. ID выдачи: {loan_id}")


def return_book():
    """Закрывает выдачу по её ID."""
    loan_id = logic.parse_id(input("ID выдачи для возврата: "))
    db.return_book(loan_id)

    print("Возврат оформлен. Книга снова доступна.")


def show_loans(active_only: bool = False):
    """Выводит историю выдач или список книг на руках."""
    loans = db.get_loans(active_only)

    if not loans:
        print("Записи не найдены.")
        return

    for loan in loans:
        state = "возвращена" if loan["returned_at"] else "на руках"
        returned_at = loan["returned_at"] or "—"

        print(
            f"\nID выдачи: {loan['id']} | ID книги: {loan['book_id']}"
            f"\nКнига: {loan['title']}"
            f"\nСотрудник: {loan['last_name']} {loan['first_name']} "
            f"(ID: {loan['employee_id']})"
            f"\nВыдана: {loan['issued_at']}"
            f"\nВозвращена: {returned_at}"
            f"\nСостояние: {state}"
        )


def show_statistics():
    """Показывает текущую статистику библиотеки."""
    statistics = db.get_statistics()

    print(f"Всего экземпляров: {statistics['total_books']}")
    print(f"Доступно экземпляров: {statistics['available_books']}")
    print(f"На руках: {statistics['active_loans']}")
    print(f"Сотрудников: {statistics['total_employees']}")
    print(f"Всего выдач: {statistics['total_loans']}")
    print(f"Завершённых возвратов: {statistics['returned_loans']}")
    print("Книги по жанрам:")

    if not statistics["genres"]:
        print("Нет данных.")

    for genre, amount in statistics["genres"].items():
        print(f"  {genre}: {amount}")


def main():
    """Инициализирует базу и обрабатывает команды меню."""
    try:
        db.init_db()
    except sqlite3.Error as error:
        print(f"Не удалось подготовить базу: {error}")
        return

    actions = {
        "1": add_book,
        "2": lambda: show_books(db.get_books()),
        "3": find_books,
        "4": add_employee,
        "5": show_employees,
        "6": issue_book,
        "7": return_book,
        "8": lambda: show_loans(active_only=True),
        "9": show_loans,
        "10": show_statistics,
    }

    while True:
        print("\n=== Корпоративная библиотека ===")
        print("Учебный прототип для ООО «Е-ЛАЙТ-ТЕЛЕКОМ»")
        print("1. Добавить книгу")
        print("2. Показать книги")
        print("3. Найти книгу")
        print("4. Добавить сотрудника")
        print("5. Показать сотрудников")
        print("6. Выдать книгу")
        print("7. Оформить возврат")
        print("8. Книги на руках")
        print("9. История выдач и возвратов")
        print("10. Статистика")
        print("0. Выход")

        choice = input("Выберите действие: ").strip()

        if choice == "0":
            print("До свидания!")
            return

        action = actions.get(choice)

        if action is None:
            print("Неизвестный пункт меню.")
            continue

        try:
            action()
        except ValueError as error:
            print(f"Ошибка ввода: {error}")
        except sqlite3.Error as error:
            print(f"Ошибка базы данных: {error}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nРабота завершена.")
