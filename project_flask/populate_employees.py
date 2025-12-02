from app import create_app, db
from app.models import Employee

app = create_app()

with app.app_context():
    # Очистка существующих данных (опционально)
    # Employee.query.delete()
    
    # Проверяем, есть ли уже данные
    if Employee.query.count() == 0:
        # Добавление сотрудников
        employees = [
            {'id': 1, 'parent': None, 'name': 'Петя', 'position': 'директор'},
            {'id': 2, 'parent': 1, 'name': 'Жора', 'position': 'бухгалтер'},
            {'id': 3, 'parent': 1, 'name': 'Толик', 'position': 'отдел продаж'},
            {'id': 4, 'parent': 2, 'name': 'Ира', 'position': 'admin'},
            {'id': 5, 'parent': 3, 'name': 'Коля', 'position': 'водитель'},
        ]
        
        for emp_data in employees:
            employee = Employee(**emp_data)
            db.session.add(employee)
        
        db.session.commit()
        print("База данных сотрудников заполнена!")
    else:
        print("Данные сотрудников уже существуют в базе")
