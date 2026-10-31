// SmartAttend - Frontend Application Script

let currentUser = null;
let currentRole = 'student';
let usersList = [];
let html5QrScanner = null;
let activeLiveSessionId = null;
let livePollInterval = null;
let manualRosterState = [];

// Audio Context for scan chime
let audioCtx = null;
function playSuccessBeep() {
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        const now = audioCtx.currentTime;

        // Tone 1
        const osc1 = audioCtx.createOscillator();
        const gain1 = audioCtx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(587.33, now); // D5
        gain1.gain.setValueAtTime(0.2, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
        osc1.connect(gain1);
        gain1.connect(audioCtx.destination);
        osc1.start(now);
        osc1.stop(now + 0.15);

        // Tone 2 (higher chord note)
        const osc2 = audioCtx.createOscillator();
        const gain2 = audioCtx.createGain();
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(880, now + 0.1); // A5
        gain2.gain.setValueAtTime(0.25, now + 0.1);
        gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
        osc2.connect(gain2);
        gain2.connect(audioCtx.destination);
        osc2.start(now + 0.1);
        osc2.stop(now + 0.35);
    } catch (e) {
        console.warn("Audio playback not permitted yet:", e);
    }
}

// ---------------- Init App ---------------- //
document.addEventListener('DOMContentLoaded', async () => {
    await loadUsers();
    // Default to student Aarav Sharma
    const defaultStudent = usersList.find(u => u.user_id === '2024CS01') || usersList.find(u => u.role === 'student');
    if (defaultStudent) {
        setCurrentUser(defaultStudent);
    }
});

async function loadUsers() {
    try {
        const res = await fetch('/api/users');
        usersList = await res.json();

        const selector = document.getElementById('userSelector');
        selector.innerHTML = '';

        const studentGroup = document.createElement('optgroup');
        studentGroup.label = 'Students';

        const teacherGroup = document.createElement('optgroup');
        teacherGroup.label = 'Faculty / Teachers';

        usersList.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.user_id;
            opt.textContent = `${u.name} (${u.user_id})`;
            if (u.role === 'student') {
                studentGroup.appendChild(opt);
            } else {
                teacherGroup.appendChild(opt);
            }
        });

        selector.appendChild(studentGroup);
        selector.appendChild(teacherGroup);
    } catch (err) {
        console.error('Failed to load users:', err);
    }
}

function onUserSelectChange(userId) {
    const user = usersList.find(u => u.user_id === userId);
    if (user) {
        setCurrentUser(user);
    }
}

function setCurrentUser(user) {
    currentUser = user;
    currentRole = user.role;

    // Update Header
    document.getElementById('userDisplayName').textContent = user.name;
    document.getElementById('userDisplaySub').textContent = `${user.user_id} (${user.role.toUpperCase()})`;
    document.getElementById('userSelector').value = user.user_id;

    // Initials avatar
    const initials = user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    const avatarEl = document.getElementById('userAvatar');
    avatarEl.textContent = initials;
    avatarEl.className = `w-9 h-9 rounded-full font-bold text-xs flex items-center justify-center shadow-inner ${user.role === 'teacher' ? 'bg-indigo-600 text-white' : 'bg-blue-600 text-white'}`;

    // Switch Role UI view
    updateRoleView();
}

function switchRole(role) {
    if (role === currentRole) return;
    // Pick first user of that role
    const nextUser = usersList.find(u => u.role === role);
    if (nextUser) {
        setCurrentUser(nextUser);
    }
}

function updateRoleView() {
    const isTeacher = currentRole === 'teacher';
    const studentView = document.getElementById('studentView');
    const teacherView = document.getElementById('teacherView');

    const navTeacher = document.getElementById('navRoleTeacher');
    const navStudent = document.getElementById('navRoleStudent');
    const mobTeacher = document.getElementById('mobileNavTeacher');
    const mobStudent = document.getElementById('mobileNavStudent');

    if (isTeacher) {
        studentView.classList.add('hidden');
        teacherView.classList.remove('hidden');

        // Nav tabs active states
        navTeacher.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 bg-white text-indigo-600 shadow-sm";
        navStudent.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 text-slate-600 hover:text-slate-900";
        mobTeacher.className = "flex-1 py-1.5 rounded-lg text-xs font-semibold text-center bg-white text-indigo-600 shadow-sm border border-slate-200";
        mobStudent.className = "flex-1 py-1.5 rounded-lg text-xs font-semibold text-center text-slate-600 border border-transparent";

        loadTeacherData();
    } else {
        teacherView.classList.add('hidden');
        studentView.classList.remove('hidden');

        navStudent.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 bg-white text-blue-600 shadow-sm";
        navTeacher.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 text-slate-600 hover:text-slate-900";
        mobStudent.className = "flex-1 py-1.5 rounded-lg text-xs font-semibold text-center bg-white text-blue-600 shadow-sm border border-slate-200";
        mobTeacher.className = "flex-1 py-1.5 rounded-lg text-xs font-semibold text-center text-slate-600 border border-transparent";

        // Stop teacher polling if active
        if (livePollInterval) clearInterval(livePollInterval);

        loadStudentData();
    }
}

