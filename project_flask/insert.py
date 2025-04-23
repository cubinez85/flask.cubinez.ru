from app import create_app, db
from app.models import User, Post, Tree
import sqlalchemy as sa
from sqlalchemy import insert
from sqlalchemy import update

app = create_app()

app.app_context().push()

db.session.execute(
    insert(Tree),
    [
        {'id': 1, 'parent': None, 'name': 'Петя', 'position': 'директор'},
        {'parent': 1, 'name': 'Жора', 'position': 'бухгалтер'},
        {'parent': 1, 'name': 'Толик', 'position': 'отдел продаж'},
        {'parent': 2, 'name': 'Ира', 'position': 'admin'},
        {'parent': 3, 'name': 'Коля', 'position': 'водитель'},




    ],
)

db.session.commit()
