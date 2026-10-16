/**
 * Settlement Page Controller
 */

requireAuth();
renderNavbar("settlement");

let currentHostelId = getSelectedHostelId();
let currentFundId = getSelectedFundId();
let currentSettlementData = null;

document.addEventListener("DOMContentLoaded", async () => {
  if (!currentHostelId) {
    showAlert("alert-container", "No hostel selected. Please go to the Dashboard to select or create a hostel.", "warning");
    return;
  }

  await initializeSettlementPage();
});

async function initializeSettlementPage() {
  try {
    const funds = await authFetch(`/hostels/${currentHostelId}/monthly-funds`);
    const selector = document.getElementById("settlement-fund-selector");
    selector.innerHTML = "";

    if (!funds || funds.length === 0) {
      selector.innerHTML = `<option value="">No Active Fund</option>`;
      showAlert("alert-container", "No monthly funds found for this hostel.", "warning");
      return;
    }

    funds.forEach(f => {
      const opt = document.createElement("option");
      opt.value = f.id;
      opt.textContent = `${f.month} ${f.year} (${f.status})`;
      selector.appendChild(opt);
    });

    const matched = funds.find(f => f.id === currentFundId);
    if (matched) {
      selector.value = matched.id;
    } else {
      selector.value = funds[0].id;
      currentFundId = funds[0].id;
      setSelectedFundId(currentFundId);
    }

    selector.addEventListener("change", (e) => {
      currentFundId = parseInt(e.target.value, 10);
      setSelectedFundId(currentFundId);
      loadSettlementData(currentFundId);
    });

    await loadSettlementData(currentFundId);

  } catch (err) {
    showAlert("alert-container", "Failed to load settlement: " + err.message, "danger");
  }
}

async function loadSettlementData(fundId) {
  try {
    currentSettlementData = await authFetch(`/settlement/${fundId}`);

    // Update Header
    document.getElementById("settlement-month-title").textContent = 
      `${currentSettlementData.month} ${currentSettlementData.year} Settlement`;
    
    const statusBadge = document.getElementById("settlement-status-badge");
    statusBadge.textContent = currentSettlementData.status;
    statusBadge.className = `badge ${currentSettlementData.status === 'ACTIVE' ? 'bg-success' : 'bg-secondary'}`;

    const closeBtn = document.getElementById("close-fund-btn");
    if (currentSettlementData.status === "ACTIVE") {
      closeBtn.innerHTML = `<i class="bi bi-lock me-1"></i> Close Month`;
      closeBtn.className = "btn btn-outline-danger btn-sm text-nowrap";
    } else {
      closeBtn.innerHTML = `<i class="bi bi-unlock me-1"></i> Reopen Month`;
      closeBtn.className = "btn btn-outline-success btn-sm text-nowrap";
    }

    // Update 5 Cards
    document.getElementById("set-starting-budget").textContent = formatCurrency(currentSettlementData.starting_budget);
    document.getElementById("set-common-expenses").textContent = formatCurrency(currentSettlementData.total_common_expenses);
    document.getElementById("set-common-balance").textContent = formatCurrency(currentSettlementData.current_common_balance);
    document.getElementById("set-personal-expenses").textContent = formatCurrency(currentSettlementData.total_personal_expenses);
    document.getElementById("set-settlement-amount").textContent = formatCurrency(currentSettlementData.total_settlement_amount);

    // Update Explanation Guide
    document.getElementById("guide-holder-name").textContent = currentSettlementData.budget_holder_name;
    document.getElementById("guide-common-balance").textContent = formatCurrency(currentSettlementData.current_common_balance);
    document.getElementById("guide-net-remaining").textContent = formatCurrency(currentSettlementData.remaining_after_settlement);

    // Render Student Breakdown
    renderStudentsTable(currentSettlementData.students);

  } catch (err) {
    showAlert("alert-container", "Failed to compute settlement: " + err.message, "danger");
  }
}

function renderStudentsTable(students) {
  const tbody = document.getElementById("settlement-students-body");
  if (!students || students.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No student records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = students.map(s => {
    const owes = s.amount_to_receive > 0;
    return `
      <tr class="${owes ? 'table-light' : ''}">
        <td>
          <div class="fw-bold">${s.student_name} ${s.is_budget_holder ? '<span class="badge badge-holder ms-1">Budget Holder</span>' : ''}</div>
          <div class="small text-muted">${s.email}</div>
        </td>
        <td>
          <span class="badge ${s.role === 'ADMIN' ? 'badge-admin' : 'bg-light text-dark border'}">${s.role}</span>
        </td>
        <td class="fw-semibold text-secondary">
          ${formatCurrency(s.personal_expenses)}
        </td>
        <td class="fw-bold ${owes ? 'text-success fs-6' : 'text-muted'}">
          ${formatCurrency(s.amount_to_receive)}
        </td>
        <td>
          ${owes 
            ? `<span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1"><i class="bi bi-arrow-down-left me-1"></i>Owed Reimbursement</span>` 
            : `<span class="badge bg-light text-muted border px-2 py-1">Settled / None</span>`}
        </td>
      </tr>
    `;
  }).join("");
}

async function toggleFundStatus() {
  if (!currentSettlementData) return;

  const currentStatus = currentSettlementData.status;
  const targetStatus = currentStatus === "ACTIVE" ? "CLOSED" : "ACTIVE";
  const confirmMsg = currentStatus === "ACTIVE"
    ? "Are you sure you want to CLOSE this monthly fund? No new expenses can be added once closed."
    : "Are you sure you want to REOPEN this monthly fund?";

  if (!confirm(confirmMsg)) return;

  try {
    await authFetch(`/monthly-funds/${currentFundId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status: targetStatus })
    });

    showAlert("alert-container", `Month marked as ${targetStatus}!`, "success");
    await initializeSettlementPage();
  } catch (err) {
    showAlert("alert-container", "Failed to update fund status: " + err.message, "danger");
  }
}