// ============================================================== //
// STUDENT VIEW LOGIC
// ============================================================== //

async function loadStudentData() {
    if (!currentUser || currentUser.role !== 'student') return;

    // Greeting
    const firstName = currentUser.name.split(' ')[0];
    document.getElementById('studentGreetingName').textContent = firstName;

    try {
        const res = await fetch(`/api/student/${currentUser.user_id}/stats`);
        if (!res.ok) throw new Error('Failed to load student stats');
        const data = await res.json();

        // 1. Overall Attendance Ring
        const pct = data.overall.percentage;
        const pctText = document.getElementById('overallPctText');
        const progressRing = document.getElementById('overallProgressRing');
        const eligibilityBadge = document.getElementById('eligibilityBadge');
        const lowBanner = document.getElementById('lowAttendanceBanner');

        pctText.textContent = `${pct}%`;

        // Circumference of circle with r=54: 2 * pi * 54 = 339.292
        const circumference = 339.292;
        const offset = circumference - (pct / 100) * circumference;
        progressRing.style.strokeDashoffset = offset;

        // Color coding
        if (pct >= 75.0) {
            progressRing.className = "text-emerald-500 transition-all duration-1000 ease-out";
            eligibilityBadge.className = "mt-3 px-3.5 py-1 rounded-full text-xs font-bold inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200";
            eligibilityBadge.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>Eligible for Exams (${pct}%)</span>`;
            lowBanner.classList.add('hidden');
        } else {
            progressRing.className = "text-rose-500 transition-all duration-1000 ease-out";
            eligibilityBadge.className = "mt-3 px-3.5 py-1 rounded-full text-xs font-bold inline-flex items-center gap-1.5 bg-rose-50 text-rose-700 border border-rose-200";
            eligibilityBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <span>Attendance Shortage (${pct}%)</span>`;
            
            lowBanner.classList.remove('hidden');
            document.getElementById('lowAttendanceMessage').textContent = 
                `Your current attendance is ${pct}%, which is below the mandatory 75% requirement. Please attend remaining classes to avoid debarment from end-semester examinations.`;
        }

        // Mini counters
        document.getElementById('totalAttendedCount').textContent = `${data.overall.total_attended} / ${data.overall.total_conducted}`;
        document.getElementById('totalMissedCount').textContent = data.overall.total_absent;

        // 2. Subject-wise Cards
        renderStudentCourseCards(data.courses);

        // 3. Recent Attendance Table
        renderStudentAttendanceTable(data.recent_records);

    } catch (err) {
        console.error('Error fetching student stats:', err);
    }
}

