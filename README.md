# flask.cubinez.ru
file .env for example:
SECRET_KEY=*********

SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://cubinez85:123@localhost/testdb'

ELASTICSEARCH_URL=https://localhost:9200
ELASTICSEARCH_CA_CERTS=./http_ca.crt
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=*********

secret.py:
import secrets

secret_key = secrets.token_hex(32)  # Генерирует 64-символьный шестнадцатеричный ключ
print(secret_key)
