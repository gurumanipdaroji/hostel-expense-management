/**
 * Expenses Page Logic
 */

requireAuth();
renderNavbar("expenses");

let currentHostelId = getSelectedHostelId();
let currentFundId = getSelectedFundId();
let currentFund = null;
let currentMembers = [];
let addExpenseModal = null;

document.addEventListener("DOMContentLoaded", async () => {
  addExpenseModal = new bootstrap.Modal(document.getElementById("addExpenseModal"));

  // Set default date to today in YYYY-MM-DD
  document.getElementById("exp-date").value = new Date().toISOString().split("T")[0];

  if (!currentHostelId) {
    showAlert("alert-container", "No hostel selected. Please go to the Dashboard to select or create a hostel.", "warning");
    return;
  }

  // Check if directed from dashboard with ?action=add
  const urlParams = new URLSearchParams(window.location.search);
  const autoAdd = urlParams.get("action") === "add";

  await initializeExpensesPage();

  if (autoAdd) {
    openAddExpenseModal();
  }
});

function toggleSourceHelp() {
  // Can be used for dynamic form styling if needed
}

async function initializeExpensesPage() {
  try {
    // 1. Ensure active fund ID is known
    if (!currentFundId) {
      const funds = await authFetch(`/hostels/${currentHostelId}/monthly-funds`);
      if (funds && funds.length > 0) {
        currentFundId = funds[0].id;
        setSelectedFundId(currentFundId);
      }
    }

    if (!currentFundId) {
      showAlert("alert-container", "No monthly fund found for this hostel. Please create a month first on the Dashboard.", "warning");
      return;
    }

    // 2. Fetch Fund Details
    currentFund = await authFetch(`/monthly-funds/${currentFundId}`);
    document.getElementById("expense-page-common-balance").textContent = formatCurrency(currentFund.current_balance);

    // 3. Fetch Hostel Members
    currentMembers = await authFetch(`/hostels/${currentHostelId}/members`);
    populateStudentDropdowns();

    // 4. Fetch Expenses
    await loadExpenses();

    // Setup filter change listeners
    document.getElementById("filter-category").addEventListener("change", loadExpenses);
    document.getElementById("filter-student").addEventListener("change", loadExpenses);
    document.getElementById("filter-source").addEventListener("change", loadExpenses);

  } catch (err) {
    showAlert("alert-container", "Error loading expenses page: " + err.message, "danger");
  }
}

function populateStudentDropdowns() {
  const modalSelect = document.getElementById("exp-paid-by");
  const filterSelect = document.getElementById("filter-student");

  modalSelect.innerHTML = `<option value="">Select student who paid...</option>`;
  filterSelect.innerHTML = `<option value="">All Students</option>`;

  currentMembers.forEach(m => {
    // Modal
    const opt1 = document.createElement("option");
    opt1.value = m.user_id;
    opt1.textContent = `${m.user_name} (${m.user_email})`;
    modalSelect.appendChild(opt1);

    // Filter
    const opt2 = document.createElement("option");
    opt2.value = m.user_id;
    opt2.textContent = m.user_name;
    filterSelect.appendChild(opt2);
  });
}

function openAddExpenseModal() {
  document.getElementById("modal-expense-alert").innerHTML = "";
  document.getElementById("exp-description").value = "";
  document.getElementById("exp-amount").value = "";
  document.getElementById("exp-date").value = new Date().toISOString().split("T")[0];
  document.getElementById("radioCommon").checked = true;

  // Auto-select logged in student if in members
  const currentUser = getUser();
  if (currentUser) {
    document.getElementById("exp-paid-by").value = currentUser.id;
  }

  addExpenseModal.show();
}

