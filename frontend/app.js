/* app.js – Phiên bản hoàn chỉnh, đã sửa lỗi nút xóa đề thi và phân quyền */

let currentUser = null;
let currentPage = 'dashboard';

// ── KHỞI ĐỘNG ────────────────────────────────────────────────────────────────
(async function init() {
  const token = sessionStorage.getItem('access_token');
  if (!token) return (window.location.href = 'login.html');
  try {
    currentUser = await getMe();
    sessionStorage.setItem('user_info', JSON.stringify(currentUser));
    renderUserInfo();
    renderSidebar();
    navigateTo('dashboard');
  } catch { logout(); }
})();

function logout() { sessionStorage.clear(); window.location.href = 'login.html'; }

function renderUserInfo() {
  document.getElementById('display-name').textContent = currentUser.ho_ten;
  const roleMap = { admin: 'Quản trị viên', giao_vien: 'Giáo viên', hoc_sinh: 'Học sinh' };
  document.getElementById('display-role').textContent = roleMap[currentUser.vai_tro] || currentUser.vai_tro;
  document.getElementById('avatar-letter').textContent = currentUser.ho_ten.charAt(0).toUpperCase();
}

// ── SIDEBAR ───────────────────────────────────────────────────────────────────
function renderSidebar() {
  const role = currentUser.vai_tro;
  const nav  = document.getElementById('sidebar-nav');
  const items = [];

  items.push({ section: 'Tổng quan' });
  items.push({ icon: '🏠', label: 'Dashboard', page: 'dashboard' });

  if (role === 'hoc_sinh') {
    items.push({ section: 'Học & Thi' });
    items.push({ icon: '📋', label: 'Đề thi', page: 'exams' });
    items.push({ icon: '📊', label: 'Lịch sử làm bài', page: 'my-history' });
  }

  if (role === 'giao_vien' || role === 'admin') {
    items.push({ section: 'Nội dung' });
    items.push({ icon: '📚', label: 'Môn học & Chủ đề', page: 'subjects' });
    items.push({ icon: '❓', label: 'Ngân hàng câu hỏi', page: 'questions' });
    items.push({ icon: '📝', label: 'Đề thi', page: 'exams' });
    items.push({ section: 'Thống kê' });
    items.push({ icon: '📈', label: 'Báo cáo', page: 'reports' });
  }

  if (role === 'admin') {
    items.push({ section: 'Quản trị' });
    items.push({ icon: '👥', label: 'Người dùng', page: 'users' });
    items.push({ icon: '📥', label: 'Import tài khoản', page: 'import-users' });
  }

  items.push({ section: 'Tài khoản' });
  items.push({ icon: '🔒', label: 'Đổi mật khẩu', page: 'change-password' });

  nav.innerHTML = items.map(it => {
    if (it.section) return `<div class="nav-section">${it.section}</div>`;
    return `<div class="nav-item" id="nav-${it.page}" onclick="navigateTo('${it.page}')">
              <span class="icon">${it.icon}</span>${it.label}</div>`;
  }).join('');
}

// ── ĐIỀU HƯỚNG ────────────────────────────────────────────────────────────────
function navigateTo(page) {
  currentPage = page;
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const nav = document.getElementById(`nav-${page}`);
  if (nav) nav.classList.add('active');

  const titles = {
    dashboard: 'Tổng quan', subjects: 'Môn học & Chủ đề',
    questions: 'Ngân hàng câu hỏi', exams: 'Quản lý đề thi',
    reports: 'Thống kê & Báo cáo', 'my-history': 'Lịch sử làm bài',
    users: 'Quản lý người dùng',
    'change-password': 'Đổi mật khẩu', 'import-users': 'Import tài khoản hàng loạt',
  };
  document.getElementById('page-title').textContent = titles[page] || page;
  document.getElementById('page-breadcrumb').textContent = `Trang chủ / ${titles[page] || page}`;

  const renders = {
    dashboard: renderDashboard,
    subjects: renderSubjects,
    questions: renderQuestions,
    exams: renderExams,
    reports: renderReports,
    'my-history': renderMyHistory,
    users: renderUsers,
    'change-password': () => showChangePasswordModal(),
    'import-users': renderImportUsers,
  };
  if (renders[page]) renders[page]();
}

function setBody(html) { document.getElementById('page-body').innerHTML = html; }
function loading() { setBody(`<div class="loading"><div class="spinner"></div> Đang tải...</div>`); }

// ── DASHBOARD ─────────────────────────────────────────────────────────────────
async function renderDashboard() {
  loading();
  try {
    const [subjects, questions, exams] = await Promise.all([
      getSubjects(), getQuestions(), getExams()
    ]);
    const role = currentUser.vai_tro;

    let statsHtml = '';
    if (role !== 'hoc_sinh') {
      statsHtml = `<div class="stats-grid">
        <div class="stat-card"><div class="stat-icon blue">📚</div><div class="stat-info"><strong>${subjects.length}</strong><span>Môn học</span></div></div>
        <div class="stat-card"><div class="stat-icon green">❓</div><div class="stat-info"><strong>${questions.length}</strong><span>Câu hỏi</span></div></div>
        <div class="stat-card"><div class="stat-icon yellow">📝</div><div class="stat-info"><strong>${exams.length}</strong><span>Đề thi</span></div></div>
      </div>`;
    } else {
      const published = exams.filter(e => e.cong_bo);
      statsHtml = `<div class="stats-grid">
        <div class="stat-card"><div class="stat-icon yellow">📝</div><div class="stat-info"><strong>${published.length}</strong><span>Đề thi đang mở</span></div></div>
      </div>`;
    }

    const examRows = exams.slice(0, 5).map(e => `<tr>
      <td>${e.tieu_de}</td>
      <td>${e.thoi_gian_lam_bai} phút</td>
      <td><span class="badge ${e.cong_bo ? 'badge-green' : 'badge-gray'}">${e.cong_bo ? 'Công bố' : 'Nháp'}</span></td>
      <td>${role !== 'hoc_sinh'
        ? `<button class="btn btn-sm btn-outline" onclick="navigateTo('exams')">Xem</button>`
        : e.cong_bo ? `<button class="btn btn-sm btn-primary" onclick="startQuiz(${e.id})">Làm bài</button>` : ''}</td>
    </tr>`).join('');

    setBody(`${statsHtml}
      <div class="card">
        <div class="card-header"><h3>📋 Đề thi gần đây</h3>
          <button class="btn btn-sm btn-outline" onclick="navigateTo('exams')">Xem tất cả</button></div>
        <table><thead><tr><th>Tên đề thi</th><th>Thời gian</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
        <tbody>${examRows || '<tr><td colspan="4" class="text-center text-muted" style="padding:30px">Chưa có đề thi</td>'}</tbody>
      </table>
      </div>`);
  } catch (err) { setBody(`<div class="alert alert-error">Lỗi: ${err.message}</div>`); }
}

