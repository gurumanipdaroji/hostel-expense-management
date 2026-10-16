/**
 * Dashboard Logic
 */

requireAuth();
renderNavbar("dashboard");

let currentHostels = [];
let currentHostelId = getSelectedHostelId();
let currentFundId = getSelectedFundId();
let currentMembers = [];

let createHostelModal = null;
let createFundModal = null;

document.addEventListener("DOMContentLoaded", async () => {
  createHostelModal = new bootstrap.Modal(document.getElementById("createHostelModal"));
  createFundModal = new bootstrap.Modal(document.getElementById("createFundModal"));

  await initializeHostels();
});

function openCreateHostelModal() {
  document.getElementById("modal-hostel-alert").innerHTML = "";
  document.getElementById("new-hostel-name").value = "";
  createHostelModal.show();
}

function openCreateFundModal() {
  document.getElementById("modal-fund-alert").innerHTML = "";
  populateBudgetHolderDropdown();
  createFundModal.show();
}

async function initializeHostels() {
  try {
    currentHostels = await authFetch("/hostels");

    if (!currentHostels || currentHostels.length === 0) {
      document.getElementById("no-hostel-banner").classList.remove("d-none");
      document.getElementById("dashboard-content").classList.add("d-none");
      const navHostelName = document.getElementById("current-hostel-name");
      if (navHostelName) navHostelName.textContent = "No Hostel Joined";
      return;
    }

    document.getElementById("no-hostel-banner").classList.add("d-none");
    document.getElementById("dashboard-content").classList.remove("d-none");

    // Select stored hostel or first available
    const matched = currentHostels.find(h => h.id === currentHostelId);
    if (!matched) {
      currentHostelId = currentHostels[0].id;
      setSelectedHostelId(currentHostelId);
    }

    updateHostelNavDropdown();
    await loadHostelData(currentHostelId);

  } catch (err) {
    showAlert("alert-container", "Failed to load hostels: " + err.message, "danger");
  }
}

function updateHostelNavDropdown() {
  const currentHostel = currentHostels.find(h => h.id === currentHostelId);
  const nameEl = document.getElementById("current-hostel-name");
  if (nameEl && currentHostel) {
    nameEl.textContent = currentHostel.hostel_name;
  }

  const dropdownMenu = document.getElementById("hostel-dropdown-menu");
  if (dropdownMenu) {
    let itemsHtml = `
      <li><span class="dropdown-item-text text-muted small fw-semibold">Switch Hostel</span></li>
    `;
    currentHostels.forEach(h => {
      const activeMark = (h.id === currentHostelId) ? "✓ " : "";
      itemsHtml += `
        <li>
          <button class="dropdown-item ${h.id === currentHostelId ? 'fw-bold text-primary' : ''}" onclick="switchHostel(${h.id})">
            ${activeMark}${h.hostel_name}
          </button>
        </li>
      `;
    });
    itemsHtml += `
      <li><hr class="dropdown-divider"></li>
      <li><button class="dropdown-item" onclick="openCreateHostelModal()"><i class="bi bi-plus-circle me-1"></i> Create New Hostel</button></li>
    `;
    dropdownMenu.innerHTML = itemsHtml;
  }
}

async function switchHostel(hostelId) {
  currentHostelId = hostelId;
  setSelectedHostelId(hostelId);
  currentFundId = null;
  setSelectedFundId(null);
  updateHostelNavDropdown();
  await loadHostelData(hostelId);
}

