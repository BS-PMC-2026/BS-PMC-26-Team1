from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')

@main_bp.route('/start')
def start():
    if session.get('user_id'):
        return redirect(url_for('intro.intro'))
    else:
        return redirect(url_for('auth.login'))
