/* api.js – Giao tiếp với FastAPI backend */
const API_BASE = '';

function getToken() { return sessionStorage.getItem('access_token'); }

function authHeaders() {
  const t = getToken();
  return { 'Content-Type': 'application/json', ...(t ? { 'Authorization': `Bearer ${t}` } : {}) };
}

async function apiCall(method, endpoint, body = null) {
  const opts = { method, headers: authHeaders() };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE}${endpoint}`, opts);
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Lỗi ${res.status}`);
  return data;
}

async function login(username, password) {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Đăng nhập thất bại');
  return data;
}

async function changeFirstPassword(username, oldPassword, newPassword) {
  return apiCall('POST', '/auth/change-first-password', {
    ten_dang_nhap: username,
    mat_khau_cu: oldPassword,
    mat_khau_moi: newPassword
  });
}

async function changePassword(oldPassword, newPassword) {
  return apiCall('PUT', '/auth/change-password', { mat_khau_cu: oldPassword, mat_khau_moi: newPassword });
}

const getMe = () => apiCall('GET', '/auth/me');

// Người dùng (Admin)
const getAllUsers = () => apiCall('GET', '/auth/users');
const toggleUserActive = (id) => apiCall('PUT', `/auth/users/${id}/toggle-active`);
const updateUserRole = (id, role) => apiCall('PUT', `/auth/users/${id}/role`, { vai_tro: role });
const deleteUser = (id) => apiCall('DELETE', `/auth/users/${id}`);

// Môn học & Chủ đề
const getSubjects = () => apiCall('GET', '/subjects');
const createSubject = (d) => apiCall('POST', '/subjects', d);
const deleteSubject = (id) => apiCall('DELETE', `/subjects/${id}`);
const getTopics = (mid) => apiCall('GET', `/topics${mid ? `?mon_hoc_id=${mid}` : ''}`);
const createTopic = (d) => apiCall('POST', '/topics', d);

// Câu hỏi
const getQuestions = (p = {}) => {
  const q = new URLSearchParams();
  Object.entries(p).forEach(([k, v]) => { if (v) q.append(k, v); });
  return apiCall('GET', `/questions?${q}`);
};
const createQuestion = (d) => apiCall('POST', '/questions', d);
const deleteQuestion = (id) => apiCall('DELETE', `/questions/${id}`);

// Đề thi
const getExams = () => apiCall('GET', '/exams');
const getExam = (id) => apiCall('GET', `/exams/${id}`);
const createExam = (d) => apiCall('POST', '/exams', d);
const autoGenerateExam = (d) => apiCall('POST', '/exams/auto-generate', d);
const publishExam = (id) => apiCall('POST', `/exams/${id}/publish`);
const deleteExam = (id) => apiCall('DELETE', `/exams/${id}`);
const getExamQuestions = (id) => apiCall('GET', `/exams/${id}/questions`);

// Làm bài
const startAttempt = (examId) => apiCall('POST', `/exams/${examId}/start`);
const submitAttempt = (id, answers, auto = false) =>
  apiCall('POST', `/attempts/${id}/submit`, { danh_sach_tra_loi: answers, nop_tu_dong: auto });
const getAttemptResult = (id) => apiCall('GET', `/attempts/${id}/result`);
const getMyAttempts = () => apiCall('GET', '/my-attempts');
const monitorEvent = (id, loai, mo_ta = '') =>
  apiCall('POST', `/attempts/${id}/monitor`, { loai_su_kien: loai, mo_ta });

// Báo cáo
const getExamReport = (id) => apiCall('GET', `/reports/exam/${id}`);
const getMyHistory = () => apiCall('GET', '/reports/my-history');

// Admin Import Users (Excel)
async function downloadAdminTemplate() {
  const res = await fetch(`${API_BASE}/admin/import-template`, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  if (!res.ok) { alert('Không tải được file mẫu.'); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'mau_tao_tai_khoan.xlsx';
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
}

async function importUsersExcel(file) {
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch(`${API_BASE}/admin/import-users`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${getToken()}` },
    body: fd,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Lỗi import');
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const cd = res.headers.get('Content-Disposition') || '';
  const name = cd.match(/filename\*?=(?:UTF-8'')?([^;]+)/)?.[1]?.replace(/"/g, '') || 'bao_cao_import.xlsx';
  a.download = decodeURIComponent(name);
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
}

// Xuất & Import câu hỏi
async function downloadWithAuth(endpoint) {
  const res = await fetch(`${API_BASE}/${endpoint}`, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  if (!res.ok) { alert('Không xuất được file.'); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const cd = res.headers.get('Content-Disposition') || '';
  const name = cd.match(/filename\*?=(?:UTF-8'')?([^;]+)/)?.[1]?.replace(/"/g, '') || 'export.xlsx';
  a.href = url; a.download = decodeURIComponent(name);
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
}
const downloadTemplate = () => `${API_BASE}/import/template/excel`;