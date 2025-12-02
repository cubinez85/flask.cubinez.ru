from threading import Thread
from datetime import datetime
from flask import current_app, render_template
from flask_mail import Message
from app import mail
import logging


def send_async_email(app, msg, logger_name='flask.app'):
    """Асинхронная отправка email"""
    try:
        with app.app_context():
            mail.send(msg)
        
        # Логируем успех
        logger = logging.getLogger(logger_name)
        logger.info(f"Email sent successfully: {msg.subject}")
        
    except Exception as e:
        # Логируем ошибку
        logger = logging.getLogger(logger_name)
        logger.error(f"Failed to send email: {str(e)}")
        print(f"Email sending failed: {str(e)}")


def send_email(subject, sender, recipients, text_body, html_body, 
               reply_to=None, cc=None, bcc=None, attachments=None):
    """
    Основная функция отправки email
    """
    app = current_app._get_current_object()
    
    # Получаем имя логгера
    logger_name = current_app.logger.name
    
    msg = Message(
        subject=subject,
        sender=sender,
        recipients=recipients,
        reply_to=reply_to,
        cc=cc,
        bcc=bcc
    )
    
    msg.body = text_body
    msg.html = html_body
    
    # Добавляем вложения
    if attachments:
        for filename, content_type, data in attachments:
            msg.attach(filename, content_type, data)
    
    # Логируем отправку
    safe_log = {
        'subject': subject,
        'sender': sender,
        'recipients_count': len(recipients),
        'has_attachments': bool(attachments)
    }
    current_app.logger.info(f"Sending email: {safe_log}")
    
    # Запускаем в отдельном потоке
    Thread(target=send_async_email, args=(app, msg, logger_name), daemon=True).start()


def send_password_reset_email(user):
    """Отправка email для сброса пароля"""
    token = user.get_reset_password_token()
    
    # Используем ленивый импорт для перевода
    try:
        from flask_babel import _
        subject = _('[project_flask] Reset Your Password')
    except ImportError:
        subject = '[project_flask] Reset Your Password'
    
    send_email(
        subject=subject,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER', current_app.config['ADMINS'][1]),
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )


def send_error_notification(error_message, context=None, request=None):
    """Отправка уведомления об ошибке администраторам"""
    if context is None:
        context = {}
    
    import traceback
    
    error_details = {
        'error': str(error_message),
        'traceback': traceback.format_exc(),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'context': context,
        'url': request.url if request else 'N/A',
        'method': request.method if request else 'N/A',
        'ip': request.remote_addr if request else 'N/A'
    }
    
    app_name = current_app.config.get('APP_NAME', 'Flask App')
    subject = f"🚨 Ошибка в проекте {app_name}"
    
    text_body = f"""
    Произошла ошибка в приложении:
    
    Ошибка: {error_details['error']}
    Время: {error_details['time']}
    URL: {error_details['url']}
    Метод: {error_details['method']}
    IP: {error_details['ip']}
    
    Контекст: {error_details['context']}
    
    Traceback:
    {error_details['traceback']}
    """
    
    html_body = render_template('email/error_notification.html', 
                               error_details=error_details)
    
    send_email(
        subject=subject,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@cubinez.ru'),
        recipients=current_app.config['ADMINS'],
        text_body=text_body,
        html_body=html_body
    )


def send_test_email(recipient=None):
    """Отправка тестового email"""
    if not recipient:
        recipient = current_app.config['ADMINS'][0] if current_app.config.get('ADMINS') else 'test@example.com'
    
    mail_config = current_app.config
    
    subject = "✅ Test Email - Конфигурация почты работает"
    
    text_body = f"""
    Тестовое письмо из Flask приложения.
    
    Конфигурация:
    - Сервер: {mail_config.get('MAIL_SERVER')}
    - Порт: {mail_config.get('MAIL_PORT')}
    - TLS: {mail_config.get('MAIL_USE_TLS')}
    - Отправитель: {mail_config.get('MAIL_DEFAULT_SENDER')}
    
    Если вы получили это письмо, почтовая конфигурация работает корректно.
    Время отправки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    html_body = f"""
    <h1>✅ Тестовое письмо</h1>
    <p>Это тестовое письмо из вашего Flask приложения.</p>
    
    <h2>Конфигурация:</h2>
    <ul>
        <li><strong>Сервер:</strong> {mail_config.get('MAIL_SERVER')}</li>
        <li><strong>Порт:</strong> {mail_config.get('MAIL_PORT')}</li>
        <li><strong>TLS:</strong> {mail_config.get('MAIL_USE_TLS')}</li>
        <li><strong>Отправитель:</strong> {mail_config.get('MAIL_DEFAULT_SENDER')}</li>
    </ul>
    
    <p>Если вы получили это письмо, почтовая конфигурация работает корректно.</p>
    <p><em>Время отправки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    """
    
    send_email(
        subject=subject,
        sender=mail_config.get('MAIL_DEFAULT_SENDER', 'noreply@cubinez.ru'),
        recipients=[recipient],
        text_body=text_body,
        html_body=html_body
    )