function renderStudentCourseCards(courses) {
    const grid = document.getElementById('studentCoursesGrid');
    grid.innerHTML = '';

    courses.forEach(c => {
        const isSafe = c.percentage >= 75.0;
        const card = document.createElement('div');
        card.className = "bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex flex-col justify-between interactive-card";

        const badgeColor = isSafe ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-rose-50 text-rose-700 border-rose-200';
        const progressColor = isSafe ? 'bg-emerald-500' : 'bg-rose-500';

        card.innerHTML = `
            <div>
                <div class="flex items-center justify-between">
                    <span class="text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">${c.code}</span>
                    <span class="text-[11px] font-bold px-2 py-0.5 rounded-full border ${badgeColor}">
                        ${isSafe ? 'Eligible' : 'Shortage'}
                    </span>
                </div>
                <h4 class="text-sm font-bold text-slate-900 mt-2 leading-snug">${c.name}</h4>
                <p class="text-[11px] text-slate-500 mt-0.5">Faculty: ${c.teacher_name}</p>
            </div>

            <div class="mt-4 pt-3 border-t border-slate-100">
                <div class="flex items-baseline justify-between mb-1.5">
                    <span class="text-xl font-extrabold ${isSafe ? 'text-slate-900' : 'text-rose-600'}">${c.percentage}%</span>
                    <span class="text-xs font-semibold text-slate-500">${c.attended} / ${c.total_sessions} classes</span>
                </div>

                <!-- Progress Bar -->
                <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div class="${progressColor} h-2 rounded-full transition-all duration-700" style="width: ${c.percentage}%"></div>
                </div>

                ${!isSafe && c.needed_for_75 > 0 ? `
                    <div class="mt-2 text-[10px] font-semibold text-rose-600 flex items-center gap-1">
                        <i class="fa-solid fa-arrow-trend-up"></i>
                        <span>Need ${c.needed_for_75} consecutive class${c.needed_for_75 > 1 ? 'es' : ''} to reach 75%</span>
                    </div>
                ` : `
                    <div class="mt-2 text-[10px] font-medium text-slate-400 flex items-center gap-1">
                        <i class="fa-regular fa-calendar-check text-emerald-500"></i>
                        <span>${c.absent} missed lecture${c.absent === 1 ? '' : 's'}</span>
                    </div>
                `}
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderStudentAttendanceTable(records) {
    const tbody = document.getElementById('studentAttendanceTableBody');
    tbody.innerHTML = '';

    if (!records || records.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="px-5 py-6 text-center text-slate-400">No attendance records found.</td></tr>`;
        return;
    }

    records.forEach(r => {
        const isPresent = r.status === 'present';
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50/80 transition-colors";

        tr.innerHTML = `
            <td class="px-5 py-3 font-semibold text-slate-900">${r.course_code}</td>
            <td class="px-5 py-3 text-slate-600">${r.session_title || 'Lecture Session'}</td>
            <td class="px-5 py-3 text-slate-500">${formatDateTime(r.timestamp)}</td>
            <td class="px-5 py-3">
                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-600">
                    <i class="${r.method === 'qr_scan' ? 'fa-solid fa-qrcode text-blue-500' : 'fa-solid fa-user-pen text-slate-500'}"></i>
                    ${r.method === 'qr_scan' ? 'QR Scan' : 'Manual'}
                </span>
            </td>
            <td class="px-5 py-3">
                <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${isPresent ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                    <i class="${isPresent ? 'fa-solid fa-circle-check' : 'fa-solid fa-circle-xmark'}"></i>
                    ${isPresent ? 'Present' : 'Absent'}
                </span>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function refreshStudentData() {
    loadStudentData();
    showToast('Attendance data refreshed!', 'info');
}

// ============================================================== //
// QR SCANNING LOGIC (STUDENT)
// ============================================================== //

function openScannerModal() {
    const modal = document.getElementById('scannerModal');
    modal.classList.remove('hidden');

    const feedback = document.getElementById('scannerFeedback');
    feedback.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin text-blue-500"></i> <span>Initializing camera...</span>`;

    // Initialize Html5Qrcode
    try {
        if (!html5QrScanner) {
            html5QrScanner = new Html5Qrcode("qrReader");
        }

        const config = { fps: 10, qrbox: { width: 220, height: 220 } };

        html5QrScanner.start(
            { facingMode: "environment" },
            config,
            onQrCodeSuccess,
            (errorMessage) => {
                // Ignore frame parse warnings
            }
        ).then(() => {
            feedback.innerHTML = `<span class="text-emerald-600 font-semibold"><i class="fa-solid fa-camera mr-1"></i> Camera active. Align QR in square.</span>`;
        }).catch(err => {
            console.warn("Camera start failed, testing default video device:", err);
            // Try with default camera
            html5QrScanner.start({ facingMode: "user" }, config, onQrCodeSuccess, () => {})
                .catch(e => {
                    feedback.innerHTML = `<span class="text-rose-600"><i class="fa-solid fa-video-slash mr-1"></i> Camera inaccessible. Use Manual Code below!</span>`;
                });
        });
    } catch (e) {
        feedback.innerHTML = `<span class="text-rose-600">Camera error. Please enter code manually.</span>`;
    }
}

function closeScannerModal() {
    const modal = document.getElementById('scannerModal');
    modal.classList.add('hidden');

    if (html5QrScanner) {
        html5QrScanner.stop().catch(() => {}).then(() => {
            html5QrScanner.clear();
            html5QrScanner = null;
        });
    }
}

async function onQrCodeSuccess(decodedText) {
    // Play celebratory sound and confetti!
    playSuccessBeep();

    if (typeof confetti === 'function') {
        confetti({
            particleCount: 70,
            spread: 60,
            origin: { y: 0.6 }
        });
    }

    // Close camera modal
    closeScannerModal();

    // Submit token to backend
    await submitAttendanceToken(decodedText);
}

async function handleQRFileUpload(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];

    try {
        const scanner = new Html5Qrcode("qrReader");
        const result = await scanner.scanFile(file, true);
        playSuccessBeep();
        closeScannerModal();
        await submitAttendanceToken(result);
    } catch (err) {
        showToast('Could not detect a QR code in the image.', 'error');
    }
}

function openManualCodeModal() {
    document.getElementById('manualCodeModal').classList.remove('hidden');
    document.getElementById('manualCodeInput').value = '';
    setTimeout(() => document.getElementById('manualCodeInput').focus(), 100);
}

function closeManualCodeModal() {
    document.getElementById('manualCodeModal').classList.add('hidden');
}

async function handleManualCodeSubmit(e) {
    e.preventDefault();
    const code = document.getElementById('manualCodeInput').value.trim();
    if (!code) return;

    closeManualCodeModal();
    await submitAttendanceToken(code);
}

async function submitAttendanceToken(tokenString) {
    if (!currentUser) return;

    try {
        const res = await fetch('/api/attendance/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                token: tokenString,
                student_id: currentUser.user_id
            })
        });

        const data = await res.json();

        if (data.success) {
            if (data.already_marked) {
                showToast(data.message, 'info');
            } else {
                playSuccessBeep();
                if (typeof confetti === 'function') {
                    confetti({ particleCount: 100, spread: 70, origin: { y: 0.5 } });
                }
                showToast(`🎉 ${data.message}`, 'success');
            }
            // Auto reload student records & percentages
            await loadStudentData();
        } else {
            showToast(data.message || 'Failed to record attendance', 'error');
        }
    } catch (err) {
        showToast('Network error while recording attendance', 'error');
    }
}

