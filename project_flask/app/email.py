from threading import Thread
from flask import current_app
from flask_mail import Message
from app import mail


def send_async_email(app, msg):
    print(f"Entering send_async_email. App: {app}")
    with app.app_context():
        print("App Context active")
        mail.send(msg)
    print("Exiting send_async_email")


def send_email(subject, sender, recipients, text_body, html_body):
    app = current_app._get_current_object()
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email,
           args=(app, msg)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    with current_app.app_context():
        send_email(_('[project_flask] Reset Your Password'),
                   sender=current_app.config['ADMINS'][1],
                   recipients=[user.email],
                   text_body=render_template('email/reset_password.txt',
                                             user=user, token=token),
                   html_body=render_template('email/reset_password.html',
                                             user=user, token=token))
