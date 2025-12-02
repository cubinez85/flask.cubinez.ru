import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

class Config(object):
    SECRET_KEY = os.getenv('SECRET_KEY')

    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

    ADMINS = ['cubinez85.oleg@yandex.ru', 'postfix@cubinez.ru', 'cubinez85@cubinez.ru', 'cubinez85@mail.ru', 'cubinez85@gmail.com']

    POSTS_PER_PAGE = 3

    LANGUAGES = ['en', 'ru']

    es_url = os.getenv('ELASTICSEARCH_URL')
    es_ca_certs = os.getenv('ELASTICSEARCH_CA_CERTS')
    es_username = os.getenv('ELASTICSEARCH_USERNAME')
    es_password = os.getenv('ELASTICSEARCH_PASSWORD')

    es = Elasticsearch(es_url, ca_certs=es_ca_certs, basic_auth=(es_username, es_password))

    # VAPID Keys for Push Notifications
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
    VAPID_CLAIMS = {
        "sub": "mailto:admin@flask.cubinez.ru"
    }

    # Email configuration с умной обработкой
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_PORT') or 25)

    # Определяем, это локальный Postfix или внешний SMTP
    is_local_postfix = MAIL_SERVER in ['localhost', '127.0.0.1'] and MAIL_PORT == 25
    if is_local_postfix:
        # Для локального Postfix не нужны TLS и аутентификация
        MAIL_USE_TLS = False
        MAIL_USE_SSL = False
        MAIL_USERNAME = None  # Важно: None, а не пустая строка
        MAIL_PASSWORD = None
        print("✅ Конфигурация для локального Postfix (без аутентификации)")
    else:
        # Для внешнего SMTP
        MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes']
        MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() in ['true', '1', 'yes']
        MAIL_USERNAME = os.getenv('MAIL_USERNAME') or None
        MAIL_PASSWORD = os.getenv('MAIL_PASSWORD') or None

    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'postfix@cubinez.ru')
    MAIL_DEBUG = False

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