async function loadHostelData(hostelId) {
  try {
    // 1. Fetch members of this hostel (for modal dropdown and summary)
    currentMembers = await authFetch(`/hostels/${hostelId}/members`);

    // 2. Fetch monthly funds for this hostel
    const funds = await authFetch(`/hostels/${hostelId}/monthly-funds`);

    const fundSelector = document.getElementById("fund-selector");
    fundSelector.innerHTML = "";

    if (!funds || funds.length === 0) {
      fundSelector.innerHTML = `<option value="">No Active Fund</option>`;
      showEmptyFundState();
      return;
    }

    // Populate fund selector
    funds.forEach(f => {
      const opt = document.createElement("option");
      opt.value = f.id;
      opt.textContent = `${f.month} ${f.year} (${f.status})`;
      fundSelector.appendChild(opt);
    });

    // Pick stored or newest fund
    const matchedFund = funds.find(f => f.id === currentFundId);
    if (matchedFund) {
      fundSelector.value = matchedFund.id;
      currentFundId = matchedFund.id;
    } else {
      fundSelector.value = funds[0].id;
      currentFundId = funds[0].id;
      setSelectedFundId(currentFundId);
    }

    fundSelector.onchange = (e) => {
      const newId = parseInt(e.target.value, 10);
      if (newId) {
        currentFundId = newId;
        setSelectedFundId(newId);
        loadDashboardMetrics(currentFundId);
      }
    };

    await loadDashboardMetrics(currentFundId);

  } catch (err) {
    showAlert("alert-container", "Error loading hostel details: " + err.message, "danger");
  }
}

async function loadDashboardMetrics(fundId) {
  try {
    const data = await authFetch(`/dashboard/${fundId}`);

    // Update Header
    document.getElementById("fund-title").textContent = `${data.month} ${data.year} Overview`;
    const statusBadge = document.getElementById("fund-status-badge");
    statusBadge.textContent = data.status;
    statusBadge.className = `badge ${data.status === 'ACTIVE' ? 'bg-success' : 'bg-secondary'}`;
    document.getElementById("budget-holder-name").textContent = data.budget_holder ? data.budget_holder.name : "Unassigned";

    // Update Cards
    document.getElementById("card-total-budget").textContent = formatCurrency(data.cards.monthly_budget);
    document.getElementById("card-common-balance").textContent = formatCurrency(data.cards.current_common_balance);
    document.getElementById("card-common-spent").textContent = formatCurrency(data.cards.common_money_spent);
    document.getElementById("card-personal-spent").textContent = formatCurrency(data.cards.personal_expenses);
    document.getElementById("card-settlement-pending").textContent = formatCurrency(data.cards.settlement_pending);
    document.getElementById("card-member-count").textContent = data.cards.number_of_members;
    document.getElementById("card-member-paid-status").textContent = `${data.cards.members_paid_count} of ${data.cards.number_of_members} Paid`;

    // Render Recent Expenses
    renderRecentExpenses(data.recent_expenses);

    // Render Members Status
    renderMembersSummary(data.members);

  } catch (err) {
    showAlert("alert-container", "Failed to load dashboard metrics: " + err.message, "danger");
  }
}

function showEmptyFundState() {
  document.getElementById("fund-title").textContent = "No Monthly Fund Created";
  document.getElementById("fund-status-badge").textContent = "INACTIVE";
  document.getElementById("budget-holder-name").textContent = "None";

  document.getElementById("card-total-budget").textContent = "₹0.00";
  document.getElementById("card-common-balance").textContent = "₹0.00";
  document.getElementById("card-common-spent").textContent = "₹0.00";
  document.getElementById("card-personal-spent").textContent = "₹0.00";
  document.getElementById("card-settlement-pending").textContent = "₹0.00";
  document.getElementById("card-member-count").textContent = currentMembers.length;
  document.getElementById("card-member-paid-status").textContent = "Create Month to Begin";

  document.getElementById("recent-expenses-body").innerHTML = `
    <tr><td colspan="6" class="text-center text-muted py-4">
      No monthly fund active. <button class="btn btn-sm btn-link" onclick="openCreateFundModal()">Create one now</button>.
    </td></tr>
  `;

  renderMembersSummary(currentMembers.map(m => ({
    name: m.user_name,
    email: m.user_email,
    role: m.role,
    is_budget_holder: false,
    contribution_amount: 0,
    contribution_paid: false
  })));
}

