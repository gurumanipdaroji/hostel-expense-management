/**
 * Members Management Logic
 */

requireAuth();
renderNavbar("members");

let currentHostelId = getSelectedHostelId();
let currentFundId = getSelectedFundId();
let currentMembers = [];
let currentContributions = [];

let addMemberModal = null;
let contributionModal = null;

document.addEventListener("DOMContentLoaded", async () => {
  addMemberModal = new bootstrap.Modal(document.getElementById("addMemberModal"));
  contributionModal = new bootstrap.Modal(document.getElementById("contributionModal"));

  if (!currentHostelId) {
    showAlert("alert-container", "No hostel selected. Please go to the Dashboard to select or create a hostel.", "warning");
    return;
  }

  await loadMembersPageData();
});

function openAddMemberModal() {
  document.getElementById("modal-member-alert").innerHTML = "";
  document.getElementById("member-email").value = "";
  document.getElementById("member-role").value = "MEMBER";
  addMemberModal.show();
}

async function loadMembersPageData() {
  try {
    // 1. Fetch hostel members
    currentMembers = await authFetch(`/hostels/${currentHostelId}/members`);

    // 2. If we don't have a fund ID, try finding active fund
    if (!currentFundId) {
      const funds = await authFetch(`/hostels/${currentHostelId}/monthly-funds`);
      if (funds && funds.length > 0) {
        currentFundId = funds[0].id;
        setSelectedFundId(currentFundId);
      }
    }

    // 3. Fetch contributions if fund exists
    if (currentFundId) {
      currentContributions = await authFetch(`/monthly-funds/${currentFundId}/contributions`).catch(() => []);
    } else {
      currentContributions = [];
    }

    renderMembersTable();

  } catch (err) {
    showAlert("alert-container", "Failed to load members: " + err.message, "danger");
  }
}

function renderMembersTable() {
  const tbody = document.getElementById("members-table-body");
  if (!currentMembers || currentMembers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No members found in this hostel.</td></tr>`;
    return;
  }

  const contribMap = {};
  currentContributions.forEach(c => {
    contribMap[c.student_id] = c;
  });

  tbody.innerHTML = currentMembers.map(m => {
    const contrib = contribMap[m.user_id];
    const hasContrib = Boolean(contrib);
    const isPaid = hasContrib && contrib.paid;
    const amountStr = hasContrib ? formatCurrency(contrib.amount) : "Not Set";
    const joinedDate = new Date(m.joined_at).toLocaleDateString();

    return `
      <tr>
        <td class="fw-semibold">
          <i class="bi bi-person-circle text-muted me-1"></i> ${m.user_name}
        </td>
        <td class="text-muted small">${m.user_email}</td>
        <td>
          <span class="badge ${m.role === 'ADMIN' ? 'badge-admin' : 'bg-light text-dark border'}">${m.role}</span>
        </td>
        <td class="small text-muted">${joinedDate}</td>
        <td class="fw-semibold">${amountStr}</td>
        <td>
          ${hasContrib 
            ? `<span class="badge ${isPaid ? 'bg-success' : 'bg-warning text-dark'}">${isPaid ? 'PAID' : 'PENDING'}</span>` 
            : `<span class="badge bg-secondary">NO FUND</span>`}
        </td>
        <td class="text-end">
          ${currentFundId ? `
            <button class="btn btn-outline-primary btn-sm me-1" onclick="openContributionModal(${m.user_id}, '${m.user_name.replace(/'/g, "\\'")}', ${hasContrib ? contrib.id : 'null'}, ${hasContrib ? contrib.amount : 2000}, ${isPaid})">
              <i class="bi bi-pencil-square"></i> Fund Status
            </button>
          ` : ''}
          <button class="btn btn-outline-danger btn-sm" onclick="removeMember(${m.user_id}, '${m.user_name.replace(/'/g, "\\'")}')" title="Remove Member">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function openContributionModal(studentId, studentName, recordId, amount, isPaid) {
  document.getElementById("modal-contrib-alert").innerHTML = "";
  document.getElementById("contrib-student-id").value = studentId;
  document.getElementById("contrib-record-id").value = recordId || "";
  document.getElementById("contrib-student-name").textContent = studentName;
  document.getElementById("contrib-amount").value = amount || 2000;
  document.getElementById("contrib-paid-checkbox").checked = Boolean(isPaid);
  contributionModal.show();
}

// Add member submit handler
document.getElementById("add-member-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("member-email").value.trim();
  const role = document.getElementById("member-role").value;

  try {
    const res = await authFetch(`/hostels/${currentHostelId}/members`, {
      method: "POST",
      body: JSON.stringify({ email, role })
    });

    addMemberModal.hide();
    showAlert("alert-container", `Student ${res.user_name} added to the hostel successfully!`, "success");
    await loadMembersPageData();
  } catch (err) {
    showAlert("modal-member-alert", err.message, "danger");
  }
});

// Contribution submit handler
document.getElementById("contribution-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const studentId = parseInt(document.getElementById("contrib-student-id").value, 10);
  const recordIdStr = document.getElementById("contrib-record-id").value;
  const amount = parseFloat(document.getElementById("contrib-amount").value);
  const paid = document.getElementById("contrib-paid-checkbox").checked;

  try {
    if (recordIdStr) {
      // Update existing contribution
      const recordId = parseInt(recordIdStr, 10);
      await authFetch(`/contributions/${recordId}`, {
        method: "PUT",
        body: JSON.stringify({ amount, paid })
      });
    } else {
      // Create new contribution
      await authFetch("/contributions", {
        method: "POST",
        body: JSON.stringify({
          monthly_fund_id: currentFundId,
          student_id: studentId,
          amount: amount,
          paid: paid
        })
      });
    }

    contributionModal.hide();
    showAlert("alert-container", "Contribution recorded successfully!", "success");
    await loadMembersPageData();
  } catch (err) {
    showAlert("modal-contrib-alert", err.message, "danger");
  }
});

// Remove member
async function removeMember(userId, userName) {
  if (!confirm(`Are you sure you want to remove ${userName} from this hostel?`)) {
    return;
  }

  try {
    await authFetch(`/hostels/${currentHostelId}/members/${userId}`, {
      method: "DELETE"
    });

    showAlert("alert-container", `${userName} removed from the hostel.`, "info");
    await loadMembersPageData();
  } catch (err) {
    showAlert("alert-container", "Failed to remove member: " + err.message, "danger");
  }
}
