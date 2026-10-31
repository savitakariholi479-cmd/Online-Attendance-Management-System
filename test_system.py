import json
from app import app
from database import get_db_connection

def test_attendance_system():
    client = app.test_client()

    print("\n--- 1. Testing User Listing ---")
    res = client.get('/api/users')
    assert res.status_code == 200
    users = json.loads(res.data)
    print(f"Total Users loaded: {len(users)}")
    teachers = [u for u in users if u['role'] == 'teacher']
    students = [u for u in users if u['role'] == 'student']
    print(f"Teachers: {len(teachers)}, Students: {len(students)}")
    assert len(teachers) >= 2
    assert len(students) >= 10

    print("\n--- 2. Testing Student Attendance Stats Calculation ---")
    res = client.get('/api/student/2024CS01/stats')
    assert res.status_code == 200
    data = json.loads(res.data)
    print(f"Student: {data['student']['name']}")
    print(f"Overall Percentage: {data['overall']['percentage']}%")
    print(f"Total Conducted: {data['overall']['total_conducted']}, Attended: {data['overall']['total_attended']}")
    print(f"Courses enrolled: {len(data['courses'])}")
    for c in data['courses']:
        print(f"  - {c['code']} ({c['name']}): {c['attended']}/{c['total_sessions']} ({c['percentage']}%)")

    # Also test student with low attendance warning
    res2 = client.get('/api/student/2024CS02/stats')
    data2 = json.loads(res2.data)
    print(f"\nTesting low attendance student: {data2['student']['name']}")
    print(f"Overall Percentage: {data2['overall']['percentage']}% | Warning: {data2['overall']['is_low']}")

    print("\n--- 3. Testing Session Creation & QR Generation ---")
    res = client.post('/api/sessions/create', json={
        'course_id': 1,
        'title': 'Test Algorithms Session',
        'duration_minutes': 45
    })
    assert res.status_code == 200
    new_session_data = json.loads(res.data)
    assert new_session_data['success'] is True
    session_id = new_session_data['session']['id']
    qr_token = new_session_data['session']['qr_token']
    session_code = new_session_data['session']['session_code']
    print(f"Created Session ID: {session_id}")
    print(f"Session Code: {session_code}")
    print(f"QR Token: {qr_token}")

    # Check QR PNG endpoint
    res_qr = client.get(f'/api/sessions/{session_id}/qr.png')
    assert res_qr.status_code == 200
    assert res_qr.mimetype == 'image/png'
    print(f"QR PNG generated successfully! Size: {len(res_qr.data)} bytes")

    print("\n--- 4. Testing Student QR Attendance Scan ---")
    # Scan attendance for student 2024CS01
    scan_res = client.post('/api/attendance/scan', json={
        'token': qr_token,
        'student_id': '2024CS01'
    })
    assert scan_res.status_code == 200
    scan_data = json.loads(scan_res.data)
    assert scan_data['success'] is True
    assert scan_data['already_marked'] is False
    print(f"Scan Success: {scan_data['message']}")
    print(f"Updated Stats: {scan_data['updated_stats']['overall']['percentage']}%")

    # Duplicate scan test
    scan_dup = client.post('/api/attendance/scan', json={
        'token': qr_token,
        'student_id': '2024CS01'
    })
    assert scan_dup.status_code == 200
    dup_data = json.loads(scan_dup.data)
    assert dup_data['already_marked'] is True
    print(f"Duplicate Scan prevented: {dup_data['message']}")

    # Manual session code scan test for another student
    scan_code = client.post('/api/attendance/scan', json={
        'session_code': session_code,
        'student_id': '2024CS03'
    })
    assert scan_code.status_code == 200
    code_data = json.loads(scan_code.data)
    assert code_data['success'] is True
    print(f"Session Code scan success: {code_data['message']}")

    print("\n--- 5. Testing Live Session Feed ---")
    res_live = client.get(f'/api/sessions/{session_id}/live')
    assert res_live.status_code == 200
    live_data = json.loads(res_live.data)
    print(f"Present count: {live_data['present_count']} / {live_data['total_enrolled']}")
    print(f"Turnout percentage: {live_data['attendance_percentage']}%")
    assert live_data['present_count'] >= 2

    print("\n--- 6. Testing Course Analytics & CSV Export ---")
    res_rep = client.get('/api/reports/course/1')
    assert res_rep.status_code == 200
    rep_data = json.loads(res_rep.data)
    print(f"Course: {rep_data['course']['name']}")
    print(f"Average Attendance: {rep_data['average_attendance']}%")
    print(f"Students with shortage: {rep_data['low_attendance_count']}")

    res_csv = client.get('/api/reports/course/1/export-csv')
    assert res_csv.status_code == 200
    assert 'text/csv' in res_csv.mimetype
    csv_text = res_csv.data.decode('utf-8')
    assert 'Roll Number' in csv_text
    assert '2024CS01' in csv_text
    print(f"CSV Export generated successfully with {len(csv_text.splitlines())} rows!")

    print("\n--- 7. Testing Teacher Add & Delete Student API ---")
    test_stu = {
        'user_id': '2024CS88',
        'name': 'Pooja Hegde',
        'email': 'pooja.hegde@student.edu',
        'department': 'Computer Science',
        'course_ids': [1, 2]
    }
    res_add = client.post('/api/students/add', json=test_stu)
    assert res_add.status_code == 200
    add_data = json.loads(res_add.data)
    assert add_data['success'] is True
    print(f"Added student: {add_data['student']['name']} ({add_data['student']['user_id']})")

    # Clean up test student
    res_del = client.delete('/api/students/2024CS88')
    assert res_del.status_code == 200
    print("Deleted test student cleanly.")

    print("\n ALL BACKEND TESTS PASSED CLEANLY!")

if __name__ == '__main__':
    test_attendance_system()
