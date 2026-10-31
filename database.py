import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'attendance.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL, -- e.g. T101 or 2024CS01
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT CHECK(role IN ('teacher', 'student')) NOT NULL,
            department TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            teacher_id TEXT NOT NULL,
            semester TEXT DEFAULT 'Fall 2026',
            FOREIGN KEY(teacher_id) REFERENCES users(user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            UNIQUE(student_id, course_id),
            FOREIGN KEY(student_id) REFERENCES users(user_id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            session_code TEXT UNIQUE NOT NULL, -- short readable code e.g. CS-9482
            qr_token TEXT UNIQUE NOT NULL,    -- secret token encoded in QR
            title TEXT DEFAULT 'Lecture',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('present', 'absent', 'late')) DEFAULT 'present',
            method TEXT CHECK(method IN ('qr_scan', 'manual')) DEFAULT 'qr_scan',
            notes TEXT DEFAULT '',
            UNIQUE(session_id, student_id),
            FOREIGN KEY(session_id) REFERENCES sessions(id),
            FOREIGN KEY(student_id) REFERENCES users(user_id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')

    conn.commit()

    # Check if database needs seeding
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    print("Seeding database with realistic sample records...")

    # Teachers
    teachers = [
        ('T101', 'Dr. Rajiv Sharma', 'sharma@university.edu', 'teacher', 'Computer Science & Engineering'),
        ('T102', 'Prof. Meera Verma', 'verma@university.edu', 'teacher', 'Applied Mathematics')
    ]
    cursor.executemany(
        'INSERT INTO users (user_id, name, email, role, department) VALUES (?, ?, ?, ?, ?)',
        teachers
    )

    # Students
    students = [
        ('2024CS01', 'Aarav Sharma', 'aarav.sharma@student.edu', 'student', 'Computer Science'),
        ('2024CS02', 'Ananya Patel', 'ananya.patel@student.edu', 'student', 'Computer Science'),
        ('2024CS03', 'Maaz Khan', 'maaz.khan@student.edu', 'student', 'Computer Science'),
        ('2024CS04', 'Rohan Gupta', 'rohan.gupta@student.edu', 'student', 'Computer Science'),
        ('2024CS05', 'Priya Nair', 'priya.nair@student.edu', 'student', 'Computer Science'),
        ('2024CS06', 'Kabir Singh', 'kabir.singh@student.edu', 'student', 'Computer Science'),
        ('2024CS07', 'Sara Ali', 'sara.ali@student.edu', 'student', 'Computer Science'),
        ('2024CS08', 'Vikram Aditya', 'vikram.aditya@student.edu', 'student', 'Computer Science'),
        ('2024CS09', 'Divya Prakash', 'divya.prakash@student.edu', 'student', 'Computer Science'),
        ('2024CS10', 'Rahul Verma', 'rahul.verma@student.edu', 'student', 'Computer Science')
    ]
    cursor.executemany(
        'INSERT INTO users (user_id, name, email, role, department) VALUES (?, ?, ?, ?, ?)',
        students
    )

    # Courses
    courses = [
        ('CS301', 'Data Structures & Algorithms', 'T101', 'Semester 5'),
        ('CS302', 'Database Management Systems', 'T101', 'Semester 5'),
        ('CS304', 'Web Technologies & Frameworks', 'T101', 'Semester 5'),
        ('MA301', 'Discrete Mathematics', 'T102', 'Semester 5')
    ]
    cursor.executemany(
        'INSERT INTO courses (code, name, teacher_id, semester) VALUES (?, ?, ?, ?)',
        courses
    )

    # Enroll all students into all 4 courses
    for course_id in range(1, 5):
        for s in students:
            cursor.execute(
                'INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)',
                (s[0], course_id)
            )

    # Generate historical sessions over the last 14 days
    # Let's say 4 sessions per course = 16 sessions total in the past
    now = datetime.now()
    session_id_counter = 1

    # Predetermined student attendance weights to simulate realistic variance
    # Some high attendance, some average, some at risk (< 75%)
    student_rates = {
        '2024CS01': 0.88, # Aarav - Good (88%)
        '2024CS02': 0.62, # Ananya - Low Attendance Alert! (62%)
        '2024CS03': 0.94, # Maaz - Excellent (94%)
        '2024CS04': 0.81, # Rohan - Good (81%)
        '2024CS05': 0.96, # Priya - Outstanding (96%)
        '2024CS06': 0.72, # Kabir - Borderline Warning (72%)
        '2024CS07': 0.88, # Sara - Good (88%)
        '2024CS08': 0.78, # Vikram - Safe (78%)
        '2024CS09': 0.68, # Divya - Low Attendance Alert! (68%)
        '2024CS10': 0.84  # Rahul - Safe (84%)
    }

    random.seed(42) # Deterministic for consistent, clean initial stats

    for day_offset in range(14, 0, -1):
        # 1 or 2 lectures per day
        session_date = now - timedelta(days=day_offset, hours=random.randint(1, 4))
        for course_id in [1, 2, 3, 4]:
            if random.random() > 0.5: # 50% chance course had a lecture on this day
                code_suffix = random.randint(1000, 9999)
                session_code = f"HIST-{course_id}{code_suffix}"
                qr_token = f"HIST_TOKEN_{course_id}_{code_suffix}"
                created_str = session_date.strftime('%Y-%m-%d %H:%M:%S')
                expires_str = (session_date + timedelta(minutes=45)).strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute('''
                    INSERT INTO sessions (course_id, session_code, qr_token, title, created_at, expires_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                ''', (course_id, session_code, qr_token, f'Lecture on Module {random.randint(1, 5)}', created_str, expires_str))
                
                curr_session_id = cursor.lastrowid

                # Populate student attendance for this historical session
                for s in students:
                    roll = s[0]
                    target_rate = student_rates.get(roll, 0.8)
                    is_present = random.random() < target_rate
                    if is_present:
                        scan_delay = random.randint(1, 15)
                        scan_time = (session_date + timedelta(minutes=scan_delay)).strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute('''
                            INSERT INTO attendance (session_id, student_id, course_id, timestamp, status, method)
                            VALUES (?, ?, ?, ?, 'present', 'qr_scan')
                        ''', (curr_session_id, roll, course_id, scan_time))
                    else:
                        # Record absent or leave unrecorded (unrecorded in total sessions counts as absent)
                        cursor.execute('''
                            INSERT INTO attendance (session_id, student_id, course_id, timestamp, status, method)
                            VALUES (?, ?, ?, ?, 'absent', 'manual')
                        ''', (curr_session_id, roll, course_id, created_str))

    # Also create ONE currently active session for CS301 (Data Structures)
    # Ready for demo testing immediately!
    demo_active_token = "QR_SESSION_CS301_DEMO"
    demo_expires = (now + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO sessions (course_id, session_code, qr_token, title, created_at, expires_at, is_active)
        VALUES (1, 'CS-301-LIVE', ?, 'Live Lecture: Binary Search Trees', ?, ?, 1)
    ''', (demo_active_token, now.strftime('%Y-%m-%d %H:%M:%S'), demo_expires))

    demo_session_id = cursor.lastrowid
    # Have 2 students already scanned in to show live activity
    cursor.execute('''
        INSERT INTO attendance (session_id, student_id, course_id, timestamp, status, method)
        VALUES (?, '2024CS05', 1, ?, 'present', 'qr_scan')
    ''', (demo_session_id, now.strftime('%Y-%m-%d %H:%M:%S')))
    cursor.execute('''
        INSERT INTO attendance (session_id, student_id, course_id, timestamp, status, method)
        VALUES (?, '2024CS07', 1, ?, 'present', 'qr_scan')
    ''', (demo_session_id, (now + timedelta(seconds=45)).strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    init_db()
    print("Database initialized at", DB_PATH)