async function loadExpenses() {
  try {
    const category = document.getElementById("filter-category").value;
    const studentId = document.getElementById("filter-student").value;
    const source = document.getElementById("filter-source").value;

    let url = `/monthly-funds/${currentFundId}/expenses?`;
    if (category) url += `category=${encodeURIComponent(category)}&`;
    if (studentId) url += `student_id=${encodeURIComponent(studentId)}&`;
    if (source) url += `payment_source=${encodeURIComponent(source)}&`;

    const expenses = await authFetch(url);

    renderExpensesTable(expenses);

    // Also update common balance in case it changed
    currentFund = await authFetch(`/monthly-funds/${currentFundId}`);
    document.getElementById("expense-page-common-balance").textContent = formatCurrency(currentFund.current_balance);

  } catch (err) {
    showAlert("alert-container", "Failed to load expenses: " + err.message, "danger");
  }
}

function renderExpensesTable(expenses) {
  const tbody = document.getElementById("expenses-table-body");
  const countEl = document.getElementById("expense-count");
  const totalEl = document.getElementById("total-filtered-spent");

  if (!expenses || expenses.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No matching expenses found.</td></tr>`;
    countEl.textContent = "0";
    totalEl.textContent = "₹0.00";
    return;
  }

  countEl.textContent = expenses.length;
  const totalAmount = expenses.reduce((sum, e) => sum + e.amount, 0);
  totalEl.textContent = formatCurrency(totalAmount);

  tbody.innerHTML = expenses.map(e => `
    <tr>
      <td class="text-nowrap small text-muted">${e.expense_date}</td>
      <td class="fw-semibold">${e.description}</td>
      <td><span class="badge bg-light text-dark border">${e.category}</span></td>
      <td>
        <i class="bi bi-person me-1 text-muted"></i> ${e.payer_name}
      </td>
      <td>
        <span class="${e.payment_source === 'COMMON_MONEY' ? 'badge-common' : 'badge-personal'} small">
          ${e.payment_source === 'COMMON_MONEY' ? 'Common Money' : 'Personal Money'}
        </span>
      </td>
      <td class="text-end fw-bold text-nowrap">${formatCurrency(e.amount)}</td>
      <td class="text-end">
        <button class="btn btn-outline-danger btn-sm" onclick="deleteExpense(${e.id}, '${e.description.replace(/'/g, "\\'")}', ${e.amount})" title="Delete Expense">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    </tr>
  `).join("");
}

function resetFilters() {
  document.getElementById("filter-category").value = "";
  document.getElementById("filter-student").value = "";
  document.getElementById("filter-source").value = "";
  loadExpenses();
}

// Add Expense Form Handler
document.getElementById("add-expense-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const description = document.getElementById("exp-description").value.trim();
  const category = document.getElementById("exp-category").value;
  const amount = parseFloat(document.getElementById("exp-amount").value);
  const paidBy = parseInt(document.getElementById("exp-paid-by").value, 10);
  const sourceRadio = document.querySelector('input[name="paymentSourceRadio"]:checked');
  const paymentSource = sourceRadio ? sourceRadio.value : "COMMON_MONEY";
  const expenseDate = document.getElementById("exp-date").value;

  if (!description || !amount || amount <= 0 || !paidBy || !expenseDate) {
    showAlert("modal-expense-alert", "Please complete all fields with valid information.", "danger");
    return;
  }

  try {
    await authFetch("/expenses", {
      method: "POST",
      body: JSON.stringify({
        monthly_fund_id: currentFundId,
        paid_by: paidBy,
        description: description,
        category: category,
        amount: amount,
        payment_source: paymentSource,
        expense_date: expenseDate
      })
    });

    addExpenseModal.hide();
    showAlert("alert-container", `Expense "${description}" recorded successfully!`, "success");
    await loadExpenses();

  } catch (err) {
    showAlert("modal-expense-alert", err.message, "danger");
  }
});

// Delete Expense Handler
async function deleteExpense(id, description, amount) {
  if (!confirm(`Are you sure you want to delete expense "${description}" for ${formatCurrency(amount)}?`)) {
    return;
  }

  try {
    await authFetch(`/expenses/${id}`, {
      method: "DELETE"
    });

    showAlert("alert-container", `Expense "${description}" was deleted.`, "info");
    await loadExpenses();
  } catch (err) {
    showAlert("alert-container", "Failed to delete expense: " + err.message, "danger");
  }
}
