/**
 * Monthly Fund History Controller
 */

requireAuth();
renderNavbar("monthly-history");

let currentHostelId = getSelectedHostelId();

document.addEventListener("DOMContentLoaded", async () => {
  if (!currentHostelId) {
    showAlert("alert-container", "No hostel selected. Please go to the Dashboard to select or create a hostel.", "warning");
    return;
  }

  await loadMonthlyHistory();
});

async function loadMonthlyHistory() {
  const container = document.getElementById("history-grid");

  try {
    const funds = await authFetch(`/hostels/${currentHostelId}/monthly-funds`);

    if (!funds || funds.length === 0) {
      container.innerHTML = `
        <div class="col-12 text-center text-muted py-5">
          <i class="bi bi-calendar-x fs-1 text-secondary mb-2 d-block"></i>
          <h5>No monthly funds recorded yet</h5>
          <p class="small">Create your first monthly fund on the <a href="dashboard.html">Dashboard</a>.</p>
        </div>
      `;
      return;
    }

    // Fetch settlement details for all funds in parallel for accurate breakdown
    const settlements = await Promise.all(
      funds.map(f => authFetch(`/settlement/${f.id}`).catch(() => null))
    );

    container.innerHTML = funds.map((f, index) => {
      const s = settlements[index];
      const startingBudget = s ? s.starting_budget : f.total_budget;
      const commonExpenses = s ? s.total_common_expenses : (f.total_budget - f.current_balance);
      const remainingBalance = s ? s.current_common_balance : f.current_balance;
      const personalExpenses = s ? s.total_personal_expenses : 0.0;
      const budgetHolder = s ? s.budget_holder_name : (f.budget_holder_name || "Unassigned");
      const isClosed = f.status === "CLOSED";

      return `
        <div class="col-md-6 col-lg-4">
          <div class="card border-0 shadow-sm rounded-4 h-100 p-4 position-relative" style="border-top: 4px solid ${isClosed ? '#94a3b8' : 'var(--primary-color)'} !important;">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div>
                <h4 class="fw-bold mb-0">${f.month} ${f.year}</h4>
                <small class="text-muted">Budget Holder: <strong>${budgetHolder}</strong></small>
              </div>
              <span class="badge ${isClosed ? 'bg-secondary' : 'bg-success'}">
                ${f.status}
              </span>
            </div>

            <!-- Stats List -->
            <div class="bg-light p-3 rounded-3 mb-3">
              <div class="d-flex justify-content-between mb-2">
                <span class="text-muted small">Budget:</span>
                <strong class="text-dark">${formatCurrency(startingBudget)}</strong>
              </div>
              <div class="d-flex justify-content-between mb-2">
                <span class="text-muted small">Common Expenses:</span>
                <strong class="text-danger">${formatCurrency(commonExpenses)}</strong>
              </div>
              <div class="d-flex justify-content-between mb-2">
                <span class="text-muted small">Remaining Balance:</span>
                <strong class="text-success">${formatCurrency(remainingBalance)}</strong>
              </div>
              <div class="d-flex justify-content-between pt-2 border-top">
                <span class="text-muted small">Personal Expenses:</span>
                <strong class="text-primary">${formatCurrency(personalExpenses)}</strong>
              </div>
            </div>

            <!-- Card Actions -->
            <div class="d-flex gap-2 mt-auto">
              <button class="btn btn-outline-primary btn-sm w-50" onclick="viewInDashboard(${f.id})">
                <i class="bi bi-grid-fill me-1"></i> Dashboard
              </button>
              <button class="btn btn-primary btn-sm w-50" onclick="viewInSettlement(${f.id})">
                <i class="bi bi-calculator-fill me-1"></i> Settlement
              </button>
            </div>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    showAlert("alert-container", "Failed to load monthly history: " + err.message, "danger");
  }
}

function viewInDashboard(fundId) {
  setSelectedFundId(fundId);
  window.location.href = "dashboard.html";
}

function viewInSettlement(fundId) {
  setSelectedFundId(fundId);
  window.location.href = "settlement.html";
}