function renderRecentExpenses(expenses) {
  const tbody = document.getElementById("recent-expenses-body");
  if (!expenses || expenses.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No expenses recorded for this month yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = expenses.map(e => `
    <tr>
      <td class="text-nowrap small text-muted">${e.expense_date}</td>
      <td class="fw-semibold">${e.description}</td>
      <td><span class="badge bg-light text-dark border">${e.category}</span></td>
      <td>${e.paid_by_name}</td>
      <td>
        <span class="${e.payment_source === 'COMMON_MONEY' ? 'badge-common' : 'badge-personal'} small">
          ${e.payment_source === 'COMMON_MONEY' ? 'Common Money' : 'Personal Money'}
        </span>
      </td>
      <td class="text-end fw-bold text-nowrap">${formatCurrency(e.amount)}</td>
    </tr>
  `).join("");
}

function renderMembersSummary(members) {
  const tbody = document.getElementById("members-list-body");
  if (!members || members.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-3">No members added yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = members.map(m => `
    <tr>
      <td>
        <div class="fw-semibold">${m.name}</div>
        <div class="small text-muted">${m.email}</div>
      </td>
      <td>
        <span class="badge ${m.role === 'ADMIN' ? 'badge-admin' : 'bg-light text-dark border'} small">${m.role}</span>
        ${m.is_budget_holder ? '<span class="badge badge-holder ms-1 small">Holder</span>' : ''}
      </td>
      <td>
        <span class="badge ${m.contribution_paid ? 'bg-success' : 'bg-warning text-dark'} small">
          ${m.contribution_paid ? 'Paid' : 'Unpaid'}
        </span>
      </td>
      <td class="text-end small fw-semibold">${formatCurrency(m.contribution_amount || 0)}</td>
    </tr>
  `).join("");
}

function populateBudgetHolderDropdown() {
  const select = document.getElementById("fund-budget-holder");
  select.innerHTML = `<option value="">Select a member...</option>`;
  currentMembers.forEach(m => {
    const opt = document.createElement("option");
    opt.value = m.user_id;
    opt.textContent = `${m.user_name} (${m.user_email})`;
    select.appendChild(opt);
  });
}

// Handler: Create Hostel Form
document.getElementById("create-hostel-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("new-hostel-name").value.trim();
  if (!name) return;

  try {
    const newHostel = await authFetch("/hostels", {
      method: "POST",
      body: JSON.stringify({ hostel_name: name })
    });

    createHostelModal.hide();
    currentHostelId = newHostel.id;
    setSelectedHostelId(newHostel.id);
    showAlert("alert-container", `Hostel "${newHostel.hostel_name}" created successfully!`, "success");
    await initializeHostels();
  } catch (err) {
    showAlert("modal-hostel-alert", err.message, "danger");
  }
});

// Handler: Create Monthly Fund Form
document.getElementById("create-fund-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const month = document.getElementById("fund-month").value;
  const year = parseInt(document.getElementById("fund-year").value, 10);
  const budgetHolderId = parseInt(document.getElementById("fund-budget-holder").value, 10);
  const perStudent = parseFloat(document.getElementById("fund-per-student").value);

  if (!budgetHolderId) {
    showAlert("modal-fund-alert", "Please select a budget holder from the members list.", "danger");
    return;
  }

  try {
    const newFund = await authFetch("/monthly-funds", {
      method: "POST",
      body: JSON.stringify({
        hostel_id: currentHostelId,
        month: month,
        year: year,
        budget_holder_id: budgetHolderId,
        per_student_contribution: perStudent
      })
    });

    createFundModal.hide();
    currentFundId = newFund.id;
    setSelectedFundId(newFund.id);
    showAlert("alert-container", `Monthly fund for ${newFund.month} ${newFund.year} created!`, "success");
    await loadHostelData(currentHostelId);
  } catch (err) {
    showAlert("modal-fund-alert", err.message, "danger");
  }
});
