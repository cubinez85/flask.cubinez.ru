from flask import Flask
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Конфигурация приложения Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://cubinez85:123@localhost/testdb'
app.config['MAIL_SERVER'] = 'cubinez.ru'  # Замените на ваш SMTP-сервер
app.config['MAIL_PORT'] = 25  # Замените на порт
app.config['MAIL_USE_TLS'] = True  # Или MAIL_USE_SSL
app.config['MAIL_USERNAME'] = 'postfix@cubinez.ru'  # Замените на ваш адрес
app.config['MAIL_PASSWORD'] = '59BTzyV9ENW7NT3'  # Замените на ваш пароль
app.config['MAIL_DEFAULT_SENDER'] = 'postfix@cubinez.ru' # Укажите отправителя по умолчанию

db = SQLAlchemy(app)
mail = Mail(app)

with app.app_context():
    msg = Message('test subject',
                  recipients=['cubinez65@yandex.ru', 'cubinez85@mail.ru', 'cubinez85@gmail.com'])
    msg.body = 'text body'
    msg.html = '<h1>Hello from Flask!</h1>'
    mail.send(msg)

if __name__ == '__main__':
    with app.app_context(): # Не запускать сервер Flask, только отправить письмо
        pass
