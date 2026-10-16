// Login logic
redirectIfLoggedIn();

// Check if redirected due to expired session
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get("expired")) {
  showAlert("alert-container", "Your session has expired. Please log in again.", "warning");
}

function quickFill(email) {
  document.getElementById("email").value = email;
  document.getElementById("password").value = "password123";
}

const loginForm = document.getElementById("login-form");
const loginBtn = document.getElementById("login-btn");
const btnText = document.getElementById("btn-text");
const btnSpinner = document.getElementById("btn-spinner");

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  if (!email || !password) {
    showAlert("alert-container", "Please enter both email and password.", "danger");
    return;
  }

  // Show loading spinner
  loginBtn.disabled = true;
  btnText.textContent = "Signing in...";
  btnSpinner.classList.remove("d-none");

  try {
    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Invalid email or password");
    }

    // Save token and user details to localStorage
    setSession(data.access_token, data.user);

    showAlert("alert-container", "Login successful! Redirecting...", "success");

    setTimeout(() => {
      window.location.href = "dashboard.html";
    }, 600);

  } catch (err) {
    showAlert("alert-container", err.message || "Invalid email or password", "danger");
  } finally {
    loginBtn.disabled = false;
    btnText.textContent = "Sign In";
    btnSpinner.classList.add("d-none");
  }
});
