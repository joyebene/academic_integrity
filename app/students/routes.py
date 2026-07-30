# app/students/routes.py

from flask import render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Submission, Assignment, Course, AIAnalysis, Report, Notification, SystemLog
from app.forms.student import SubmissionForm
from app.ai_analysis.plagiarism import PlagiarismDetector
from app.ai_analysis.ai_detection import AIContentDetector
from datetime import datetime, timedelta
import os
import json
from werkzeug.utils import secure_filename
from app.students import students_bp



@students_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    student = current_user.student_profile
    
    # Get assignments
    assignments = Assignment.query.filter_by(is_active=True).all()
    pending_assignments = []
    completed_submissions = Submission.query.filter_by(student_id=student.id).all()
    
    for assignment in assignments:
        if assignment.id not in [s.assignment_id for s in completed_submissions]:
            pending_assignments.append(assignment)
    
    # Calculate stats
    stats = {
        'total_submissions': len(completed_submissions),
        'pending_assignments': len(pending_assignments),
        'completed_submissions': len([s for s in completed_submissions if s.status == 'completed']),
        'avg_integrity_score': 87  # Calculate from analysis
    }
    
    # Recent activity
    activities = []
    for sub in completed_submissions[:5]:
        activities.append({
            'type': 'success',
            'icon': 'check-circle',
            'message': f'Assignment "{sub.assignment.title}" analyzed successfully',
            'time_ago': '2 hours ago'
        })
    
    return render_template('students/dashboard.html', 
                         pending_assignments=pending_assignments[:5],
                         stats=stats,
                         activities=activities)


@students_bp.route('/submit/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    student = current_user.student_profile
    
    # Check if already submitted
    existing_submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=student.id
    ).first()
    
    if existing_submission and existing_submission.status == 'completed':
        flash('You have already submitted this assignment.', 'info')
        return redirect(url_for('students.view_submission', id=existing_submission.id))
    
    form = SubmissionForm()
    
    if form.validate_on_submit():
        # Process file upload
        file = form.file.data
        filename = secure_filename(file.filename)
        
        # Create submission folder
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions', str(student.id))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_folder, f"{assignment_id}_{filename}")
        file.save(file_path)
        
        # Create submission record
        submission = Submission(
            assignment_id=assignment_id,
            student_id=student.id,
            file_path=file_path,
            original_filename=filename,
            comments=form.comments.data,
            status='processing'
        )
        db.session.add(submission)
        db.session.commit()
        
        # Start AI analysis
        try:
            # Run plagiarism detection
            detector = PlagiarismDetector()
            text = detector.extract_text_from_file(file_path)
            
            # Get corpus of previous submissions (simplified)
            corpus = []
            previous_submissions = Submission.query.filter(
                Submission.assignment_id == assignment_id,
                Submission.id != submission.id
            ).all()
            
            for prev in previous_submissions:
                try:
                    prev_text = detector.extract_text_from_file(prev.file_path)
                    corpus.append(prev_text)
                except:
                    continue
            
            # Run analysis
            plagiarism_result = detector.detect_plagiarism(text, corpus)
            
            # AI detection
            ai_detector = AIContentDetector()
            ai_result = ai_detector.generate_detailed_analysis(text)
            
            # Save analysis results
            analysis = AIAnalysis(
                submission_id=submission.id,
                plagiarism_score=plagiarism_result['plagiarism_score'],
                ai_generated_score=ai_result['ai_probability_score'],
                analysis_details=json.dumps({
                    'plagiarism': plagiarism_result,
                    'ai_detection': ai_result
                }),
                model_version='1.0'
            )
            db.session.add(analysis)
            
            # Update submission status
            submission.status = 'completed'
            db.session.commit()
            
            # Check if flagged
            if plagiarism_result['plagiarism_score'] > 60 or ai_result['ai_probability_score'] > 60:
                # Create suspicious record
                from app.models import SuspiciousSubmission
                suspicious = SuspiciousSubmission(
                    submission_id=submission.id,
                    reason='High plagiarism or AI detection score',
                    severity='high' if max(plagiarism_result['plagiarism_score'], ai_result['ai_probability_score']) > 70 else 'medium'
                )
                db.session.add(suspicious)
                db.session.commit()
            
            # Create notification for student
            notification = Notification(
                user_id=current_user.id,
                title='Assignment Analysis Complete',
                message=f'Your assignment "{assignment.title}" has been analyzed. Check your dashboard for results.',
                type='success',
                link=f'/students/submission/{submission.id}'
            )
            db.session.add(notification)
            
            # Notify lecturer if flagged
            if assignment.course.lecturer_id:
                lecturer_user = assignment.course.lecturer.user
                if lecturer_user:
                    notification_lecturer = Notification(
                        user_id=lecturer_user.id,
                        title='Suspicious Submission Detected',
                        message=f'Student {current_user.full_name} submitted a suspicious assignment for "{assignment.title}". Please review.',
                        type='warning',
                        link=f'/lecturers/submissions/{submission.id}'
                    )
                    db.session.add(notification_lecturer)
            
            db.session.commit()
            
            flash('Assignment submitted and analyzed successfully!', 'success')
            return redirect(url_for('students.view_submission', id=submission.id))
            
        except Exception as e:
            current_app.logger.error(f"Analysis error: {str(e)}")
            submission.status = 'failed'
            db.session.commit()
            flash(f'Analysis error: {str(e)}', 'danger')
            return redirect(url_for('students.dashboard'))
    
    return render_template('students/submit_assignment.html', 
                         assignment=assignment,
                         form=form)

# app/students/routes.py

@students_bp.route("/my-submissions")
@login_required
def my_submissions():

    if current_user.role != "student":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    student = current_user.student_profile

    submissions = (
        Submission.query
        .filter_by(student_id=student.id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )

    return render_template(
        "students/my_submissions.html",
        submissions=submissions
    )


@students_bp.route('/submission/<int:id>')
@login_required
def view_submission(id):
    submission = Submission.query.get_or_404(id)
    
    if submission.student_id != current_user.student_profile.id and current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('students.dashboard'))
    
    return render_template('students/view_submission.html', submission=submission)


@students_bp.route('/submission/<int:id>/download')
@login_required
def download_submission(id):
    submission = Submission.query.get_or_404(id)
    
    if submission.student_id != current_user.student_profile.id and current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('students.dashboard'))
    
    return send_file(submission.file_path, as_attachment=True, download_name=submission.original_filename)


@students_bp.route("/assignments")
@login_required
def assignments():

    if current_user.role != "student":
        flash("Access denied", "danger")
        return redirect(url_for("auth.login"))

    assignments = Assignment.query.filter_by(is_active=True).all()

    return render_template(
        "students/assignments.html",
        assignments=assignments
    )