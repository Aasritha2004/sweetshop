// ==================== GLOBAL VARIABLES ====================
const API_BASE = "http://127.0.0.1:8000/api";
let sweetsData = [];
let cart = [];
let currentUser = null;

// ==================== API HELPER ====================
async function apiRequest(endpoint, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = localStorage.getItem("token");
  
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Request failed");
    }

    return method === "DELETE" ? null : await response.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}

// ==================== INITIALIZATION ====================
async function init() {
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "login.html";
    return;
  }

  try {
    await loadUserProfile();
    await loadSweets();
    updateCartDisplay();
  } catch (error) {
    console.error("Init error:", error);
    if (error.message.includes("401") || error.message.includes("Invalid token")) {
      localStorage.clear();
      window.location.href = "login.html";
    }
  }
}

// ==================== USER PROFILE ====================
async function loadUserProfile() {
  try {
    currentUser = await apiRequest("/auth/me");
    
    document.getElementById("userName").textContent = currentUser.username;
    document.getElementById("userInitial").textContent = currentUser.username.charAt(0).toUpperCase();
    document.getElementById("accName").textContent = currentUser.username;
    document.getElementById("accEmail").textContent = currentUser.email;
    document.getElementById("accMobile").textContent = currentUser.mobile;
    document.getElementById("accAddress").textContent = currentUser.address;
    document.getElementById("accRole").textContent = currentUser.role;

    if (currentUser.role === "admin") {
      document.getElementById("addSweetBtn").style.display = "block";
      document.getElementById("accRole").style.background = "#dc3545";
    }
  } catch (error) {
    console.error("Failed to load user profile:", error);
    throw error;
  }
}