// ============================================================== //
// TEACHER VIEW LOGIC
// ============================================================== //

async function loadTeacherData() {
    if (!currentUser || currentUser.role !== 'teacher') return;

    // Load teacher's courses
    try {
        const res = await fetch(`/api/courses?teacher_id=${currentUser.user_id}`);
        const courses = await res.json();

        // Populate Session Creator course select and Enroll check group
        const sessionCourseSelect = document.getElementById('sessionCourseSelect');
        const reportCourseSelect = document.getElementById('reportCourseSelect');
        const enrollGroup = document.getElementById('enrollCoursesCheckboxGroup');

        sessionCourseSelect.innerHTML = '';
        reportCourseSelect.innerHTML = '';
        if (enrollGroup) enrollGroup.innerHTML = '';

        courses.forEach(c => {
            const opt1 = document.createElement('option');
            opt1.value = c.id;
            opt1.textContent = `${c.code} - ${c.name}`;
            sessionCourseSelect.appendChild(opt1);

            const opt2 = document.createElement('option');
            opt2.value = c.id;
            opt2.textContent = `${c.code} - ${c.name}`;
            reportCourseSelect.appendChild(opt2);

            if (enrollGroup) {
                const label = document.createElement('label');
                label.className = "flex items-center gap-2 text-xs text-slate-700 font-medium cursor-pointer hover:text-slate-900";
                label.innerHTML = `
                    <input type="checkbox" name="enrollCourse" value="${c.id}" checked class="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500">
                    <span>${c.code} (${c.name})</span>
                `;
                enrollGroup.appendChild(label);
            }
        });

        // Load active sessions
        await loadActiveSessions();

        // Load students directory
        await loadStudentsDirectory();

        // Load report for first course
        if (courses.length > 0) {
            loadCourseReport(courses[0].id);
        }

    } catch (err) {
        console.error('Failed to load teacher data:', err);
    }
}

