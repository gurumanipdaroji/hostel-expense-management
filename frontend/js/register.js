// Registration logic
redirectIfLoggedIn();

const registerForm = document.getElementById("register-form");
const registerBtn = document.getElementById("register-btn");
const btnText = document.getElementById("btn-text");
const btnSpinner = document.getElementById("btn-spinner");

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirm-password").value;

  if (password !== confirmPassword) {
    showAlert("alert-container", "Passwords do not match. Please re-enter.", "danger");
    return;
  }

  registerBtn.disabled = true;
  btnText.textContent = "Creating Account...";
  btnSpinner.classList.remove("d-none");

  try {
    // 1. Register user
    const res = await fetch(`${BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Registration failed. Please try again.");
    }

    // 2. Auto-login immediately after registration for seamless UX
    const loginRes = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const loginData = await loginRes.json();
    if (loginRes.ok) {
      setSession(loginData.access_token, loginData.user);
      showAlert("alert-container", "Account created successfully! Redirecting to dashboard...", "success");
      setTimeout(() => {
        window.location.href = "dashboard.html";
      }, 700);
    } else {
      showAlert("alert-container", "Account created! Please sign in with your credentials.", "success");
      setTimeout(() => {
        window.location.href = "login.html";
      }, 1000);
    }

  } catch (err) {
    showAlert("alert-container", err.message || "An error occurred during registration", "danger");
  } finally {
    registerBtn.disabled = false;
    btnText.textContent = "Create Account";
    btnSpinner.classList.add("d-none");
  }
});
