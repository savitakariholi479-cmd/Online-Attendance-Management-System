# SmartAttend - Online Attendance Management System with QR Code

A modern, responsive web application for educational institutions that enables **teachers to generate secure QR codes and record attendance**, and **students to scan QR codes and track their attendance percentage**.

---

## 🚀 Key Features

### 👨‍🏫 Teacher Portal
- **Dynamic QR Code Generation:**
  - Create attendance sessions for any subject/course with custom lecture topics.
  - Set validity duration (5m, 15m, 30m, 1h, or 2h).
  - High-resolution, dynamically encrypted QR codes generated on the fly.
  - **Fullscreen Projector Mode** for classroom smartboards and projectors.
  - Generates a human-readable **Session Code** (e.g. `CS-301-LIVE`) for students whose camera may be unavailable.
- **Live Attendance Monitoring:**
  - Auto-refreshing feed updates every 3 seconds as students scan.
  - Turnout counter (e.g., `8 / 10 Enrolled - 80%`).
  - Session control: Instant "Close / End Session" or "Reopen" buttons.
- **Manual Attendance Register:**
  - View full roster of students enrolled in the class.
  - Quick toggle between `Present` and `Absent`.
  - "Mark All Present" / "Mark All Absent" shortcuts with batch save.
- **Analytics & CSV Reports:**
  - Real-time overall average attendance percentage.
  - Count of students with low attendance (< 75% shortage).
  - One-click **Export to CSV / Excel** report for university administrative records.

---

### 👨‍🎓 Student Portal
- **Interactive QR Code Scanner:**
  - Integrated camera scanner using `html5-qrcode`.
  - Multi-camera support (switch between front and back camera).
  - Web Audio API synthetic chime and confetti animation upon successful scan!
  - Alternative scan options:
    - **Enter Session Code manually**
    - **Upload QR screenshot/photo**
  - Instant confirmation showing lecture title, subject, and timestamp.
  - Anti-proxy protection: prevents duplicate scans from the same student account.
- **Attendance Percentage Dashboard:**
  - **Animated circular percentage gauge** displaying overall attendance rate.
  - Visual status pill:
    - 🟢 `Eligible for Exams (>= 75%)`
    - 🔴 `Shortage Alert (< 75%)` with warning notice explaining how many consecutive classes are needed to regain eligibility.
  - Subject-by-subject cards with progress bars and attended/missed lecture counts.
  - Recent check-in history table.

---

### 🔄 Instant Persona / Role Switcher
- Switch seamlessly between:
  - **Teachers:** Dr. Rajiv Sharma (Computer Science), Prof. Meera Verma (Mathematics)
  - **Students:** Aarav Sharma (Good standing ~86%), Ananya Patel (Shortage alert ~58%), Maaz Khan (High attendance ~94%), and more.
- Ideal for project presentations, live demonstrations, and evaluations.

---

## 🛠️ Technology Stack
- **Backend:** Python 3, Flask, SQLite3, Pillow, QRCode library
- **Frontend:** HTML5, Modern CSS, Tailwind CSS CDN, FontAwesome 6, Canvas Confetti
- **QR Scanner:** `html5-qrcode` (HTML5 Camera API)
- **Audio:** Web Audio API (zero audio file dependencies)

---

## 🏃 Running the Application

Double-click `start.bat` or run:

```bash
python app.py
```

Then open your browser at:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Automated Test Suite
To run the automated tests verifying all APIs, QR generation, percentage calculations, duplicate prevention, and CSV exports:

```bash
python test_system.py
```
