const API_BASE = "http://127.0.0.1:8000/api";

document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value;
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const mobile = document.getElementById("mobile").value;
  const address = document.getElementById("address").value;

  const registerBtn = document.getElementById("registerBtn");
  const errorMsg = document.getElementById("errorMessage");
  const successMsg = document.getElementById("successMessage");

  errorMsg.style.display = "none";
  successMsg.style.display = "none";

  if (!/^\d{10,15}$/.test(mobile)) {
    errorMsg.textContent = "Please enter a valid mobile number (10-15 digits)";
    errorMsg.style.display = "block";
    return;
  }

  registerBtn.disabled = true;
  registerBtn.innerHTML =
    '<span class="loading-spinner"></span>Creating account...';

  try {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username,
        email,
        password,
        mobile,
        address,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Registration failed");
    }

    successMsg.textContent =
      "Account created successfully! Redirecting to login...";
    successMsg.style.display = "block";

    document.getElementById("registerForm").reset();

    setTimeout(() => {
      window.location.href = "login.html";
    }, 2000);
  } catch (error) {
    errorMsg.textContent = error.message;
    errorMsg.style.display = "block";
    registerBtn.disabled = false;
    registerBtn.innerHTML = "Create Account";
  }
});

if (localStorage.getItem("token")) {
  window.location.href = "dashboard.html";
}
