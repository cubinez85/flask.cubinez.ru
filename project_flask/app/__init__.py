import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from config import Config
from flask_bcrypt import Bcrypt
from elasticsearch import Elasticsearch
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
moment = Moment()
babel = Babel()
admin = Admin(name='Admin Panel', template_mode='bootstrap4')
ADMINS = ['cubinez65@yandex.ru', 'postfix@cubinez.ru']
login.login_view = 'auth.login'

def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])
#    return 'en'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    admin.init_app(app)

    es_url = os.getenv('ELASTICSEARCH_URL')

    es_ca_certs = os.getenv('ELASTICSEARCH_CA_CERTS')

    es_username = os.getenv('ELASTICSEARCH_USERNAME')

    es_password = os.getenv('ELASTICSEARCH_PASSWORD')

    es = Elasticsearch(es_url, ca_certs=es_ca_certs, basic_auth=(es_username, es_password))

    app.elasticsearch = Elasticsearch(es_url, ca_certs=es_ca_certs, basic_auth=(es_username, es_password)) if es_url else None


    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.cli import bp as cli_bp
    app.register_blueprint(cli_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    if not app.debug:
        import logging
        from logging.handlers import SMTPHandler
        mail_handler = SMTPHandler('127.0.0.1',
                               'postfix@cubinez.ru',
                               ADMINS, 'YourApplication Failed')
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
               os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/project_flask.log', maxBytes=10240,
                                       backupCount=10)
        file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('project_flask startup')

        return app


from app import models


