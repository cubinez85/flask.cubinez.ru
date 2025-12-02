from flask import url_for
from flask import render_template, current_app
from flask_babel import _
from app.email import send_email

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    reset_link = url_for('auth.reset_password', token=token, _external=True)
    send_email(_('[project_flask] Reset Your Password'),
               sender=current_app.config['ADMINS'][1],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))
