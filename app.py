import io
import os
import csv
import json
import uuid
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file, Response
import qrcode
from qrcode.image.pil import PilImage
from database import get_db_connection, init_db

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'online_attendance_secret_key_savita'

# Ensure database is initialized
init_db()

# ----------------- Helper Functions ----------------- #

def calculate_student_stats(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get student info
    cursor.execute('SELECT * FROM users WHERE user_id = ? AND role = "student"', (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return None

    # Get all courses enrolled
    cursor.execute('''
        SELECT c.id, c.code, c.name, u.name as teacher_name
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        JOIN users u ON c.teacher_id = u.user_id
        WHERE e.student_id = ?
        ORDER BY c.code
    ''', (student_id,))
    courses = cursor.fetchall()

    course_stats = []
    total_conducted_all = 0
    total_attended_all = 0

    for c in courses:
        course_id = c['id']
        # Total sessions conducted for this course
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE course_id = ?', (course_id,))
        total_sessions = cursor.fetchone()[0]

        # Sessions attended (present or late)
        cursor.execute('''
            SELECT COUNT(*) FROM attendance 
            WHERE student_id = ? AND course_id = ? AND status IN ('present', 'late')
        ''', (student_id, course_id))
        attended = cursor.fetchone()[0]

        total_conducted_all += total_sessions
        total_attended_all += attended

        pct = round((attended / total_sessions * 100), 1) if total_sessions > 0 else 0.0

        # Classes needed to reach 75% if below
        needed_for_75 = 0
        if total_sessions > 0 and pct < 75.0:
            # attended + x / (total + x) >= 0.75
            # attended + x >= 0.75*total + 0.75*x => 0.25*x >= 0.75*total - attended => x >= 3*total - 4*attended
            needed_for_75 = max(0, int(3 * total_sessions - 4 * attended))

        course_stats.append({
            'course_id': course_id,
            'code': c['code'],
            'name': c['name'],
            'teacher_name': c['teacher_name'],
            'total_sessions': total_sessions,
            'attended': attended,
            'absent': total_sessions - attended,
            'percentage': pct,
            'is_low': pct < 75.0 if total_sessions > 0 else False,
            'needed_for_75': needed_for_75
        })

    overall_pct = round((total_attended_all / total_conducted_all * 100), 1) if total_conducted_all > 0 else 0.0

    # Recent attendance records
    cursor.execute('''
        SELECT a.id, a.timestamp, a.status, a.method, c.code as course_code, c.name as course_name, s.title as session_title
        FROM attendance a
        JOIN courses c ON a.course_id = c.id
        JOIN sessions s ON a.session_id = s.id
        WHERE a.student_id = ?
        ORDER BY a.timestamp DESC
        LIMIT 15
    ''', (student_id,))
    recent_records = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        'student': dict(student),
        'overall': {
            'total_conducted': total_conducted_all,
            'total_attended': total_attended_all,
            'total_absent': total_conducted_all - total_attended_all,
            'percentage': overall_pct,
            'status': 'Eligible' if overall_pct >= 75.0 else 'Low Attendance Warning',
            'is_low': overall_pct < 75.0 if total_conducted_all > 0 else False
        },
        'courses': course_stats,
        'recent_records': recent_records
    }

# ----------------- Web UI Route ----------------- #

@app.route('/')
def index():
    return render_template('index.html')

# ----------------- API Routes ----------------- #

@app.route('/api/users')
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, name, email, role, department FROM users ORDER BY role DESC, user_id')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/api/courses')
def get_courses():
    teacher_id = request.args.get('teacher_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    if teacher_id:
        cursor.execute('''
            SELECT c.*, u.name as teacher_name 
            FROM courses c
            JOIN users u ON c.teacher_id = u.user_id
            WHERE c.teacher_id = ?
            ORDER BY c.code
        ''', (teacher_id,))
    else:
        cursor.execute('''
            SELECT c.*, u.name as teacher_name 
            FROM courses c
            JOIN users u ON c.teacher_id = u.user_id
            ORDER BY c.code
        ''')
    courses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(courses)

@app.route('/api/students')
def get_students():
    course_id = request.args.get('course_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    if course_id:
        cursor.execute('''
            SELECT u.user_id, u.name, u.email, u.department, u.created_at
            FROM users u
            JOIN enrollments e ON u.user_id = e.student_id
            WHERE e.course_id = ? AND u.role = 'student'
            ORDER BY u.user_id
        ''', (course_id,))
    else:
        cursor.execute('''
            SELECT u.user_id, u.name, u.email, u.department, u.created_at,
                   (SELECT GROUP_CONCAT(c.code, ', ') 
                    FROM enrollments e 
                    JOIN courses c ON e.course_id = c.id 
                    WHERE e.student_id = u.user_id) as enrolled_courses_str
            FROM users u
            WHERE u.role = 'student'
            ORDER BY u.user_id
        ''')
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(students)

@app.route('/api/students/add', methods=['POST'])
def add_student():
    data = request.json or {}
    user_id = data.get('user_id', '').strip().upper()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    department = data.get('department', '').strip()
    course_ids = data.get('course_ids', [])

    if not user_id or not name or not email or not department:
        return jsonify({'success': False, 'message': 'All fields (Roll Number, Name, Email, Department) are required.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user_id or email already exists
    cursor.execute('SELECT user_id, email FROM users WHERE user_id = ? OR email = ?', (user_id, email))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        if existing['user_id'] == user_id:
            return jsonify({'success': False, 'message': f'Student with Roll Number "{user_id}" already exists.'}), 400
        else:
            return jsonify({'success': False, 'message': f'Student with Email "{email}" already exists.'}), 400

    try:
        # Insert student into users table
        cursor.execute('''
            INSERT INTO users (user_id, name, email, role, department)
            VALUES (?, ?, ?, 'student', ?)
        ''', (user_id, name, email, department))

        # Enroll student in selected courses
        # If no course selected, default to all courses
        if not course_ids:
            cursor.execute('SELECT id FROM courses')
            course_ids = [row['id'] for row in cursor.fetchall()]

        for cid in course_ids:
            cursor.execute('''
                INSERT OR IGNORE INTO enrollments (student_id, course_id)
                VALUES (?, ?)
            ''', (user_id, int(cid)))

        # Also register student in any active sessions for those courses
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for cid in course_ids:
            cursor.execute('SELECT id FROM sessions WHERE course_id = ? AND is_active = 1', (int(cid),))
            active_sessions = cursor.fetchall()
            for s in active_sessions:
                cursor.execute('''
                    INSERT OR IGNORE INTO attendance (session_id, student_id, course_id, timestamp, status, method)
                    VALUES (?, ?, ?, ?, 'absent', 'manual')
                ''', (s['id'], user_id, int(cid), now_str))

        conn.commit()

        # Fetch created student with courses
        cursor.execute('''
            SELECT u.user_id, u.name, u.email, u.department,
                   (SELECT GROUP_CONCAT(c.code, ', ') 
                    FROM enrollments e 
                    JOIN courses c ON e.course_id = c.id 
                    WHERE e.student_id = u.user_id) as enrolled_courses_str
            FROM users u
            WHERE u.user_id = ?
        ''', (user_id,))
        new_student = dict(cursor.fetchone())
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Student {name} ({user_id}) registered successfully!',
            'student': new_student
        })

    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ? AND role = "student"', (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'success': False, 'message': 'Student not found'}), 404

    try:
        cursor.execute('DELETE FROM attendance WHERE student_id = ?', (student_id,))
        cursor.execute('DELETE FROM enrollments WHERE student_id = ?', (student_id,))
        cursor.execute('DELETE FROM users WHERE user_id = ?', (student_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Student {student["name"]} ({student_id}) removed successfully.'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

# ----------------- Student Attendance Stats API ----------------- #

@app.route('/api/student/<student_id>/stats')
def student_stats(student_id):
    stats = calculate_student_stats(student_id)
    if not stats:
        return jsonify({'error': 'Student not found'}), 404
    return jsonify(stats)

# ----------------- Session Management & QR API ----------------- #

@app.route('/api/sessions/create', methods=['POST'])
def create_session():
    data = request.json or {}
    course_id = data.get('course_id')
    title = data.get('title', 'Lecture Session')
    duration_minutes = int(data.get('duration_minutes', 30))

    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify course exists
    cursor.execute('SELECT code, name FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    if not course:
        conn.close()
        return jsonify({'error': 'Course not found'}), 404

    # Generate readable session code and unique QR token
    code_suffix = random.randint(1000, 9999)
    session_code = f"{course['code']}-{code_suffix}"
    qr_token = f"QR_{course['code']}_{uuid.uuid4().hex[:12].upper()}"

    now = datetime.now()
    expires_at = now + timedelta(minutes=duration_minutes)

    cursor.execute('''
        INSERT INTO sessions (course_id, session_code, qr_token, title, created_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (course_id, session_code, qr_token, title, now.strftime('%Y-%m-%d %H:%M:%S'), expires_at.strftime('%Y-%m-%d %H:%M:%S')))
    session_id = cursor.lastrowid
    conn.commit()

    cursor.execute('SELECT s.*, c.code as course_code, c.name as course_name FROM sessions s JOIN courses c ON s.course_id = c.id WHERE s.id = ?', (session_id,))
    new_session = dict(cursor.fetchone())
    conn.close()

    # Pre-populate absent records for all enrolled students
    # When student scans, status changes to 'present'
    conn = get_db_connection()
    c2 = conn.cursor()
    c2.execute('SELECT student_id FROM enrollments WHERE course_id = ?', (course_id,))
    enrolled = c2.fetchall()
    for row in enrolled:
        c2.execute('''
            INSERT OR IGNORE INTO attendance (session_id, student_id, course_id, timestamp, status, method)
            VALUES (?, ?, ?, ?, 'absent', 'manual')
        ''', (session_id, row['student_id'], course_id, now.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': 'Attendance session started successfully!',
        'session': new_session
    })

@app.route('/api/sessions/active')
def get_active_sessions():
    teacher_id = request.args.get('teacher_id')
    course_id = request.args.get('course_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT s.*, c.code as course_code, c.name as course_name, u.name as teacher_name,
               (SELECT COUNT(*) FROM attendance a WHERE a.session_id = s.id AND a.status = 'present') as present_count,
               (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = s.course_id) as total_enrolled
        FROM sessions s
        JOIN courses c ON s.course_id = c.id
        JOIN users u ON c.teacher_id = u.user_id
        WHERE s.is_active = 1
    '''
    params = []
    if teacher_id:
        query += ' AND c.teacher_id = ?'
        params.append(teacher_id)
    if course_id:
        query += ' AND s.course_id = ?'
        params.append(course_id)

    query += ' ORDER BY s.created_at DESC'
    cursor.execute(query, params)
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(sessions)

@app.route('/api/sessions/<int:session_id>/qr.png')
def session_qr_image(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, c.code as course_code, c.name as course_name 
        FROM sessions s 
        JOIN courses c ON s.course_id = c.id 
        WHERE s.id = ?
    ''', (session_id,))
    session = cursor.fetchone()
    conn.close()

    if not session:
        return 'Session not found', 404

    # QR payload contains JSON with token and session details
    payload = json.dumps({
        'type': 'ATTENDANCE_QR',
        'token': session['qr_token'],
        'session_code': session['session_code'],
        'course_code': session['course_code'],
        'course_name': session['course_name']
    })

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1e293b", back_color="#ffffff")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

@app.route('/api/sessions/<int:session_id>/live')
def session_live_data(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Session info
    cursor.execute('''
        SELECT s.*, c.code as course_code, c.name as course_name, c.teacher_id
        FROM sessions s
        JOIN courses c ON s.course_id = c.id
        WHERE s.id = ?
    ''', (session_id,))
    session = cursor.fetchone()
    if not session:
        conn.close()
        return jsonify({'error': 'Session not found'}), 404

    # Total enrolled students
    cursor.execute('SELECT COUNT(*) FROM enrollments WHERE course_id = ?', (session['course_id'],))
    total_enrolled = cursor.fetchone()[0]

    # Attendance roster with status
    cursor.execute('''
        SELECT u.user_id, u.name, u.email,
               COALESCE(a.status, 'absent') as status,
               a.timestamp as scan_time,
               a.method
        FROM enrollments e
        JOIN users u ON e.student_id = u.user_id
        LEFT JOIN attendance a ON a.session_id = ? AND a.student_id = u.user_id
        WHERE e.course_id = ?
        ORDER BY (a.status = 'present') DESC, a.timestamp DESC, u.user_id
    ''', (session_id, session['course_id']))

    roster = [dict(row) for row in cursor.fetchall()]

    present_count = sum(1 for r in roster if r['status'] == 'present')
    absent_count = total_enrolled - present_count
    attendance_pct = round((present_count / total_enrolled * 100), 1) if total_enrolled > 0 else 0.0

    conn.close()

    # Check expiration
    expires_at = datetime.strptime(session['expires_at'], '%Y-%m-%d %H:%M:%S')
    is_expired = datetime.now() > expires_at

    return jsonify({
        'session': dict(session),
        'total_enrolled': total_enrolled,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_pct,
        'is_expired': is_expired,
        'roster': roster
    })

@app.route('/api/sessions/<int:session_id>/toggle', methods=['POST'])
def toggle_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_active FROM sessions WHERE id = ?', (session_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Session not found'}), 404

    new_status = 0 if row['is_active'] == 1 else 1
    cursor.execute('UPDATE sessions SET is_active = ? WHERE id = ?', (new_status, session_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'is_active': new_status})

# ----------------- Scan & Attendance Submission API ----------------- #

@app.route('/api/attendance/scan', methods=['POST'])
def scan_attendance():
    data = request.json or {}
    scanned_raw = data.get('token') or data.get('session_code')
    student_id = data.get('student_id')

    if not scanned_raw or not student_id:
        return jsonify({'success': False, 'message': 'Missing QR token or Student ID'}), 400

    # Clean token if JSON string was scanned
    token = scanned_raw
    session_code_hint = None
    if isinstance(scanned_raw, str) and scanned_raw.startswith('{'):
        try:
            parsed = json.loads(scanned_raw)
            token = parsed.get('token', token)
            session_code_hint = parsed.get('session_code')
        except Exception:
            pass

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify student exists
    cursor.execute('SELECT * FROM users WHERE user_id = ? AND role = "student"', (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'success': False, 'message': f'Student ID "{student_id}" not found'}), 404

    # Find matching session by qr_token OR session_code
    cursor.execute('''
        SELECT s.*, c.code as course_code, c.name as course_name, c.id as course_id
        FROM sessions s
        JOIN courses c ON s.course_id = c.id
        WHERE s.qr_token = ? OR s.session_code = ? OR s.session_code = ?
    ''', (token, token, session_code_hint))
    session = cursor.fetchone()

    if not session:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid QR Code or Session Code. Please verify with teacher.'}), 404

    # Check if session is active
    if session['is_active'] != 1:
        conn.close()
        return jsonify({'success': False, 'message': f"Session for {session['course_name']} is currently closed/ended by the instructor."}), 400

    # Check if session is expired
    expires_at = datetime.strptime(session['expires_at'], '%Y-%m-%d %H:%M:%S')
    if datetime.now() > expires_at:
        conn.close()
        return jsonify({'success': False, 'message': f"This attendance session expired at {expires_at.strftime('%I:%M %p')}. Ask teacher to reopen."}), 400

    # Verify student is enrolled in this course
    cursor.execute('SELECT * FROM enrollments WHERE student_id = ? AND course_id = ?', (student_id, session['course_id']))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': f"You are not enrolled in {session['course_name']} ({session['course_code']})."}), 403

    # Check if already marked present
    cursor.execute('''
        SELECT * FROM attendance 
        WHERE session_id = ? AND student_id = ? AND status = 'present'
    ''', (session['id'], student_id))
    already_marked = cursor.fetchone()

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if already_marked:
        conn.close()
        return jsonify({
            'success': True,
            'already_marked': True,
            'message': f"You have already scanned and marked attendance for this session at {already_marked['timestamp']}.",
            'details': {
                'student_name': student['name'],
                'student_id': student['user_id'],
                'course': f"{session['course_code']} - {session['course_name']}",
                'timestamp': already_marked['timestamp']
            }
        })

    # Record / update attendance as present
    cursor.execute('''
        INSERT INTO attendance (session_id, student_id, course_id, timestamp, status, method)
        VALUES (?, ?, ?, ?, 'present', 'qr_scan')
        ON CONFLICT(session_id, student_id) DO UPDATE SET
            status = 'present',
            timestamp = excluded.timestamp,
            method = 'qr_scan'
    ''', (session['id'], student_id, session['course_id'], now_str))

    conn.commit()
    conn.close()

    # Recalculate updated stats for student
    updated_stats = calculate_student_stats(student_id)

    return jsonify({
        'success': True,
        'already_marked': False,
        'message': f"Success! Attendance marked for {session['course_code']} ({session['course_name']}).",
        'details': {
            'student_name': student['name'],
            'student_id': student['user_id'],
            'course': f"{session['course_code']} - {session['course_name']}",
            'session_title': session['title'],
            'timestamp': now_str
        },
        'updated_stats': updated_stats
    })

# ----------------- Teacher Manual Attendance Marking API ----------------- #

@app.route('/api/attendance/manual', methods=['POST'])
def manual_attendance():
    data = request.json or {}
    session_id = data.get('session_id')
    student_id = data.get('student_id')
    status = data.get('status', 'present') # 'present', 'absent', 'late'

    if not session_id or not student_id:
        return jsonify({'error': 'session_id and student_id are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT course_id FROM sessions WHERE id = ?', (session_id,))
    session = cursor.fetchone()
    if not session:
        conn.close()
        return jsonify({'error': 'Session not found'}), 404

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO attendance (session_id, student_id, course_id, timestamp, status, method)
        VALUES (?, ?, ?, ?, ?, 'manual')
        ON CONFLICT(session_id, student_id) DO UPDATE SET
            status = excluded.status,
            timestamp = excluded.timestamp,
            method = 'manual'
    ''', (session_id, student_id, session['course_id'], now_str, status))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'status': status, 'student_id': student_id})

@app.route('/api/attendance/batch-update', methods=['POST'])
def batch_update_attendance():
    data = request.json or {}
    session_id = data.get('session_id')
    records = data.get('records', []) # list of {student_id, status}

    if not session_id or not records:
        return jsonify({'error': 'session_id and records are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT course_id FROM sessions WHERE id = ?', (session_id,))
    session = cursor.fetchone()
    if not session:
        conn.close()
        return jsonify({'error': 'Session not found'}), 404

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for r in records:
        cursor.execute('''
            INSERT INTO attendance (session_id, student_id, course_id, timestamp, status, method)
            VALUES (?, ?, ?, ?, ?, 'manual')
            ON CONFLICT(session_id, student_id) DO UPDATE SET
                status = excluded.status,
                timestamp = excluded.timestamp,
                method = 'manual'
        ''', (session_id, r['student_id'], session['course_id'], now_str, r['status']))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'count': len(records)})

# ----------------- Course Analytics & Export Report ----------------- #

@app.route('/api/reports/course/<int:course_id>')
def course_report(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Course details
    cursor.execute('SELECT c.*, u.name as teacher_name FROM courses c JOIN users u ON c.teacher_id = u.user_id WHERE c.id = ?', (course_id,))
    course = cursor.fetchone()
    if not course:
        conn.close()
        return jsonify({'error': 'Course not found'}), 404

    # Total sessions for this course
    cursor.execute('SELECT COUNT(*) FROM sessions WHERE course_id = ?', (course_id,))
    total_sessions = cursor.fetchone()[0]

    # Enrolled students with attendance count
    cursor.execute('''
        SELECT u.user_id, u.name, u.email,
               (SELECT COUNT(*) FROM attendance a WHERE a.course_id = ? AND a.student_id = u.user_id AND a.status IN ('present', 'late')) as attended
        FROM enrollments e
        JOIN users u ON e.student_id = u.user_id
        WHERE e.course_id = ?
        ORDER BY u.user_id
    ''', (course_id, course_id))

    students_data = []
    for row in cursor.fetchall():
        attended = row['attended']
        pct = round((attended / total_sessions * 100), 1) if total_sessions > 0 else 0.0
        students_data.append({
            'user_id': row['user_id'],
            'name': row['name'],
            'email': row['email'],
            'total_sessions': total_sessions,
            'attended': attended,
            'absent': total_sessions - attended,
            'percentage': pct,
            'status': 'Eligible' if pct >= 75.0 else 'Shortage (<75%)',
            'is_low': pct < 75.0 if total_sessions > 0 else False
        })

    # Average class attendance
    avg_pct = round(sum(s['percentage'] for s in students_data) / len(students_data), 1) if students_data else 0.0
    low_attendance_count = sum(1 for s in students_data if s['is_low'])

    conn.close()

    return jsonify({
        'course': dict(course),
        'total_sessions': total_sessions,
        'average_attendance': avg_pct,
        'low_attendance_count': low_attendance_count,
        'students': students_data
    })

@app.route('/api/reports/course/<int:course_id>/export-csv')
def export_course_csv(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    if not course:
        conn.close()
        return 'Course not found', 404

    cursor.execute('SELECT COUNT(*) FROM sessions WHERE course_id = ?', (course_id,))
    total_sessions = cursor.fetchone()[0]

    cursor.execute('''
        SELECT u.user_id, u.name, u.email,
               (SELECT COUNT(*) FROM attendance a WHERE a.course_id = ? AND a.student_id = u.user_id AND a.status IN ('present', 'late')) as attended
        FROM enrollments e
        JOIN users u ON e.student_id = u.user_id
        WHERE e.course_id = ?
        ORDER BY u.user_id
    ''', (course_id, course_id))
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Roll Number', 'Student Name', 'Email', 'Course Code', 'Course Name', 'Total Classes', 'Attended', 'Absent', 'Attendance Percentage (%)', 'Eligibility Status'])

    for r in rows:
        attended = r['attended']
        pct = round((attended / total_sessions * 100), 1) if total_sessions > 0 else 0.0
        status = 'Eligible (>=75%)' if pct >= 75.0 else 'Shortage (<75%)'
        writer.writerow([r['user_id'], r['name'], r['email'], course['code'], course['name'], total_sessions, attended, total_sessions - attended, f"{pct}%", status])

    output.seek(0)
    filename = f"attendance_report_{course['code']}_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

# ----------------- Presentation Download API ----------------- #

@app.route('/api/presentation/download')
def download_presentation():
    pptx_path = os.path.join(os.path.dirname(__file__), 'SmartAttend_Attendance_System_Presentation.pptx')
    if not os.path.exists(pptx_path):
        import generate_presentation
        generate_presentation.build_presentation()
    return send_file(
        pptx_path,
        as_attachment=True,
        download_name='SmartAttend_Attendance_System_Presentation.pptx',
        mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
    )

@app.route('/presentation')
def presentation_view():
    return render_template('presentation.html')

if __name__ == '__main__':
    print("Starting Attendance Management Server on http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)
