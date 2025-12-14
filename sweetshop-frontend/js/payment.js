const API_BASE = "http://127.0.0.1:8000/api";
let cartData = [];
let selectedPaymentMethod = 'card';
let selectedUpiApp = null;

function loadCart() {
  cartData = JSON.parse(localStorage.getItem('cart') || '[]');
  displayOrderSummary();
}

function displayOrderSummary() {
  const orderItems = document.getElementById('orderItems');
  if (cartData.length === 0) {
    orderItems.innerHTML = '<p style="text-align:center;color:#999;">No items in cart</p>';
    return;
  }

  let subtotal = 0;
  orderItems.innerHTML = '';

  cartData.forEach(item => {
    const itemTotal = (item.price * item.weight) / 100;
    subtotal += itemTotal;

    orderItems.innerHTML += `
      <div class="order-item">
        <div class="item-details">
          <div class="item-name">${item.name}</div>
          <div class="item-quantity">${item.weight}g</div>
        </div>
        <div class="item-price">₹${itemTotal.toFixed(2)}</div>
      </div>`;
  });

  const deliveryFee = subtotal > 500 ? 0 : 40;
  const gst = subtotal * 0.05;
  const total = subtotal + deliveryFee + gst;

  document.getElementById('subtotal').textContent = `₹${subtotal.toFixed(2)}`;
  document.getElementById('deliveryFee').textContent = deliveryFee === 0 ? 'FREE' : `₹${deliveryFee}`;
  document.getElementById('gst').textContent = `₹${gst.toFixed(2)}`;
  document.getElementById('totalAmount').textContent = `₹${total.toFixed(2)}`;
}

function selectPayment(method) {
  selectedPaymentMethod = method;
  document.querySelectorAll('.payment-method').forEach(m => m.classList.remove('active'));
  event.target.closest('.payment-method').classList.add('active');

  document.querySelectorAll('.payment-form').forEach(f => f.classList.remove('active'));
  document.getElementById(`${method}Form`).classList.add('active');
}

function selectUpiApp(el, app) {
  selectedUpiApp = app;
  document.querySelectorAll('.upi-app').forEach(a => a.classList.remove('selected'));
  el.classList.add('selected');
}

function goBack() {
  window.location.href = 'dashboard.html';
}

async function processPayment() {
  if (!validatePayment()) return;

  document.querySelector('.payment-wrapper').style.display = 'none';
  document.getElementById('loadingState').style.display = 'block';

  try {
    const token = localStorage.getItem('token');
    for (const item of cartData) {
      const quantity = Math.ceil(item.weight / 100);
      await fetch(`${API_BASE}/sweets/${item.sweetId}/purchase`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ quantity })
      });
    }

    setTimeout(() => {
      localStorage.removeItem('cart');
      document.getElementById('loadingState').style.display = 'none';
      document.getElementById('successMessage').style.display = 'block';
    }, 2000);

  } catch (err) {
    alert('Payment failed');
    document.getElementById('loadingState').style.display = 'none';
    document.querySelector('.payment-wrapper').style.display = 'grid';
  }
}

function validatePayment() {
  return true;
}

// Auto-format inputs
document.getElementById('cardNumber')?.addEventListener('input', e => {
  e.target.value = e.target.value.replace(/\s/g, '').match(/.{1,4}/g)?.join(' ') || '';
});

document.getElementById('cardExpiry')?.addEventListener('input', e => {
  let v = e.target.value.replace(/\D/g, '');
  if (v.length >= 2) v = v.substring(0, 2) + '/' + v.substring(2, 4);
  e.target.value = v;
});

loadCart();