// ── IMPORT TÀI KHOẢN (ADMIN) ─────────────────────────────────────────────────
function renderImportUsers() {
  setBody(`
    <div class="card" style="max-width:700px;margin:0 auto">
      <div class="card-header">
        <h3>📥 Import tài khoản sinh viên từ Excel</h3>
      </div>
      <div class="card-body">
        <div class="alert alert-info">
          <strong>📌 Hướng dẫn:</strong>
          <ul style="margin-top:8px;margin-left:20px">
            <li>Tải file mẫu, điền thông tin sinh viên</li>
            <li>File bắt buộc có các cột: <strong>Mã sinh viên, Họ và tên, Lớp, Ngày sinh (dd/mm/yyyy)</strong></li>
            <li>Mật khẩu mặc định là <strong>Ngày sinh</strong> (định dạng dd/mm/yyyy)</li>
            <li>Sinh viên sẽ bắt buộc đổi mật khẩu lần đầu khi đăng nhập</li>
          </ul>
        </div>
        <div class="form-group">
          <button class="btn btn-outline" onclick="downloadAdminTemplate()">⬇ Tải file mẫu Excel</button>
        </div>
        <div class="form-group">
          <label>Chọn file Excel (.xlsx)</label>
          <input type="file" id="import-user-file" accept=".xlsx,.xls" style="padding:8px;border:1.5px solid var(--border);border-radius:8px;width:100%">
        </div>
        <div id="import-user-result"></div>
        <button class="btn btn-primary btn-full" onclick="doImportUsers()">📤 Import & Tạo tài khoản</button>
      </div>
    </div>
  `);
}

async function doImportUsers() {
  const file = document.getElementById('import-user-file').files[0];
  if (!file) {
    document.getElementById('import-user-result').innerHTML = '<div class="alert alert-error">Vui lòng chọn file Excel</div>';
    return;
  }
  document.getElementById('import-user-result').innerHTML = '<div class="loading"><div class="spinner"></div> Đang xử lý...</div>';
  try {
    await importUsersExcel(file);
    document.getElementById('import-user-result').innerHTML = '<div class="alert alert-success">✅ Import thành công! File báo cáo đã được tải xuống.</div>';
    document.getElementById('import-user-file').value = '';
    renderUsers();
  } catch (err) {
    document.getElementById('import-user-result').innerHTML = `<div class="alert alert-error">❌ Lỗi: ${err.message}</div>`;
  }
}

// ── LÀM BÀI THI (CÓ GIÁM SÁT TAB) ──────────────────────────────────────────
let currentAttempt = null;
let quizAnswers = {};
let quizTimer = null;
let tabViolations = 0;
let timeLeftGlobal = 0;
const MAX_VIOLATIONS = 3;

async function startQuiz(examId) {
  loading();
  const attempt = await startAttempt(examId);
  const examData = await getExamQuestions(examId);
  currentAttempt = attempt;
  quizAnswers = {};
  tabViolations = 0;

  document.addEventListener('visibilitychange', handleVisibilityChange);
  renderQuizPage(examData);
}

let pauseStart = null;

function handleVisibilityChange() {
  if (!currentAttempt) return;
  if (document.hidden) {
    pauseStart = Date.now();
    clearInterval(quizTimer);
    tabViolations++;
    monitorEvent(currentAttempt.id, 'thoat_tab', `Lần ${tabViolations}: Rời khỏi tab thi`).then(res => {
      if (res && res.nop_tu_dong) {
        document.removeEventListener('visibilitychange', handleVisibilityChange);
        const answers = Object.entries(quizAnswers).map(([cau_hoi_id, lua_chon_id]) => ({
          cau_hoi_id: parseInt(cau_hoi_id), lua_chon_id
        }));
        submitAttempt(currentAttempt.id, answers, true).then(result => {
          showResult(result, true);
        });
      }
    });
  } else {
    if (pauseStart !== null) {
      pauseStart = null;
    }
    monitorEvent(currentAttempt.id, 'quay_lai', 'Quay lại tab thi');
    resumeTimer();
  }
}

function resumeTimer() {
  clearInterval(quizTimer);
  quizTimer = setInterval(() => {
    if (document.hidden) return;
    timeLeftGlobal--;
    const el = document.getElementById('quiz-timer');
    if (el) {
      const m = String(Math.floor(timeLeftGlobal / 60)).padStart(2, '0');
      const s = String(timeLeftGlobal % 60).padStart(2, '0');
      el.textContent = `${m}:${s}`;
      if (timeLeftGlobal <= 60) el.style.color = '#e74c3c';
    }
    if (timeLeftGlobal <= 0) {
      clearInterval(quizTimer);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      doSubmit(true);
    }
  }, 1000);
}

