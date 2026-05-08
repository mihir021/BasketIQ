import { loginAdmin } from "./api.js";


const TOKEN_KEY = "grocerypulse_admin_token";
const ADMIN_KEY = "grocerypulse_admin_profile";


function saveSession(payload) {
  localStorage.setItem(TOKEN_KEY, payload.token);
  localStorage.setItem(ADMIN_KEY, JSON.stringify(payload.admin));
}


export function getSession() {
  const token = localStorage.getItem(TOKEN_KEY);
  const rawAdmin = localStorage.getItem(ADMIN_KEY);
  if (!token || !rawAdmin) {
    return { token: "", admin: null };
  }

  try {
    return { token, admin: JSON.parse(rawAdmin) };
  } catch {
    clearSession();
    return { token: "", admin: null };
  }
}


export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ADMIN_KEY);
}


export function mountAdminChrome() {
  const session = getSession();
  const adminName = document.querySelector("[data-admin-name]");
  if (adminName) {
    adminName.textContent = session.admin?.name || "Guest";
  }

  document.querySelectorAll("[data-logout]").forEach((button) => {
    button.addEventListener("click", () => {
      clearSession();
      window.location.href = "/admin/portal/";
    });
  });
}


export function initAdminSession(onAuthenticatedLoad) {
  const session = getSession();
  const loginPanel = document.querySelector("#login-panel");
  const pagePanels = document.querySelectorAll("[data-page-panel]");
  const loginForm = document.querySelector("#login-form");
  const loginFeedback = document.querySelector("#login-feedback");

  async function showAuthedState() {
    loginPanel?.classList.add("hidden");
    pagePanels.forEach((panel) => panel.classList.remove("hidden"));
    mountAdminChrome();
    await onAuthenticatedLoad(getSession());
  }

  if (session.token) {
    showAuthedState().catch(() => {
      clearSession();
      loginPanel?.classList.remove("hidden");
      pagePanels.forEach((panel) => panel.classList.add("hidden"));
      if (loginFeedback) {
        loginFeedback.textContent = "Session expired. Please sign in again.";
      }
    });
  } else {
    loginPanel?.classList.remove("hidden");
    pagePanels.forEach((panel) => panel.classList.add("hidden"));
  }

  loginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(loginForm);
    if (loginFeedback) {
      loginFeedback.textContent = "Signing in...";
    }

    try {
      const payload = await loginAdmin(formData.get("email"), formData.get("password"));
      saveSession(payload);
      if (loginFeedback) {
        loginFeedback.textContent = `Welcome back, ${payload.admin.name}.`;
      }
      await showAuthedState();
    } catch (error) {
      if (loginFeedback) {
        loginFeedback.textContent = error.message;
      }
    }
  });
}