async function loadActiveSessions() {
    try {
        const res = await fetch(`/api/sessions/active?teacher_id=${currentUser.user_id}`);
        const sessions = await res.json();

        const dropdown = document.getElementById('activeSessionsDropdown');
        dropdown.innerHTML = '';

        if (sessions.length === 0) {
            dropdown.innerHTML = '<option value="">No active sessions right now</option>';
            return;
        }

        sessions.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `${s.course_code}: ${s.title} (${s.session_code})`;
            dropdown.appendChild(opt);
        });

        // Auto select first session to display QR
        if (!activeLiveSessionId && sessions.length > 0) {
            activeLiveSessionId = sessions[0].id;
        }

        if (activeLiveSessionId) {
            dropdown.value = activeLiveSessionId;
            loadSessionLiveData(activeLiveSessionId);
        }

    } catch (err) {
        console.error('Failed to load active sessions:', err);
    }
}

async function handleCreateSession(e) {
    e.preventDefault();
    const courseId = document.getElementById('sessionCourseSelect').value;
    const title = document.getElementById('sessionTitleInput').value.trim();
    const duration = document.getElementById('sessionDurationSelect').value;

    try {
        const res = await fetch('/api/sessions/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_id: courseId,
                title: title,
                duration_minutes: duration
            })
        });

        const data = await res.json();
        if (data.success) {
            showToast('New Attendance Session Started!', 'success');
            activeLiveSessionId = data.session.id;
            await loadActiveSessions();
            loadSessionLiveData(activeLiveSessionId);
        } else {
            showToast(data.error || 'Failed to start session', 'error');
        }
    } catch (err) {
        showToast('Error starting session', 'error');
    }
}

async function loadSessionLiveData(sessionId) {
    if (!sessionId) return;
    activeLiveSessionId = sessionId;

    try {
        const res = await fetch(`/api/sessions/${sessionId}/live`);
        if (!res.ok) return;
        const data = await res.json();

        // Update Session Banner
        document.getElementById('liveCourseCodeBadge').textContent = data.session.course_code;
        document.getElementById('liveSessionTitle').textContent = data.session.title;
        document.getElementById('liveSessionCodeDisplay').textContent = data.session.session_code;

        // QR Image
        const qrUrl = `/api/sessions/${sessionId}/qr.png?t=${Date.now()}`;
        document.getElementById('qrImageElement').src = qrUrl;

        // Projector QR
        document.getElementById('projQrImage').src = qrUrl;
        document.getElementById('projCourseBadge').textContent = data.session.course_code;
        document.getElementById('projSessionTitle').textContent = data.session.title;
        document.getElementById('projSessionCode').textContent = data.session.session_code;
        document.getElementById('projTurnout').textContent = `${data.present_count} / ${data.total_enrolled}`;

        // Counts
        document.getElementById('livePresentCount').textContent = data.present_count;
        document.getElementById('liveTotalCount').textContent = `/ ${data.total_enrolled} Enrolled`;
        document.getElementById('liveTurnoutPct').textContent = `${data.attendance_percentage}%`;

        // Active Status & Toggle button
        const toggleBtn = document.getElementById('toggleSessionBtn');
        const statusTime = document.getElementById('liveSessionTimeRemaining');

        if (data.session.is_active === 1 && !data.is_expired) {
            toggleBtn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 transition-all";
            toggleBtn.innerHTML = '<i class="fa-solid fa-stop mr-1"></i> Close Session';
            statusTime.innerHTML = `<span class="text-emerald-600 font-bold"><i class="fa-solid fa-circle text-[8px] mr-1"></i> Active</span> &bull; Expires at ${formatTimeOnly(data.session.expires_at)}`;
        } else {
            toggleBtn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-all";
            toggleBtn.innerHTML = '<i class="fa-solid fa-play mr-1"></i> Reopen Session';
            statusTime.innerHTML = `<span class="text-rose-600 font-bold"><i class="fa-solid fa-circle text-[8px] mr-1"></i> Closed / Ended</span>`;
        }

        // Live attendees chips
        const attendeesContainer = document.getElementById('liveAttendeesList');
        attendeesContainer.innerHTML = '';

        const presentStudents = data.roster.filter(s => s.status === 'present');
        if (presentStudents.length === 0) {
            attendeesContainer.innerHTML = `<span class="text-xs text-slate-400 italic">No students scanned yet. Display the QR code for students to scan.</span>`;
        } else {
            presentStudents.forEach(s => {
                const chip = document.createElement('div');
                chip.className = "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold animate-in fade-in";
                chip.innerHTML = `
                    <i class="fa-solid fa-circle-check text-emerald-600 text-[10px]"></i>
                    <span>${s.name} (${s.user_id})</span>
                    <span class="text-[10px] text-emerald-600 font-normal ml-1">${formatTimeOnly(s.scan_time)}</span>
                `;
                attendeesContainer.appendChild(chip);
            });
        }

        // Also update Manual Roster table
        manualRosterState = data.roster.map(r => ({ ...r }));
        renderManualRosterTable();

    } catch (err) {
        console.error('Error fetching live session data:', err);
    }

    // Start auto polling if not running
    if (!livePollInterval) {
        livePollInterval = setInterval(() => {
            if (activeLiveSessionId && currentRole === 'teacher') {
                loadSessionLiveData(activeLiveSessionId);
            }
        }, 3000);
    }
}

