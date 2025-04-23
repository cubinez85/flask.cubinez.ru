from app import create_app, db
from app.models import User, Post, Tree
import sqlalchemy as sa
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy import delete

app = create_app()

app.app_context().push()

stmt = delete(User).where(User.username == 'cubinez85')

#stmt = update(User).where(User.id == 5).values(email='tester@gmail.com')

db.session.execute(stmt)

db.session.commit()