function renderQuizPage(examData) {
  let timeLeft = examData.thoi_gian_lam_bai * 60;
  const minTime = Math.floor(examData.thoi_gian_lam_bai * 0.5);

  const questionsHtml = examData.danh_sach_cau_hoi.map((q, idx) => {
    const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
    const choices = q.lua_chon.map((lc, i) => `
      <div class="choice-item ${quizAnswers[q.cau_hoi_id] === lc.id ? 'selected' : ''}"
           onclick="selectAnswer(${q.cau_hoi_id}, ${lc.id}, this)">
        <div class="choice-letter">${letters[i]}</div>
        <div>${lc.noi_dung}</div>
      </div>`).join('');
    return `<div class="question-card" id="qcard-${q.cau_hoi_id}">
      <div class="question-number">Câu ${idx + 1} / ${examData.tong_so_cau}</div>
      <div class="question-text">${q.noi_dung}</div>
      <div class="choices">${choices}</div>
    </div>`;
  }).join('');

  setBody(`
    <div class="quiz-container">
      ${tabViolations > 0 ? `<div class="alert alert-error">
        ⚠️ Bạn đã thoát tab ${tabViolations}/${MAX_VIOLATIONS} lần. Vượt quá ${MAX_VIOLATIONS} lần sẽ bị nộp bài tự động!
      </div>` : ''}
      <div class="quiz-header">
        <div>
          <strong style="font-size:16px">${examData.tieu_de}</strong>
          <div style="font-size:12px;opacity:.7;margin-top:4px">
            Đã trả lời: <span id="answered-count">0</span>/${examData.tong_so_cau} câu
          </div>
          <div class="quiz-progress">
            <div class="quiz-progress-bar" id="progress-bar" style="width:0%"></div>
          </div>
        </div>
        <div>
          <div style="font-size:11px;opacity:.6;text-align:center;margin-bottom:4px">Thời gian còn</div>
          <div class="quiz-timer" id="quiz-timer">--:--</div>
          <div style="font-size:10px;text-align:center;color:rgba(255,255,255,0.5);margin-top:4px">
            Nộp sớm nhất sau ${minTime} phút
          </div>
        </div>
      </div>
      ${questionsHtml}
      <div style="text-align:center;padding:20px 0">
        <button class="btn btn-success" id="btn-submit"
                style="padding:12px 32px;font-size:15px" onclick="confirmSubmit()">
          ✅ Nộp bài
        </button>
      </div>
    </div>
  `);

  updateProgress(examData.tong_so_cau);
  timeLeftGlobal = timeLeft;
  clearInterval(quizTimer);
  quizTimer = setInterval(() => {
    if (document.hidden) return;
    timeLeftGlobal--;
    const el = document.getElementById('quiz-timer');
    if (el) {
      const m = String(Math.floor(timeLeftGlobal / 60)).padStart(2, '0');
      const s = String(timeLeftGlobal % 60).padStart(2, '0');
      el.textContent = `${m}:${s}`;
      if (timeLeftGlobal <= 60) el.style.color = '#e74c3c';
    }
    if (timeLeftGlobal <= 0) {
      clearInterval(quizTimer);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      doSubmit(true);
    }
  }, 1000);
}

function updateProgress(total) {
  const answered = Object.keys(quizAnswers).length;
  const el = document.getElementById('answered-count');
  const pb = document.getElementById('progress-bar');
  if (el) el.textContent = answered;
  if (pb) pb.style.width = `${(answered / total) * 100}%`;
}

function selectAnswer(questionId, choiceId, el) {
  el.closest('.choices').querySelectorAll('.choice-item').forEach(c => {
    c.classList.remove('selected');
  });
  el.classList.add('selected');
  quizAnswers[questionId] = choiceId;
  const total = document.querySelectorAll('.question-card').length;
  updateProgress(total);
}

function confirmSubmit() {
  const total = document.querySelectorAll('.question-card').length;
  const answered = Object.keys(quizAnswers).length;
  if (answered < total) {
    alert(`⚠️ Bạn còn ${total - answered} câu chưa trả lời!\nPhải hoàn thành tất cả ${total} câu trước khi nộp bài.`);
    document.querySelectorAll('.question-card').forEach(card => {
      const qid = parseInt(card.id.replace('qcard-', ''));
      if (!quizAnswers[qid]) {
        card.style.border = '2px solid var(--danger)';
        card.style.borderRadius = '10px';
      } else {
        card.style.border = '';
      }
    });
    return;
  }
  if (!confirm('Bạn có chắc muốn nộp bài?')) return;
  doSubmit(false);
}

