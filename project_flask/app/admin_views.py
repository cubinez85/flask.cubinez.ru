from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, request

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == 'cubinez85'

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))