async function toggleActiveSessionStatus() {
    if (!activeLiveSessionId) return;

    try {
        const res = await fetch(`/api/sessions/${activeLiveSessionId}/toggle`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(data.is_active ? 'Session Reopened' : 'Session Ended / Closed', 'info');
            loadSessionLiveData(activeLiveSessionId);
        }
    } catch (err) {
        showToast('Failed to update session status', 'error');
    }
}

function copySessionCode() {
    const code = document.getElementById('liveSessionCodeDisplay').textContent.trim();
    navigator.clipboard.writeText(code).then(() => {
        showToast(`Copied code: ${code}`, 'success');
    });
}

function openProjectorModal() {
    document.getElementById('projectorModal').classList.remove('hidden');
}

function closeProjectorModal() {
    document.getElementById('projectorModal').classList.add('hidden');
}

// ---------------- Teacher Sub Tabs ---------------- //

function switchTeacherTab(tabName) {
    const tabs = [
        { id: 'live_qr', view: 'teacherSubViewLiveQR', btn: 'teacherTabLiveQR' },
        { id: 'manual', view: 'teacherSubViewManual', btn: 'teacherTabManual' },
        { id: 'students', view: 'teacherSubViewStudents', btn: 'teacherTabStudents' },
        { id: 'reports', view: 'teacherSubViewReports', btn: 'teacherTabReports' }
    ];

    tabs.forEach(t => {
        const view = document.getElementById(t.view);
        const btn = document.getElementById(t.btn);
        if (!view || !btn) return;

        if (t.id === tabName) {
            view.classList.remove('hidden');
            btn.className = "pb-3 text-sm font-bold text-indigo-600 border-b-2 border-indigo-600 flex items-center gap-2 whitespace-nowrap";
        } else {
            view.classList.add('hidden');
            btn.className = "pb-3 text-sm font-semibold text-slate-500 hover:text-slate-800 border-b-2 border-transparent flex items-center gap-2 whitespace-nowrap";
        }
    });

    if (tabName === 'reports') {
        const sel = document.getElementById('reportCourseSelect');
        if (sel.value) loadCourseReport(sel.value);
    } else if (tabName === 'students') {
        loadStudentsDirectory();
    }
}

// ---------------- Student Management (Add / Directory) ---------------- //

let allDirectoryStudents = [];

async function loadStudentsDirectory() {
    try {
        const res = await fetch('/api/students');
        if (!res.ok) return;
        allDirectoryStudents = await res.json();

        // Update count badge
        const countBadge = document.getElementById('directoryStudentCount');
        if (countBadge) countBadge.textContent = `${allDirectoryStudents.length} Students`;

        renderStudentsDirectory(allDirectoryStudents);
    } catch (err) {
        console.error('Failed to load students directory:', err);
    }
}

