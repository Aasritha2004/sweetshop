const API_BASE = "http://127.0.0.1:8000/api";

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const loginBtn = document.getElementById("loginBtn");
  const errorMsg = document.getElementById("errorMessage");
  const successMsg = document.getElementById("successMessage");

  errorMsg.style.display = "none";
  successMsg.style.display = "none";

  loginBtn.disabled = true;
  loginBtn.innerHTML =
    '<span class="loading-spinner"></span>Logging in...';

  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Login failed");
    }

    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);

    successMsg.textContent = "Login successful! Redirecting...";
    successMsg.style.display = "block";

    setTimeout(() => {
      window.location.href = "dashboard.html";
    }, 1000);
  } catch (error) {
    errorMsg.textContent = error.message;
    errorMsg.style.display = "block";
    loginBtn.disabled = false;
    loginBtn.innerHTML = "Login";
  }
});

if (localStorage.getItem("token")) {
  window.location.href = "dashboard.html";
}
