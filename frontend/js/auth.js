/**
 * Authentication and Shared Utilities
 */

const TOKEN_KEY = "hostel_jwt_token";
const USER_KEY = "hostel_user_data";
const HOSTEL_ID_KEY = "hostel_selected_id";
const FUND_ID_KEY = "hostel_selected_fund_id";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getUser() {
  const userStr = localStorage.getItem(USER_KEY);
  try {
    return userStr ? JSON.parse(userStr) : null;
  } catch (e) {
    return null;
  }
}

function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(HOSTEL_ID_KEY);
  localStorage.removeItem(FUND_ID_KEY);
}

function logout() {
  clearSession();
  window.location.href = "login.html";
}

function requireAuth() {
  const token = getToken();
  if (!token) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}

function redirectIfLoggedIn() {
  const token = getToken();
  if (token) {
    window.location.href = "dashboard.html";
  }
}

function getSelectedHostelId() {
  const val = localStorage.getItem(HOSTEL_ID_KEY);
  return val ? parseInt(val, 10) : null;
}

function setSelectedHostelId(id) {
  localStorage.setItem(HOSTEL_ID_KEY, id);
}

function getSelectedFundId() {
  const val = localStorage.getItem(FUND_ID_KEY);
  return val ? parseInt(val, 10) : null;
}

function setSelectedFundId(id) {
  localStorage.setItem(FUND_ID_KEY, id);
}

/**
 * Universal authenticated fetch wrapper
 */
async function authFetch(endpoint, options = {}) {
  const token = getToken();
  const headers = options.headers || {};

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const url = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      clearSession();
      window.location.href = "login.html?expired=1";
      throw new Error("Session expired. Please log in again.");
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = (data && data.detail) 
        ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))
        : `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  } catch (err) {
    throw err;
  }
}

/**
 * Currency Formatter
 */
function formatCurrency(amount) {
  const val = Number(amount) || 0;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
    minimumFractionDigits: 2
  }).format(val);
}

/**
 * UI Alert Box
 */
function showAlert(containerId, message, type = "danger") {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  `;
}

/**
 * Render standard navigation bar
 */
function renderNavbar(activePage = "") {
  const navContainer = document.getElementById("navbar-container");
  if (!navContainer) return;

  const user = getUser();
  const userName = user ? user.name : "Student";

  navContainer.innerHTML = `
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
      <div class="container-fluid px-lg-4">
        <a class="navbar-brand d-flex align-items-center" href="dashboard.html">
          <i class="bi bi-wallet2 me-2 fs-4"></i>
          <span>Hostel Expense System</span>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNavbar" aria-controls="mainNavbar" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="mainNavbar">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <a class="nav-link ${activePage === 'dashboard' ? 'active' : ''}" href="dashboard.html">
                <i class="bi bi-grid-fill me-1"></i> Dashboard
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link ${activePage === 'members' ? 'active' : ''}" href="members.html">
                <i class="bi bi-people-fill me-1"></i> Members
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link ${activePage === 'expenses' ? 'active' : ''}" href="expenses.html">
                <i class="bi bi-receipt me-1"></i> Expenses
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link ${activePage === 'settlement' ? 'active' : ''}" href="settlement.html">
                <i class="bi bi-calculator-fill me-1"></i> Settlement
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link ${activePage === 'monthly-history' ? 'active' : ''}" href="monthly-history.html">
                <i class="bi bi-calendar3 me-1"></i> Monthly History
              </a>
            </li>
          </ul>

          <div class="d-flex align-items-center gap-3">
            <div class="dropdown">
              <button class="btn btn-outline-light btn-sm dropdown-toggle" type="button" id="hostelDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="bi bi-building me-1"></i> <span id="current-hostel-name">Loading Hostel...</span>
              </button>
              <ul class="dropdown-menu dropdown-menu-end shadow" id="hostel-dropdown-menu" aria-labelledby="hostelDropdown">
                <li><span class="dropdown-item-text text-muted small">Switch Hostel</span></li>
                <li><hr class="dropdown-divider"></li>
                <li><button class="dropdown-item" onclick="openCreateHostelModal()"><i class="bi bi-plus-circle me-1"></i> Create New Hostel</button></li>
              </ul>
            </div>

            <div class="text-light d-none d-md-block">
              <span class="badge bg-light text-primary py-2 px-3 rounded-pill fw-semibold">
                <i class="bi bi-person-circle me-1"></i> ${userName}
              </span>
            </div>

            <button class="btn btn-light btn-sm" onclick="logout()" title="Logout">
              <i class="bi bi-box-arrow-right me-1"></i> Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  `;
}