function toggleAccountDropdown() {
  const dropdown = document.getElementById("accountDropdown");
  dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

window.addEventListener('click', (e) => {
  const dropdown = document.getElementById("accountDropdown");
  const accountBox = document.getElementById("userAccount");
  if (!accountBox.contains(e.target)) {
    dropdown.style.display = "none";
  }
});

function logout() {
  localStorage.clear();
  window.location.href = "login.html";
}

// ==================== LOAD SWEETS ====================
async function loadSweets() {
  const sweetList = document.getElementById("sweetList");
  sweetList.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading sweets...</p></div>';

  try {
    const search = document.getElementById("search").value.toLowerCase();
    const category = document.getElementById("categoryFilter").value;
    const minPrice = document.getElementById("minPrice").value;
    const maxPrice = document.getElementById("maxPrice").value;

    let endpoint = "/sweets";
    const params = new URLSearchParams();
    
    if (search) params.append("name", search);
    if (category) params.append("category", category);
    if (minPrice) params.append("min_price", minPrice);
    if (maxPrice) params.append("max_price", maxPrice);

    if (params.toString()) {
      endpoint = `/sweets/search?${params.toString()}`;
    }

    sweetsData = await apiRequest(endpoint);
    
    sweetsData.forEach(sweet => {
      if (!sweet.selectedWeight) sweet.selectedWeight = 100;
    });

    displaySweets();
  } catch (error) {
    sweetList.innerHTML = `<div class="loading"><p style="color: #dc3545;">Failed to load sweets: ${error.message}</p></div>`;
  }
}

function displaySweets() {
  const sweetList = document.getElementById("sweetList");
  
  if (sweetsData.length === 0) {
    sweetList.innerHTML = '<div class="loading"><p>No sweets found matching your criteria.</p></div>';
    return;
  }

  sweetList.innerHTML = "";

  sweetsData.forEach(sweet => {
    const isOutOfStock = sweet.quantity === 0;
    const isAdmin = currentUser && currentUser.role === "admin";

    const div = document.createElement("div");
    div.className = "sweet-card";
    div.innerHTML = `
      <img src="${sweet.img}" alt="${sweet.name}" onerror="this.src='assets/Images/logo.jpg'">
      <div class="card-body">
        <h3>${sweet.name}</h3>
        <span class="category-badge">${sweet.category}</span>
        <p class="price">₹${sweet.price}<span style="font-size: 0.8rem; font-weight: normal;">/100g</span></p>
        <div class="stock-info">
          <span class="stock-badge ${isOutOfStock ? 'out-of-stock' : 'in-stock'}">
            ${isOutOfStock ? 'Out of Stock' : `${sweet.quantity} in stock`}
          </span>
        </div>
        
        <div class="weight-bar">
          <button onclick="decreaseWeight(${sweet.id})" ${isOutOfStock ? 'disabled' : ''}>−</button>
          <span class="weight-display" id="weight-${sweet.id}">${sweet.selectedWeight}g</span>
          <button onclick="increaseWeight(${sweet.id})" ${isOutOfStock ? 'disabled' : ''}>+</button>
        </div>

        <div class="card-actions">
          <button class="btn-add-cart" onclick="addToCart(${sweet.id})" ${isOutOfStock ? 'disabled' : ''}>
            ${isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
          </button>
          ${isAdmin ? `
            <button class="btn-edit" onclick="editSweet(${sweet.id})" title="Edit">✏️</button>
            <button class="btn-delete" onclick="deleteSweet(${sweet.id})" title="Delete">🗑️</button>
          ` : ''}
        </div>
      </div>
    `;
    sweetList.appendChild(div);
  });
}

// ==================== WEIGHT CONTROLS ====================
function increaseWeight(id) {
  const sweet = sweetsData.find(s => s.id === id);
  sweet.selectedWeight += 50;
  document.getElementById(`weight-${id}`).textContent = sweet.selectedWeight + 'g';
}

function decreaseWeight(id) {
  const sweet = sweetsData.find(s => s.id === id);
  if (sweet.selectedWeight > 100) {
    sweet.selectedWeight -= 50;
    document.getElementById(`weight-${id}`).textContent = sweet.selectedWeight + 'g';
  }
}

// ==================== CART MANAGEMENT ====================
function addToCart(id) {
  const sweet = sweetsData.find(s => s.id === id);
  const existing = cart.find(c => c.sweetId === id);

  if (existing) {
    existing.weight += sweet.selectedWeight;
  } else {
    cart.push({
      sweetId: id,
      name: sweet.name,
      price: sweet.price,
      weight: sweet.selectedWeight,
      img: sweet.img
    });
  }

  sweet.selectedWeight = 100;
  document.getElementById(`weight-${id}`).textContent = '100g';
  
  updateCartDisplay();
  showNotification(`${sweet.name} added to cart!`, 'success');
}

function updateCartDisplay() {
  document.getElementById("cartCount").textContent = cart.length;
  renderCart();
}

function toggleCart() {
  document.getElementById("cartSidebar").classList.toggle("open");
}

function renderCart() {
  const container = document.getElementById("cartItems");
  const totalEl = document.getElementById("cartTotal");
  const checkoutBtn = document.getElementById("checkoutBtn");

  if (cart.length === 0) {
    container.innerHTML = `
      <div class="empty-cart">
        <svg width="80" height="80" viewBox="0 0 24 24" fill="#ccc">
          <path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>
        </svg>
        <p>Your cart is empty</p>
      </div>
    `;
    totalEl.textContent = "₹0.00";
    checkoutBtn.style.display = "none";
    return;
  }

  let total = 0;
  container.innerHTML = "";

  cart.forEach((item, index) => {
    const itemTotal = (item.price * item.weight) / 100;
    total += itemTotal;

    const div = document.createElement("div");
    div.className = "cart-item";
    div.innerHTML = `
      <div class="cart-item-info">
        <div class="cart-item-name">${item.name}</div>
        <div class="cart-item-details">${item.weight}g × ₹${item.price}/100g = ₹${itemTotal.toFixed(2)}</div>
      </div>
      <div class="cart-item-actions">
        <button onclick="increaseCartWeight(${index})" title="Add 50g">+</button>
        <button onclick="decreaseCartWeight(${index})" title="Remove 50g">−</button>
        <button class="btn-remove" onclick="removeFromCart(${index})" title="Remove">×</button>
      </div>
    `;
    container.appendChild(div);
  });

  totalEl.textContent = `₹${total.toFixed(2)}`;
  checkoutBtn.style.display = "block";
}

function increaseCartWeight(index) {
  cart[index].weight += 50;
  renderCart();
}

function decreaseCartWeight(index) {
  if (cart[index].weight > 100) {
    cart[index].weight -= 50;
    renderCart();
  }
}

function removeFromCart(index) {
  cart.splice(index, 1);
  updateCartDisplay();
}

// ==================== CHECKOUT ====================
function checkout() {
  if (cart.length === 0) {
    showNotification('Your cart is empty!', 'error');
    return;
  }

  // Save cart to localStorage for payment page
  localStorage.setItem('cart', JSON.stringify(cart));
  
  // Redirect to payment page
  window.location.href = 'payment.html';
}

// ==================== ADMIN FUNCTIONS ====================
function showAddSweet() {
  document.getElementById("modalTitle").textContent = "Add New Sweet";
  document.getElementById("sweetForm").reset();
  document.getElementById("sweetId").value = "";
  document.getElementById("editModal").classList.add("active");
}

async function editSweet(id) {
  const sweet = sweetsData.find(s => s.id === id);
  if (!sweet) return;

  document.getElementById("modalTitle").textContent = "Edit Sweet";
  document.getElementById("sweetId").value = sweet.id;
  document.getElementById("sweetName").value = sweet.name;
  document.getElementById("sweetCategory").value = sweet.category;
  document.getElementById("sweetPrice").value = sweet.price;
  document.getElementById("sweetQuantity").value = sweet.quantity;
  document.getElementById("sweetDescription").value = sweet.description || "";
  document.getElementById("sweetImg").value = sweet.img;
  document.getElementById("editModal").classList.add("active");
}

async function saveSweetForm(e) {
  e.preventDefault();

  const id = document.getElementById("sweetId").value;
  const sweetData = {
    name: document.getElementById("sweetName").value,
    category: document.getElementById("sweetCategory").value,
    price: parseFloat(document.getElementById("sweetPrice").value),
    quantity: parseInt(document.getElementById("sweetQuantity").value),
    description: document.getElementById("sweetDescription").value,
    img: document.getElementById("sweetImg").value
  };

  try {
    if (id) {
      await apiRequest(`/sweets/${id}`, "PUT", sweetData);
      showNotification("Sweet updated successfully!", 'success');
    } else {
      await apiRequest("/sweets", "POST", sweetData);
      showNotification("Sweet added successfully!", 'success');
    }
    
    closeEditModal();
    await loadSweets();
  } catch (error) {
    showNotification(`Failed: ${error.message}`, 'error');
  }
}

async function deleteSweet(id) {
  if (!confirm("Are you sure you want to delete this sweet?")) return;

  try {
    await apiRequest(`/sweets/${id}`, "DELETE");
    showNotification("Sweet deleted successfully!", 'success');
    await loadSweets();
  } catch (error) {
    showNotification(`Failed to delete: ${error.message}`, 'error');
  }
}

function closeEditModal() {
  document.getElementById("editModal").classList.remove("active");
}

// ==================== PURCHASE HISTORY ====================
async function viewPurchaseHistory() {
  document.getElementById("historyModal").classList.add("active");
  const content = document.getElementById("historyContent");
  
  content.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading history...</p></div>';

  try {
    const history = await apiRequest("/purchases/history");
    
    if (history.length === 0) {
      content.innerHTML = '<p style="text-align: center; color: #999;">No purchase history found.</p>';
      return;
    }

    content.innerHTML = history.map(purchase => `
      <div class="cart-item" style="margin-bottom: 1rem;">
        <div class="cart-item-info">
          <div class="cart-item-name">${purchase.sweet_name}</div>
          <div class="cart-item-details">
            Quantity: ${purchase.quantity} | Total: ₹${purchase.total_price.toFixed(2)}
            <br>
            <small>${new Date(purchase.purchase_date).toLocaleString()}</small>
          </div>
        </div>
      </div>
    `).join('');
  } catch (error) {
    content.innerHTML = `<p style="color: #dc3545;">Failed to load history: ${error.message}</p>`;
  }
}

function closeHistoryModal() {
  document.getElementById("historyModal").classList.remove("active");
}

// ==================== NOTIFICATIONS ====================
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#6495ed'};
    color: white;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;
  notification.textContent = message;
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(400px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(400px); opacity: 0; }
  }
`;
document.head.appendChild(style);

// ==================== INITIALIZE ====================
init();