const BASE_URL = window.location.origin;

/**
 * api.js - Centralized API handler for BasketIQ.
 * Ensures consistent "token" usage and provides debugging logs.
 * All fetch calls are simplified for 2nd-year level understanding.
 */
const api = {
    // --- 1. AUTHENTICATION & SESSION ---

    async signup(data) {
        console.log("🛠️ Attempting Signup for:", data.email);
        const response = await fetch(`${BASE_URL}/api/auth/signup/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        console.log("📩 Signup API Result:", result);
        return result;
    },

    async login(data) {
        console.log("🛠️ Attempting Login...");
        const response = await fetch(`${BASE_URL}/api/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok && result.token) {
            console.log("✅ Login Success! Token:", result.token);
            // Securely store the token and user name
            localStorage.setItem("token", result.token);
            localStorage.setItem("user_name", result.name);
        } else {
            console.error("❌ Login Failed Error:", result.error || result.detail);
        }
        return result;
    },

    logout() {
        console.log("🚪 Logging out... clearing storage.");
        localStorage.clear();
        window.location.href = '/login/';
    },

    // --- 2. PRODUCTS (GROCERY CATALOG) ---

    async fetchProducts(search = '', category = 'All') {
        let url = `${BASE_URL}/api/auth/products/?search=${search}&category=${category}`;
        console.log("🔍 Fetching products from:", url);
        const response = await fetch(url);
        return response.json();
    },

    async getBestSellers() {
        const response = await fetch(`${BASE_URL}/api/auth/products/best-sellers/`);
        return response.json();
    },

    async getOffers() {
        const response = await fetch(`${BASE_URL}/api/auth/products/offers/`);
        return response.json();
    },

    // --- 3. PROFILE & EXPENSES ---

    // --- 3. PROFILE, EXPENSES & ORDERS ---
    getAuthHeader() {
        const token = localStorage.getItem('token');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },

    async getProfile() {
        const response = await fetch(`${BASE_URL}/api/profile/profile/`, {
            headers: this.getAuthHeader()
        });
        return response.json();
    },

    async updateProfile(data) {
        const response = await fetch(`${BASE_URL}/api/profile/profile/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...this.getAuthHeader()
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async getExpenses() {
        const response = await fetch(`${BASE_URL}/api/expenses/expenses/`, {
            headers: this.getAuthHeader()
        });
        return response.json();
    },

    async addExpense(data) {
        const response = await fetch(`${BASE_URL}/api/expenses/expenses/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...this.getAuthHeader()
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async getExpenseGraph(type) {
        const response = await fetch(`${BASE_URL}/api/expenses/expense-graph/${type}/`, {
            headers: this.getAuthHeader()
        });
        return response.json();
    },

    async getOrders() {
        const response = await fetch(`${BASE_URL}/api/orders/orders/`, {
            headers: this.getAuthHeader()
        });
        return response.json();
    }
};

// --- ADMIN API ENDPOINTS ---
export async function loginAdmin(email, password) {
  const response = await fetch("/admin/auth/login", {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error('Invalid credentials');
  return response.json();
}

export async function fetchAdminDashboard(token, range = '7d') {
  const response = await fetch("/admin/dashboard/summary?range=${range}", {
    headers: { 'Authorization': "Bearer ${token}" }
  });
  if (!response.ok) throw new Error('Failed to fetch dashboard data');
  return response.json();
}

export async function fetchOperationsSummary(token, range = '7d') {
  const response = await fetch("/admin/operations/summary?range=${range}", {
    headers: { 'Authorization': "Bearer ${token}" }
  });
  return response.json();
}

export async function fetchUserInsights(token) {
  const response = await fetch("/admin/users/insights", {
    headers: { 'Authorization': "Bearer ${token}" }
  });
  return response.json();
}

export async function fetchAdminLogs(token) {
  const response = await fetch("/admin/admin-logs", {
    headers: { 'Authorization': "Bearer ${token}" }
  });
  return response.json();
}
