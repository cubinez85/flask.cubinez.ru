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
from flask_admin import Admin, AdminIndexView
from flask_login import current_user
from flask import redirect, url_for, request

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
moment = Moment()
babel = Babel()

# Правильный SecureAdminIndexView - наследуется от AdminIndexView
class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'cubinez85'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))

admin = Admin(name='Admin Panel', template_mode='bootstrap4', index_view=SecureAdminIndexView())
ADMINS = ['cubinez85.oleg@yandex.ru', 'postfix@cubinez.ru']
login.login_view = 'auth.login'

def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])

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

    # Elasticsearch configuration
    es_url = app.config.get('ELASTICSEARCH_URL')
    if es_url:
        app.elasticsearch = Elasticsearch(es_url)
    else:
        app.elasticsearch = None

    # Register blueprints

    from app.template_helpers import register_template_helpers
    register_template_helpers(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Logging configuration (only in production)
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/project_flask.log',
                                           maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Project Flask startup')

    return app

from app import models

# Импортируем push функции для доступности во всем приложении
# Эти функции будут доступны после создания приложения
def init_push_functions(app):
    """Инициализирует push функции в контексте приложения"""
    with app.app_context():
        from app.api.push import (
            send_push_notification, 
            notify_new_message, 
            notify_mention, 
            notify_new_follower, 
            notify_new_post
        )
        
        # Делаем функции доступными как атрибуты приложения
        app.send_push_notification = send_push_notification
        app.notify_new_message = notify_new_message
        app.notify_mention = notify_mention
        app.notify_new_follower = notify_new_follower
        app.notify_new_post = notify_new_post
        
        return app

# Альтернативный способ - создаем модуль-прокси для push функций
class PushNotifications:
    """Прокси-класс для доступа к push функциям"""
    
    @staticmethod
    def send_push_notification(user, title, body, url='/'):
        from app.api.push import send_push_notification as _send
        return _send(user, title, body, url)
    
    @staticmethod
    def notify_new_message(recipient, sender, message):
        from app.api.push import notify_new_message as _notify
        return _notify(recipient, sender, message)
    
    @staticmethod
    def notify_mention(user, post):
        from app.api.push import notify_mention as _notify
        return _notify(user, post)
    
    @staticmethod
    def notify_new_follower(user, follower):
        from app.api.push import notify_new_follower as _notify
        return _notify(user, follower)
    
    @staticmethod
    def notify_new_post(user, author, post):
        from app.api.push import notify_new_post as _notify
        return _notify(user, author, post)

# Создаем глобальный экземпляр для удобного доступа
push = PushNotifications()