async function doSubmit(auto = false) {
  const submitBtn = document.getElementById('btn-submit');
  if (submitBtn) submitBtn.disabled = true;

  const answers = Object.entries(quizAnswers).map(([cau_hoi_id, lua_chon_id]) => ({
    cau_hoi_id: parseInt(cau_hoi_id), lua_chon_id
  }));
  try {
    const result = await submitAttempt(currentAttempt.id, answers, auto);
    clearInterval(quizTimer);
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    showResult(result, auto);
  } catch (err) {
    alert('❌ ' + err.message);
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function showResult(result, auto = false) {
  const detail = await getAttemptResult(result.id);
  const pass = result.dat_yeu_cau;

  const detailRows = detail.chi_tiet_tung_cau.map((item, i) => `
    <div class="question-card">
      <div class="question-number">Câu ${i + 1}</div>
      <div class="question-text" style="font-size:14px">${item.noi_dung_cau_hoi}</div>
      <div style="margin-top:8px">
        <div class="choice-item ${item.dung ? 'correct' : 'wrong'}">
          <div class="choice-letter">${item.dung ? '✓' : '✗'}</div>
          <div>Bạn chọn: <strong>${item.lua_chon_da_chon || 'Không trả lời'}</strong></div>
        </div>
        ${!item.dung && item.dap_an_dung ? `
          <div class="choice-item correct" style="margin-top:6px">
            <div class="choice-letter">✓</div>
            <div>Đáp án đúng: <strong>${item.dap_an_dung}</strong></div>
          </div>` : ''}
      </div>
      ${item.giai_thich ? `<div class="explanation-box">💡 ${item.giai_thich}</div>` : ''}
    </div>`).join('');

  setBody(`
    <div class="quiz-container">
      ${auto ? `<div class="alert alert-error" style="margin-bottom:16px">
        ⚠️ Bài thi đã bị nộp tự động do bạn thoát tab quá ${MAX_VIOLATIONS} lần.
      </div>` : ''}
      <div class="card" style="overflow:hidden;margin-bottom:20px">
        <div class="result-header">
          <div class="result-score">${result.tong_diem ?? 0}<small>/10</small></div>
          <div class="result-status ${pass ? 'pass' : 'fail'}">${pass ? '🎉 Đạt yêu cầu!' : '😔 Chưa đạt. Hãy thử lại!'}</div>
          ${result.so_lan_thoat_tab > 0 ? `<div style="margin-top:8px;font-size:13px;color:rgba(255,255,255,0.7)">Vi phạm thoát tab: ${result.so_lan_thoat_tab} lần</div>` : ''}
        </div>
        <div class="card-body text-center">
          <button class="btn btn-primary" onclick="navigateTo('exams')">← Quay lại đề thi</button>
          <button class="btn btn-outline" style="margin-left:8px" onclick="navigateTo('my-history')">Lịch sử</button>
        </div>
      </div>
      <h3 style="margin-bottom:12px;color:var(--primary)">📋 Chi tiết từng câu</h3>
      ${detailRows}
    </div>`);
}

// ── MÔN HỌC & CHỦ ĐỀ (ĐÃ SỬA LỖI HIỂN THỊ) ─────────────────────────────────
async function renderSubjects() {
  loading();
  const [subjects, topics] = await Promise.all([getSubjects(), getTopics()]);

  const subjectRows = subjects.map(s => `<tr>
    <td><strong>${s.ten_mon}</strong></td>
    <td><span class="badge badge-blue">${s.ma_mon}</span></td>
    <td>${s.mo_ta || '<span class="text-muted">–</span>'}</td>
    <td>${topics.filter(t => t.mon_hoc_id === s.id).length}</td>
    <td><button class="btn btn-sm btn-danger" onclick="deleteSubjectAction(${s.id})">🗑</button></td>
  </tr>`).join('');

  const topicRows = topics.map(t => {
    const mon = subjects.find(s => s.id === t.mon_hoc_id);
    return `<tr>
      <td><strong>${t.ten_chu_de}</strong></td>
      <td>${mon ? `<span class="badge badge-blue">${mon.ma_mon}</span>` : '<span class="text-muted">–</span>'}</td>
      <td>${t.mo_ta || '<span class="text-muted">–</span>'}</td>
    </tr>`;
  }).join('');

  setBody(`
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <div class="card">
        <div class="card-header">
          <h3>📚 Môn học (${subjects.length})</h3>
          <button class="btn btn-sm btn-primary" onclick="showAddSubjectModal()">+ Thêm môn</button>
        </div>
        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr><th>Tên môn</th><th>Mã</th><th>Mô tả</th><th>Chủ đề</th><th></th></tr>
            </thead>
            <tbody>${subjectRows || '<tr><td colspan="5" class="text-center text-muted">Trống</td>'}</tbody>
          </table>
        </div>
      </div>
      <div class="card">
        <div class="card-header">
          <h3>📂 Chủ đề (${topics.length})</h3>
          <button class="btn btn-sm btn-primary" onclick="showAddTopicModal(${JSON.stringify(subjects).replace(/"/g, '&quot;')})">+ Thêm chủ đề</button>
        </div>
        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr><th>Tên chủ đề</th><th>Môn</th><th>Mô tả</th></tr>
            </thead>
            <tbody>${topicRows || '<tr><td colspan="3" class="text-center text-muted">Trống</td>'}</tbody>
          </table>
        </div>
      </div>
    </div>
  `);
}

function showAddSubjectModal() {
  showModal('Thêm môn học mới', `
    <div class="form-group"><label>Tên môn học</label><input id="m-tenmon" placeholder="Toán học đại cương"></div>
    <div class="form-group"><label>Mã môn</label><input id="m-mamon" placeholder="TOAN"></div>
    <div class="form-group"><label>Mô tả</label><textarea id="m-mota"></textarea></div>
  `, async () => {
    const p = {
      ten_mon: document.getElementById('m-tenmon').value.trim(),
      ma_mon: document.getElementById('m-mamon').value.trim().toUpperCase(),
      mo_ta: document.getElementById('m-mota').value.trim(),
    };
    if (!p.ten_mon || !p.ma_mon) throw new Error('Vui lòng nhập tên và mã môn');
    await createSubject(p);
    closeModal(); renderSubjects();
  });
}

function showAddTopicModal(subjects) {
  const opts = subjects.map(s => `<option value="${s.id}">${s.ten_mon}</option>`).join('');
  showModal('Thêm chủ đề mới', `
    <div class="form-group"><label>Môn học</label><select id="m-monhoc">${opts}</select></div>
    <div class="form-group"><label>Tên chủ đề</label><input id="m-tenchude" placeholder="Chương 1..."></div>
    <div class="form-group"><label>Mô tả</label><textarea id="m-chmota"></textarea></div>
  `, async () => {
    const p = {
      ten_chu_de: document.getElementById('m-tenchude').value.trim(),
      mon_hoc_id: parseInt(document.getElementById('m-monhoc').value),
      mo_ta: document.getElementById('m-chmota').value.trim(),
    };
    if (!p.ten_chu_de) throw new Error('Nhập tên chủ đề');
    await createTopic(p);
    closeModal(); renderSubjects();
  });
}

async function deleteSubjectAction(id) {
  if (!confirm('Ẩn môn học này?')) return;
  await deleteSubject(id); renderSubjects();
}

// ── NGÂN HÀNG CÂU HỎI ────────────────────────────────────────────────────────
let questionFilters = {};
async function renderQuestions() {
  loading();
  const [subjects, topics, questions] = await Promise.all([
    getSubjects(), getTopics(), getQuestions(questionFilters)
  ]);

  const diffMap = { de: ['Dễ', 'badge-green'], trung_binh: ['Trung bình', 'badge-yellow'], kho: ['Khó', 'badge-red'] };
  const typeMap = { trac_nghiem_mot_dap_an: 'TN 1 đáp án', trac_nghiem_nhieu_dap_an: 'TN nhiều đáp án', dung_sai: 'Đúng/Sai' };

  const sOpts = `<option value="">-- Tất cả môn --</option>` + subjects.map(s => `<option value="${s.id}" ${questionFilters.mon_hoc_id == s.id ? 'selected' : ''}>${s.ten_mon}</option>`).join('');
  const tOpts = `<option value="">-- Tất cả chủ đề --</option>` + topics.map(t => `<option value="${t.id}" ${questionFilters.chu_de_id == t.id ? 'selected' : ''}>${t.ten_chu_de}</option>`).join('');

  const rows = questions.map(q => {
    const [dl, dc] = diffMap[q.do_kho] || ['?', 'badge-gray'];
    return `<tr>
      <td style="max-width:320px;word-break:break-word">${q.noi_dung}</td>
      <td>${typeMap[q.loai_cau_hoi] || q.loai_cau_hoi}</td>
      <td><span class="badge ${dc}">${dl}</span></td>
      <td>${q.lua_chon.length}</td>
      <td style="text-align:center">
        <button class="btn btn-sm btn-danger" onclick="deleteQuestionAction(${q.id})" title="Xóa câu hỏi">🗑</button>
      </td>
    </tr>`;
  }).join('');

  setBody(`<div class="card">
    <div class="card-header">
      <h3>❓ Câu hỏi (${questions.length})</h3>
      <div style="display:flex;gap:8px">
        <button class="btn btn-sm btn-outline" onclick="showImportModal()">📥 Import Excel</button>
        <button class="btn btn-sm btn-primary" onclick="showAddQuestionModal(${JSON.stringify(topics).replace(/"/g, '&quot;')})">+ Thêm câu hỏi</button>
      </div>
    </div>
    <div class="card-body" style="padding-bottom:0">
      <div class="filter-bar">
        <input placeholder="🔍 Tìm theo nội dung..." value="${questionFilters.tu_khoa || ''}"
          onchange="questionFilters.tu_khoa=this.value;renderQuestions()" style="min-width:200px">
        <select onchange="questionFilters.mon_hoc_id=this.value;questionFilters.chu_de_id='';renderQuestions()">${sOpts}</select>
        <select onchange="questionFilters.chu_de_id=this.value;renderQuestions()">${tOpts}</select>
        <select onchange="questionFilters.do_kho=this.value;renderQuestions()">
          <option value="">-- Độ khó --</option>
          <option value="de" ${questionFilters.do_kho === 'de' ? 'selected' : ''}>Dễ</option>
          <option value="trung_binh" ${questionFilters.do_kho === 'trung_binh' ? 'selected' : ''}>Trung bình</option>
          <option value="kho" ${questionFilters.do_kho === 'kho' ? 'selected' : ''}>Khó</option>
        </select>
        <button class="btn btn-sm btn-outline" onclick="questionFilters={};renderQuestions()">↺ Xóa lọc</button>
      </div>
    </div>
    <div class="table-responsive">
      <table class="table">
        <thead>
          <tr><th>Nội dung câu hỏi</th><th>Loại</th><th>Độ khó</th><th>Đáp án</th><th>Thao tác</th></tr>
        </thead>
        <tbody>${rows || '<tr><td colspan="5"><div class="empty-state">Không có câu hỏi nào</div></td>'}</tbody>
      </table>
    </div>
  </div>`);
}

function showAddQuestionModal(topics) {
  const tOpts = topics.map(t => `<option value="${t.id}">${t.ten_chu_de}</option>`).join('');
  showModal('Thêm câu hỏi mới', `
    <div class="form-group"><label>Nội dung câu hỏi</label><textarea id="q-noidung" rows="3"></textarea></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="form-group"><label>Chủ đề</label><select id="q-chude">${tOpts}</select></div>
      <div class="form-group"><label>Độ khó</label>
        <select id="q-dokho"><option value="de">Dễ</option><option value="trung_binh" selected>Trung bình</option><option value="kho">Khó</option></select>
      </div>
    </div>
    <div class="form-group"><label>Giải thích (tùy chọn)</label><input id="q-giaithich"></div>
    <label style="font-weight:700;margin-bottom:8px">Các lựa chọn (tối thiểu 2, tối đa 6)</label>
    ${['A', 'B', 'C', 'D', 'E', 'F'].map((l, i) => `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <input type="checkbox" id="q-correct-${i}" style="width:16px">
        <span style="font-weight:700;min-width:20px">${l}.</span>
        <input type="text" id="q-choice-${i}" placeholder="Lựa chọn ${l}" style="flex:1;padding:8px;border:1.5px solid var(--border);border-radius:6px">
      </div>`).join('')}
  `, async () => {
    const lua_chon = [];
    for (let i = 0; i < 6; i++) {
      const nd = document.getElementById(`q-choice-${i}`).value.trim();
      if (nd) {
        lua_chon.push({
          noi_dung: nd,
          la_dap_an: document.getElementById(`q-correct-${i}`).checked,
          thu_tu: i,
        });
      }
    }
    if (lua_chon.length < 2) throw new Error('Cần ít nhất 2 lựa chọn');
    if (!lua_chon.some(lc => lc.la_dap_an)) throw new Error('Phải chọn ít nhất 1 đáp án đúng');
    await createQuestion({
      noi_dung: document.getElementById('q-noidung').value.trim(),
      chu_de_id: parseInt(document.getElementById('q-chude').value),
      do_kho: document.getElementById('q-dokho').value,
      loai_cau_hoi: lua_chon.filter(l => l.la_dap_an).length > 1 ? 'trac_nghiem_nhieu_dap_an' : 'trac_nghiem_mot_dap_an',
      giai_thich: document.getElementById('q-giaithich').value.trim() || null,
      lua_chon,
    });
    closeModal(); renderQuestions();
  });
}

async function deleteQuestionAction(id) {
  if (!confirm('Bạn có chắc muốn xóa (ẩn) câu hỏi này?')) return;
  try {
    await deleteQuestion(id);
    renderQuestions();
  } catch (err) {
    alert('Lỗi: ' + err.message);
  }
}

function showImportModal() {
  showModal('📥 Import câu hỏi từ Excel', `
    <div class="alert alert-info">
      <a href="${downloadTemplate()}" target="_blank" style="color:var(--primary)">⬇ Tải file Excel mẫu</a>
      (định dạng: chu_de_id | noi_dung | do_kho | giai_thich | dap_an_A | dap_an_B | dap_an_C | dap_an_D | dap_an_dung)
    </div>
    <div class="form-group">
      <label>Chọn file Excel (.xlsx)</label>
      <input type="file" id="import-file" accept=".xlsx,.xls" style="width:100%">
    </div>
    <div id="import-result"></div>
  `, async () => {
    const f = document.getElementById('import-file').files[0];
    if (!f) throw new Error('Chọn file Excel');
    const fd = new FormData();
    fd.append('file', f);
    const res = await fetch('http://127.0.0.1:8000/import/questions/excel', {
      method: 'POST', headers: { 'Authorization': `Bearer ${getToken()}` }, body: fd,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Lỗi import');
    document.getElementById('import-result').innerHTML = `<div class="alert alert-success">✅ Thành công: ${data.thanh_cong} câu | Lỗi: ${data.that_bai}</div>`;
    if (data.thanh_cong > 0) renderQuestions();
  }, 'Import');
}
// ── ĐỀ THI (ĐÃ SỬA: xóa đúng cách, chỉ giữ nút xuất Excel, bỏ nút báo cáo) ──
// ── ĐỀ THI (ĐÃ SỬA: bỏ cột Điểm đạt, chỉ giữ nút xuất Excel) ──
async function renderExams() {
  loading();
  const [exams, topics] = await Promise.all([getExams(), getTopics()]);
  const role = currentUser.vai_tro;

  const rows = exams.map(e => {
    const isPublished = e.cong_bo === true || e.cong_bo === 1;
    let actionButtons = '';
    
    if (role === 'hoc_sinh') {
      actionButtons = isPublished 
        ? `<button class="btn btn-sm btn-primary" onclick="startQuiz(${e.id})">▶ Làm bài</button>`
        : `<span class="text-muted">Chưa công bố</span>`;
    } else {
      actionButtons = `
        <button class="btn btn-sm btn-warning" onclick="publishExamAction(${e.id})">${isPublished ? '🔒 Gỡ' : '🌐 Công bố'}</button>
        <button class="btn btn-sm btn-danger" onclick="deleteExamAction(${e.id})">🗑 Xóa</button>
        <button class="btn btn-sm btn-success" onclick="downloadWithAuth('export/exam/${e.id}/excel')" title="Xuất đề thi Excel">📄 Xuất</button>
      `;
    }

    return `<tr>
      <td style="max-width:300px">
        <strong>${e.tieu_de}</strong><br>
        <small class="text-muted">${e.mo_ta || ''}</small>
      </td>
      <td class="text-center">${e.thoi_gian_lam_bai} phút</td>
      <td class="text-center"><span class="badge ${isPublished ? 'badge-green' : 'badge-gray'}">${isPublished ? 'Công bố' : 'Nháp'}</span></td>
      <td class="action-buttons" style="white-space: nowrap;">${actionButtons}</td>
    </tr>`;
  }).join('');

  setBody(`
    <div class="card">
      <div class="card-header">
        <h3>📝 Danh sách đề thi</h3>
        ${role !== 'hoc_sinh' ? `
        <div style="display:flex;gap:8px">
          <button class="btn btn-sm btn-outline" onclick="showAutoGenModal(${JSON.stringify(topics).replace(/"/g, '&quot;')})">⚡ Sinh tự động</button>
          <button class="btn btn-sm btn-primary" onclick="showCreateExamModal()">+ Tạo đề</button>
        </div>` : ''}
      </div>
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr><th>Đề thi</th><th>Thời gian</th><th>Trạng thái</th><th>Thao tác</th></tr>
          </thead>
          <tbody>
            ${rows || '<tr><td colspan="4" class="text-center">Chưa có đề thi</td>'}</tbody>
        </table>
      </div>
    </div>
  `);
}

async function deleteExamAction(id) {
  if (!confirm('Bạn có chắc chắn muốn xóa đề thi này? Hành động không thể hoàn tác.')) return;
  try {
    await deleteExam(id);
    renderExams();
    alert('Đã xóa đề thi thành công.');
  } catch (err) {
    alert('Lỗi khi xóa: ' + err.message);
  }
}

async function publishExamAction(id) {
  try {
    await publishExam(id);
    renderExams();
  } catch (err) {
    alert('Lỗi: ' + err.message);
  }
}

// Các hàm showCreateExamModal, showAutoGenModal, showExamReport (nếu có) giữ nguyên
// Nhưng nếu có hàm showExamReport, bạn có thể xóa nó hoặc giữ (không dùng nữa).

function showCreateExamModal() {
  showModal('Tạo đề thi mới', `
    <div class="form-group"><label>Tiêu đề</label><input id="e-tieude"></div>
    <div class="form-group"><label>Mô tả</label><textarea id="e-mota"></textarea></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="form-group"><label>Thời gian (phút)</label><input type="number" id="e-thoigian" value="30"></div>
      <div class="form-group"><label>Điểm đạt</label><input type="number" id="e-diemdai" value="5" step="0.5"></div>
    </div>
  `, async () => {
    await createExam({
      tieu_de: document.getElementById('e-tieude').value.trim(),
      mo_ta: document.getElementById('e-mota').value.trim(),
      thoi_gian_lam_bai: parseInt(document.getElementById('e-thoigian').value),
      diem_dat: parseFloat(document.getElementById('e-diemdai').value),
      danh_sach_cau_hoi: [],
    });
    closeModal(); renderExams();
  });
}

function showAutoGenModal(topics) {
  const tOpts = topics.map(t => `<option value="${t.id}">${t.ten_chu_de}</option>`).join('');
  showModal('⚡ Tự động sinh đề', `
    <div class="form-group"><label>Tiêu đề</label><input id="ag-tieude"></div>
    <div class="form-group"><label>Chủ đề</label><select id="ag-chude">${tOpts}</select></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="form-group"><label>Số câu</label><input type="number" id="ag-socau" value="5"></div>
      <div class="form-group"><label>Thời gian</label><input type="number" id="ag-thoigian" value="15"></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="form-group"><label>Độ khó</label>
        <select id="ag-dokho"><option value="">Tất cả</option><option value="de">Dễ</option><option value="trung_binh">Trung bình</option><option value="kho">Khó</option></select>
      </div>
      <div class="form-group"><label>Điểm/câu</label><input type="number" id="ag-diemcau" value="2" step="0.5"></div>
    </div>
  `, async () => {
    const p = {
      tieu_de: document.getElementById('ag-tieude').value.trim(),
      chu_de_id: parseInt(document.getElementById('ag-chude').value),
      so_luong_cau_hoi: parseInt(document.getElementById('ag-socau').value),
      thoi_gian_lam_bai: parseInt(document.getElementById('ag-thoigian').value),
      diem_moi_cau: parseFloat(document.getElementById('ag-diemcau').value),
      diem_dat: 5.0,
    };
    const dk = document.getElementById('ag-dokho').value;
    if (dk) p.do_kho = dk;
    await autoGenerateExam(p);
    closeModal(); renderExams();
  });
}

async function showExamReport(id) {
  const d = await getExamReport(id);
  showModal(`📊 ${d.tieu_de}`, `
    <div class="stats-grid" style="grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:20px">
      <div class="stat-card"><div class="stat-icon blue">👥</div><div class="stat-info"><strong>${d.tong_luot_thi}</strong><span>Lượt thi</span></div></div>
      <div class="stat-card"><div class="stat-icon green">⭐</div><div class="stat-info"><strong>${d.diem_trung_binh ?? '–'}</strong><span>Điểm TB</span></div></div>
      <div class="stat-card"><div class="stat-icon yellow">✅</div><div class="stat-info"><strong>${d.ty_le_dat != null ? d.ty_le_dat + '%' : '–'}</strong><span>Tỷ lệ đạt</span></div></div>
    </div>
    ${d.tong_luot_thi === 0 ? '<div class="alert alert-info">Chưa có học sinh nào làm bài.</div>' : ''}
  `, null, 'Đóng');
}

// ── LỊCH SỬ ──────────────────────────────────────────────────────────────────
async function renderMyHistory() {
  loading();
  const history = await getMyHistory();
  const rows = history.map(h => `<tr>
    <td>${h.ten_de_thi}</td>
    <td>${new Date(h.ngay_thi).toLocaleString('vi-VN')}</td>
    <td><strong>${h.diem_so ?? '–'}</strong></td>
    <td><span class="badge ${h.ket_qua === 'Đạt' ? 'badge-green' : 'badge-red'}">${h.ket_qua}</span></td>
  </tr>`).join('');
  setBody(`<div class="card"><div class="card-header"><h3>📊 Lịch sử làm bài</h3></div>
    <div class="table-responsive">
      <table class="table">
        <thead><tr><th>Đề thi</th><th>Thời gian</th><th>Điểm</th><th>Kết quả</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="4">Chưa có lần thi nào</td>'}</tbody>
      </table>
    </div>
  </div>`);
}

// ── BÁO CÁO (ĐÃ SỬA LỖI HIỂN THỊ) ──────────────────────────────────────────
async function renderReports() {
  loading();
  const exams = await getExams();
  
  const rows = exams.map(e => {
    const statusClass = e.cong_bo ? 'badge-green' : 'badge-gray';
    const statusText = e.cong_bo ? 'Công bố' : 'Nháp';
    return `<tr>
      <td><strong>${e.tieu_de}</strong><br><small class="text-muted">${e.mo_ta || ''}</small></td>
      <td><span class="badge ${statusClass}">${statusText}</span></td>
      <td><button class="btn btn-sm btn-outline" onclick="loadExamReport(${e.id})">📊 Xem</button></td>
    </tr>`;
  }).join('');

  setBody(`
    <div class="card">
      <div class="card-header">
        <h3>📈 Chọn đề thi để xem báo cáo</h3>
      </div>
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr><th>Đề thi</th><th>Trạng thái</th><th>Báo cáo</th></tr>
          </thead>
          <tbody>
            ${rows || '<tr><td colspan="3" class="text-center text-muted">Chưa có đề thi</td>'}</tbody>
        </table>
      </div>
    </div>
    <div id="report-detail"></div>
  `);
}

async function loadExamReport(id) {
  const d = await getExamReport(id);
  const statsHtml = `
    <div class="stats-grid" style="grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:20px">
      <div class="stat-card">
        <div class="stat-icon blue">👥</div>
        <div class="stat-info"><strong>${d.tong_luot_thi}</strong><span>Lượt thi</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">⭐</div>
        <div class="stat-info"><strong>${d.diem_trung_binh ?? '–'}</strong><span>Điểm TB</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon yellow">✅</div>
        <div class="stat-info"><strong>${d.ty_le_dat != null ? d.ty_le_dat + '%' : '–'}</strong><span>Tỷ lệ đạt</span></div>
      </div>
    </div>
    ${d.tong_luot_thi === 0 ? '<div class="alert alert-info">Chưa có học sinh nào làm bài.</div>' : ''}
  `;
  document.getElementById('report-detail').innerHTML = `<div class="card"><div class="card-header"><h3>📊 ${d.tieu_de}</h3></div><div class="card-body">${statsHtml}</div></div>`;
}

// ── NGƯỜI DÙNG ────────────────────────────────────────────────────────────────
async function renderUsers() {
  loading();
  const users = await getAllUsers();
  const roleMap = { admin: 'Quản trị viên', giao_vien: 'Giáo viên', hoc_sinh: 'Học sinh' };
  const rows = users.map((u, index) => {
    const isMe = currentUser && u.id === currentUser.id;
    const roleText = roleMap[u.vai_tro] || u.vai_tro;
    return `<tr>
      <td>${index + 1}</td>
      <td><strong>${u.ten_dang_nhap || '???'}</strong>${isMe ? ' <span class="badge badge-blue">Bạn</span>' : ''}</td>
      <td>${u.ho_ten || '???'}</td>
      <td><span class="badge badge-blue">${roleText}</span></td>
      <td><span class="badge ${u.kich_hoat ? 'badge-green' : 'badge-red'}">${u.kich_hoat ? 'Hoạt động' : 'Đã khóa'}</span></td>
      <td>
        ${!isMe ? `<button class="btn btn-sm ${u.kich_hoat ? 'btn-warning' : 'btn-success'}" onclick="toggleActiveAction(${u.id})">${u.kich_hoat ? '🔒 Khóa' : '🔓 Mở'}</button>
        <button class="btn btn-sm btn-danger" onclick="deleteUserAction(${u.id},'${u.ten_dang_nhap}')">🗑 Xóa</button>` : '<span class="text-muted">–</span>'}
      </td>
    </tr>`;
  }).join('');

  setBody(`<div class="card"><div class="card-header"><h3>👥 Người dùng (${users.length})</h3>
    <button class="btn btn-sm btn-primary" onclick="showCreateUserModal()">+ Tạo tài khoản</button></div>
    <div class="table-responsive">
      <table class="table">
        <thead><tr><th>STT</th><th>Tên đăng nhập</th><th>Họ tên</th><th>Vai trò</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="6">Chưa có người dùng</td>'}</tbody>
      </table>
    </div>
  </div>`);
}

async function toggleActiveAction(id) {
  try {
    await toggleUserActive(id);
    renderUsers();
  } catch (err) {
    alert('Lỗi: ' + err.message);
  }
}

async function deleteUserAction(id, ten) {
  if (!confirm(`Xóa tài khoản "${ten}"? Hành động này không thể hoàn tác.`)) return;
  try {
    await deleteUser(id);
    renderUsers();
  } catch (err) {
    alert('Lỗi: ' + err.message);
  }
}

function showCreateUserModal() {
  showModal('Tạo tài khoản mới', `
    <div class="form-group"><label>Họ tên</label><input id="u-hoten"></div>
    <div class="form-group"><label>Tên đăng nhập</label><input id="u-tendangnhap"></div>
    <div class="form-group"><label>Mật khẩu</label><input type="password" id="u-matkhau" placeholder="Ít nhất 6 ký tự"></div>
    <div class="form-group"><label>Vai trò</label>
      <select id="u-vaitro"><option value="hoc_sinh">Học sinh</option><option value="giao_vien">Giáo viên</option><option value="admin">Admin</option></select>
    </div>
  `, async () => {
    const p = {
      ho_ten: document.getElementById('u-hoten').value.trim(),
      ten_dang_nhap: document.getElementById('u-tendangnhap').value.trim(),
      mat_khau: document.getElementById('u-matkhau').value,
      vai_tro: document.getElementById('u-vaitro').value,
    };
    if (!p.ho_ten || !p.ten_dang_nhap || !p.mat_khau) throw new Error('Điền đầy đủ thông tin');
    if (p.mat_khau.length < 6) throw new Error('Mật khẩu tối thiểu 6 ký tự');
    await register(p);
    closeModal();
    renderUsers();
  }, 'Tạo tài khoản');
}

// ── ĐỔI MẬT KHẨU ─────────────────────────────────────────────────────────────
function showChangePasswordModal() {
  showModal('🔒 Đổi mật khẩu', `
    <div class="form-group"><label>Mật khẩu cũ</label><input type="password" id="cp-cu"></div>
    <div class="form-group"><label>Mật khẩu mới</label><input type="password" id="cp-moi" placeholder="Ít nhất 6 ký tự"></div>
    <div class="form-group"><label>Xác nhận</label><input type="password" id="cp-xn"></div>
  `, async () => {
    const cu = document.getElementById('cp-cu').value;
    const moi = document.getElementById('cp-moi').value;
    const xn = document.getElementById('cp-xn').value;
    if (!cu || !moi) throw new Error('Điền đầy đủ');
    if (moi.length < 6) throw new Error('Mật khẩu mới phải 6+ ký tự');
    if (moi !== xn) throw new Error('Mật khẩu xác nhận không khớp');
    await changePassword(cu, moi);
    closeModal();
    alert('Đổi mật khẩu thành công! Vui lòng đăng nhập lại.');
    logout();
  });
}

// ── IMPORT EXCEL CÂU HỎI ──────────────────────────────────────────────────────
function showImportModal() {
  showModal('📥 Import câu hỏi từ Excel', `
    <div class="alert alert-info"><a href="${downloadTemplate()}" target="_blank" style="color:var(--primary)">⬇ Tải file mẫu</a></div>
    <div class="form-group"><input type="file" id="import-file" accept=".xlsx,.xls"></div>
    <div id="import-result"></div>
  `, async () => {
    const f = document.getElementById('import-file').files[0];
    if (!f) throw new Error('Chọn file');
    const fd = new FormData();
    fd.append('file', f);
    const res = await fetch('http://127.0.0.1:8000/import/questions/excel', {
      method: 'POST', headers: { 'Authorization': `Bearer ${getToken()}` }, body: fd,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);
    document.getElementById('import-result').innerHTML = `<div class="alert alert-success">✅ Thành công: ${data.thanh_cong} | Lỗi: ${data.that_bai}</div>`;
    if (data.thanh_cong > 0) renderQuestions();
  });
}

// ── MODAL ─────────────────────────────────────────────────────────────────────
function showModal(title, bodyHtml, onConfirm, confirmLabel = 'Lưu', cancelLabel = 'Hủy') {
  document.getElementById('modal-overlay')?.remove();
  const div = document.createElement('div');
  div.id = 'modal-overlay';
  div.className = 'modal-overlay';
  div.innerHTML = `<div class="modal">
    <div class="modal-header"><h3>${title}</h3><button class="btn-close" onclick="closeModal()">×</button></div>
    <div class="modal-body">${bodyHtml}</div>
    <div class="modal-footer">
      <button class="btn btn-outline" onclick="closeModal()">${cancelLabel}</button>
      ${onConfirm ? `<button class="btn btn-primary" id="modal-confirm">${confirmLabel}</button>` : ''}
    </div>
  </div>`;
  document.body.appendChild(div);
  if (onConfirm) {
    document.getElementById('modal-confirm').onclick = async () => {
      const btn = document.getElementById('modal-confirm');
      btn.disabled = true; btn.textContent = 'Đang xử lý...';
      try { await onConfirm(); } catch (err) {
        document.querySelector('.modal-body').insertAdjacentHTML('beforeend', `<div class="alert alert-error">${err.message}</div>`);
        btn.disabled = false; btn.textContent = confirmLabel;
      }
    };
  }
}
function closeModal() { document.getElementById('modal-overlay')?.remove(); }