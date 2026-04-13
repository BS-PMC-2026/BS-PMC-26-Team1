from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models import db, ProgressRecord

intro_bp = Blueprint('intro', __name__)

@intro_bp.route('/intro')
def intro():
    user_id = session.get('user_id')
    if not user_id:
        flash('Session missing. Please login to continue.', 'error')
        return redirect(url_for('auth.login'))

    record = ProgressRecord.query.filter_by(user_id=user_id).first()
    if not record:
        record = ProgressRecord(user_id=user_id)
        db.session.add(record)
    record.intro_completed = True
    db.session.commit()
        
    return render_template('intro.html')
