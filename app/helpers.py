from functools import wraps
from flask import redirect, url_for, flash, request, session
from .models import User


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        return view(*args, **kwargs)

    return wrapped_view


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


def get_required_string(field_name):
    return request.form.get(field_name, '').strip()


def get_optional_string(field_name):
    return request.form.get(field_name, '').strip() or None


def get_optional_int(field_name):
    raw_value = request.form.get(field_name, '').strip()
    if raw_value == '':
        return None
    try:
        value = int(raw_value)
        return value if value >= 0 else None
    except ValueError:
        return None
