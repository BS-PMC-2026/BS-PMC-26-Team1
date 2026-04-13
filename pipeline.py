from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models import db, ProgressRecord

pipeline_bp = Blueprint('pipeline', __name__)

@pipeline_bp.route('/pipeline')
def pipeline():
    user_id = session.get('user_id')
    if not user_id:
        flash('Session missing. Please login to continue.', 'error')
        return redirect(url_for('auth.login'))

    record = ProgressRecord.query.filter_by(user_id=user_id).first()
    if not record:
        record = ProgressRecord(user_id=user_id)
        db.session.add(record)
    record.pipeline_viewed = True
    db.session.commit()
        
    return render_template('pipeline.html')
