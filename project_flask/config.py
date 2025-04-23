import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch


load_dotenv()
#load_dotenv(dotenv_path='/var/www/project_flask/.env')


class Config(object):

    SECRET_KEY = os.getenv('SECRET_KEY')

    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

    ADMINS = ['cubinez65@yandex.ru', 'postfix@cubinez.ru', 'cubinez85@mail.ru', 'cubinez85@gmail.com']

    POSTS_PER_PAGE = 3

    LANGUAGES = ['en', 'ru']

    es_url = os.getenv('ELASTICSEARCH_URL')

    es_ca_certs = os.getenv('ELASTICSEARCH_CA_CERTS')

    es_username = os.getenv('ELASTICSEARCH_USERNAME')

    es_password = os.getenv('ELASTICSEARCH_PASSWORD')

    es = Elasticsearch(es_url, ca_certs=es_ca_certs, basic_auth=(es_username, es_password))