function renderStudentsDirectory(students) {
    const tbody = document.getElementById('studentsDirectoryTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!students || students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="px-5 py-6 text-center text-slate-400">No students found.</td></tr>`;
        return;
    }

    students.forEach(s => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50/80 transition-colors";

        const coursesStr = s.enrolled_courses_str || 'All Active';

        tr.innerHTML = `
            <td class="px-4 py-3 font-semibold text-slate-900">${s.user_id}</td>
            <td class="px-4 py-3 font-bold text-slate-800">${s.name}</td>
            <td class="px-4 py-3 text-slate-500">${s.email}</td>
            <td class="px-4 py-3 text-slate-600">${s.department}</td>
            <td class="px-4 py-3">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                    ${coursesStr}
                </span>
            </td>
            <td class="px-4 py-3 text-center">
                <button onclick="handleDeleteStudent('${s.user_id}', '${s.name}')" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all" title="Remove Student">
                    <i class="fa-regular fa-trash-can"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterStudentsDirectory(query) {
    const q = query.toLowerCase().trim();
    if (!q) {
        renderStudentsDirectory(allDirectoryStudents);
        return;
    }
    const filtered = allDirectoryStudents.filter(s => 
        s.user_id.toLowerCase().includes(q) || 
        s.name.toLowerCase().includes(q) ||
        s.email.toLowerCase().includes(q) ||
        s.department.toLowerCase().includes(q)
    );
    renderStudentsDirectory(filtered);
}

async function handleAddStudent(e) {
    e.preventDefault();

    const roll = document.getElementById('newStudentRoll').value.trim().toUpperCase();
    const name = document.getElementById('newStudentName').value.trim();
    const email = document.getElementById('newStudentEmail').value.trim().toLowerCase();
    const dept = document.getElementById('newStudentDept').value.trim();

    // Checked courses
    const checkedBoxes = document.querySelectorAll('input[name="enrollCourse"]:checked');
    const courseIds = Array.from(checkedBoxes).map(cb => parseInt(cb.value));

    const submitBtn = document.getElementById('addStudentSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Registering...`;

    try {
        const res = await fetch('/api/students/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: roll,
                name: name,
                email: email,
                department: dept,
                course_ids: courseIds
            })
        });

        const data = await res.json();

        if (data.success) {
            showToast(`🎉 ${data.message}`, 'success');
            // Reset form
            document.getElementById('addStudentForm').reset();
            document.getElementById('newStudentDept').value = 'Computer Science';

            // Refresh user selector at the top so teacher can switch to this student immediately!
            await loadUsers();
            // Refresh student directory
            await loadStudentsDirectory();

            // Refresh active live session roster if open
            if (activeLiveSessionId) {
                loadSessionLiveData(activeLiveSessionId);
            }
        } else {
            showToast(data.message || 'Failed to add student', 'error');
        }
    } catch (err) {
        showToast('Network error while adding student', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i class="fa-solid fa-plus"></i> <span>Register Student</span>`;
    }
}

async function handleDeleteStudent(userId, userName) {
    if (!confirm(`Are you sure you want to remove student "${userName}" (${userId})? This will also remove their attendance history.`)) {
        return;
    }

    try {
        const res = await fetch(`/api/students/${userId}`, { method: 'DELETE' });
        const data = await res.json();

        if (data.success) {
            showToast(data.message, 'info');
            await loadUsers();
            await loadStudentsDirectory();
            if (activeLiveSessionId) {
                loadSessionLiveData(activeLiveSessionId);
            }
        } else {
            showToast(data.message || 'Failed to remove student', 'error');
        }
    } catch (err) {
        showToast('Network error removing student', 'error');
    }
}

// ---------------- Manual Attendance Roster ---------------- //

function renderManualRosterTable() {
    const tbody = document.getElementById('manualRosterTableBody');
    tbody.innerHTML = '';

    manualRosterState.forEach((r, idx) => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50/80 transition-colors";

        const isPresent = r.status === 'present';
        const isLate = r.status === 'late';
        const isAbsent = r.status === 'absent';

        tr.innerHTML = `
            <td class="px-5 py-3 font-semibold text-slate-900">${r.user_id}</td>
            <td class="px-5 py-3">
                <div class="font-bold text-slate-800">${r.name}</div>
                <div class="text-[11px] text-slate-400">${r.email}</div>
            </td>
            <td class="px-5 py-3 text-slate-500">${r.scan_time ? formatTimeOnly(r.scan_time) : '-'}</td>
            <td class="px-5 py-3 text-slate-500 capitalize">${r.method || 'Manual'}</td>
            <td class="px-5 py-3 text-center">
                <div class="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-100">
                    <button onclick="setRosterStatus(${idx}, 'present')" class="px-3 py-1 rounded-md text-xs font-bold transition-all ${isPresent ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-600 hover:text-emerald-700'}">
                        Present
                    </button>
                    <button onclick="setRosterStatus(${idx}, 'absent')" class="px-3 py-1 rounded-md text-xs font-bold transition-all ${isAbsent ? 'bg-rose-600 text-white shadow-sm' : 'text-slate-600 hover:text-rose-700'}">
                        Absent
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function setRosterStatus(index, newStatus) {
    if (manualRosterState[index]) {
        manualRosterState[index].status = newStatus;
        renderManualRosterTable();
    }
}

function markAllCurrent(present) {
    const targetStatus = present ? 'present' : 'absent';
    manualRosterState.forEach(r => r.status = targetStatus);
    renderManualRosterTable();
    showToast(`Marked all students as ${targetStatus}`, 'info');
}

async function saveManualBatchChanges() {
    if (!activeLiveSessionId) {
        showToast('No active session selected', 'error');
        return;
    }

    const records = manualRosterState.map(r => ({
        student_id: r.user_id,
        status: r.status
    }));

    try {
        const res = await fetch('/api/attendance/batch-update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: activeLiveSessionId,
                records: records
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Attendance register successfully saved!', 'success');
            loadSessionLiveData(activeLiveSessionId);
        } else {
            showToast(data.error || 'Failed to update', 'error');
        }
    } catch (err) {
        showToast('Error saving changes', 'error');
    }
}

// ---------------- Reports & Analytics ---------------- //

async function loadCourseReport(courseId) {
    if (!courseId) return;

    try {
        const res = await fetch(`/api/reports/course/${courseId}`);
        if (!res.ok) return;
        const data = await res.json();

        // Update KPIs
        document.getElementById('reportTotalLectures').textContent = data.total_sessions;
        document.getElementById('reportAvgAttendance').textContent = `${data.average_attendance}%`;
        document.getElementById('reportLowCount').textContent = `${data.low_attendance_count} Student${data.low_attendance_count === 1 ? '' : 's'}`;

        // Export CSV Link
        document.getElementById('exportCsvBtn').href = `/api/reports/course/${courseId}/export-csv`;

        // Render Roster Table
        const tbody = document.getElementById('reportTableBody');
        tbody.innerHTML = '';

        data.students.forEach(s => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-50/80 transition-colors";

            const isLow = s.is_low;
            const badgeClass = isLow ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800';
            const progressColor = isLow ? 'bg-rose-500' : 'bg-emerald-500';

            tr.innerHTML = `
                <td class="px-5 py-3 font-semibold text-slate-900">${s.user_id}</td>
                <td class="px-5 py-3">
                    <div class="font-bold text-slate-800">${s.name}</div>
                    <div class="text-[11px] text-slate-400">${s.email}</div>
                </td>
                <td class="px-5 py-3 font-semibold text-slate-700">${s.attended} / ${s.total_sessions}</td>
                <td class="px-5 py-3 text-slate-500">${s.absent}</td>
                <td class="px-5 py-3 font-extrabold ${isLow ? 'text-rose-600' : 'text-slate-900'}">${s.percentage}%</td>
                <td class="px-5 py-3 w-36">
                    <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div class="${progressColor} h-2 rounded-full" style="width: ${s.percentage}%"></div>
                    </div>
                </td>
                <td class="px-5 py-3">
                    <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${badgeClass}">
                        <i class="${isLow ? 'fa-solid fa-triangle-exclamation' : 'fa-solid fa-check'}"></i>
                        ${s.status}
                    </span>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error('Failed to load course report:', err);
    }
}

// ============================================================== //
// UTILITY FUNCTIONS
// ============================================================== //

function formatDateTime(dtStr) {
    if (!dtStr) return '-';
    try {
        const d = new Date(dtStr.replace(' ', 'T'));
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        return dtStr;
    }
}

function formatTimeOnly(dtStr) {
    if (!dtStr) return '-';
    try {
        const d = new Date(dtStr.replace(' ', 'T'));
        return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        return dtStr;
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');

    const colors = {
        success: 'bg-emerald-600 text-white',
        error: 'bg-rose-600 text-white',
        info: 'bg-slate-900 text-white'
    };

    const icons = {
        success: 'fa-circle-check',
        error: 'fa-triangle-exclamation',
        info: 'fa-circle-info'
    };

    toast.className = `${colors[type] || colors.info} px-4 py-3 rounded-xl shadow-xl flex items-center gap-3 text-xs font-semibold pointer-events-auto transform transition-all duration-300 translate-y-2 opacity-0`;
    toast.innerHTML = `
        <i class="fa-solid ${icons[type] || icons.info} text-sm"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    // Dismiss after 4s
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
