/* Sessao autenticada Fase A+ — marca SADS */

const SESSION_KEYS = {
  token: "rf_access_token",
  companyId: "rf_company_id",
  companyName: "rf_company_name",
  employeeId: "rf_employee_id",
  employeeName: "rf_employee_name",
  employeeEmail: "rf_employee_email",
  role: "rf_role",
};

const ASSET_VER = "clean2";
const THEME_KEY = "rf_theme";

function getTheme() {
  const t = localStorage.getItem(THEME_KEY);
  return t === "light" ? "light" : "dark";
}

function applyTheme(theme) {
  const mode = theme === "light" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", mode);
  localStorage.setItem(THEME_KEY, mode);
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    const isLight = mode === "light";
    btn.setAttribute("aria-pressed", isLight ? "true" : "false");
    btn.title = isLight ? "Mudar para modo noturno" : "Mudar para modo claro";
    btn.textContent = isLight ? "☾ Noturno" : "☀ Claro";
  });
}

function toggleTheme() {
  applyTheme(getTheme() === "light" ? "dark" : "light");
}

applyTheme(getTheme());

function getSession() {
  return {
    token: localStorage.getItem(SESSION_KEYS.token),
    companyId: localStorage.getItem(SESSION_KEYS.companyId),
    companyName: localStorage.getItem(SESSION_KEYS.companyName),
    employeeId: localStorage.getItem(SESSION_KEYS.employeeId),
    employeeName: localStorage.getItem(SESSION_KEYS.employeeName),
    employeeEmail: localStorage.getItem(SESSION_KEYS.employeeEmail),
    role: localStorage.getItem(SESSION_KEYS.role),
  };
}

function isLoggedIn() {
  const s = getSession();
  return Boolean(s.token && s.companyId && s.employeeId);
}

function setAuthSession(auth) {
  const user = auth.user || auth;
  if (auth.access_token) {
    localStorage.setItem(SESSION_KEYS.token, auth.access_token);
  }
  localStorage.setItem(SESSION_KEYS.companyId, user.company_id);
  localStorage.setItem(SESSION_KEYS.companyName, user.company_name || "");
  localStorage.setItem(SESSION_KEYS.employeeId, user.employee_id);
  localStorage.setItem(SESSION_KEYS.employeeName, user.name || "");
  localStorage.setItem(SESSION_KEYS.employeeEmail, user.email || "");
  localStorage.setItem(SESSION_KEYS.role, user.role || "admin");
}

function setCompanySession(id, name) {
  localStorage.setItem(SESSION_KEYS.companyId, id);
  localStorage.setItem(SESSION_KEYS.companyName, name || "");
}

function setEmployeeSession(id, name) {
  localStorage.setItem(SESSION_KEYS.employeeId, id);
  localStorage.setItem(SESSION_KEYS.employeeName, name || "");
}

function clearSession() {
  Object.values(SESSION_KEYS).forEach((k) => localStorage.removeItem(k));
}

function requireCompany(redirect = "/register.html") {
  return requireAuth(redirect);
}

function requireEmployee(redirect = "/login.html") {
  return requireAuth(redirect);
}

function requireAuth(redirect = "/login.html") {
  const s = getSession();
  if (!isLoggedIn()) {
    window.location.href = redirect;
    return null;
  }
  return s;
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const s = getSession();
  if (s.token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${s.token}`);
  }
  const hasBody = options.body != null && options.body !== "";
  if (hasBody && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(path, { ...options, headers });
  let data = null;
  const text = await res.text();
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!res.ok) {
    if (res.status === 401 && !String(path).includes("/auth/login") && !String(path).includes("/auth/register")) {
      clearSession();
    }
    const detail = data?.detail || data?.message || res.statusText;
    let msg;
    if (typeof detail === "string") msg = detail;
    else if (Array.isArray(detail)) {
      msg = detail
        .map((d) => (d.msg ? `${(d.loc || []).join(".")}: ${d.msg}` : JSON.stringify(d)))
        .join("; ");
    } else msg = JSON.stringify(detail);
    throw new Error(msg || res.statusText);
  }
  return data;
}

function moneyBRL(v) {
  const n = Number(v || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function ensureBrandAssets() {
  if (!document.querySelector(".brand-ribbon")) {
    const ribbon = document.createElement("div");
    ribbon.className = "brand-ribbon";
    ribbon.setAttribute("aria-hidden", "true");
    document.body.prepend(ribbon);
  }
  let icon = document.querySelector('link[rel="icon"]');
  if (!icon) {
    icon = document.createElement("link");
    icon.rel = "icon";
    document.head.appendChild(icon);
  }
  icon.href = `/static/assets/sads-logo.png?v=${ASSET_VER}`;

  const sheets = {
    "styles.css": `/static/styles.css?v=${ASSET_VER}`,
    "report.css": `/static/report.css?v=${ASSET_VER}`,
  };
  Object.entries(sheets).forEach(([name, wanted]) => {
    let linked = false;
    document.querySelectorAll('link[rel="stylesheet"]').forEach((link) => {
      if (String(link.href || "").includes(name)) {
        if (!String(link.href).includes(`v=${ASSET_VER}`)) {
          link.href = wanted;
        }
        linked = true;
      }
    });
    if (!linked && name === "styles.css" && !document.body.classList.contains("report-body")) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = wanted;
      document.head.appendChild(link);
    }
  });
}

function appNavItems() {
  return [
    { href: "dashboard.html", label: "Painel", icon: "◈" },
    { href: "project-new.html", label: "Novo projeto", icon: "＋" },
    { href: "applications.html", label: "Recomendações", icon: "◎" },
    { href: "materials.html", label: "Materiais", icon: "▤" },
    { href: "employee.html", label: "Equipe", icon: "☺" },
    { href: "#", label: "Perguntar", icon: "◉", disabled: true, title: "Chat — Fase B" },
  ];
}

function mountAppShell(active, s) {
  document.body.classList.add("app-mode");
  if (document.getElementById("app-shell")) {
    document.querySelectorAll(".app-nav a").forEach((a) => {
      a.classList.toggle("active", a.dataset.page === active);
    });
    return;
  }

  const nav = document.getElementById("nav");
  const main = document.querySelector("main");
  if (!nav || !main) return;

  const initials = String(s.employeeName || "U")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || "")
    .join("") || "U";

  const shell = document.createElement("div");
  shell.id = "app-shell";
  shell.className = "app-shell";
  shell.innerHTML = `
    <aside class="app-sidebar" aria-label="Navegação principal">
      <a class="app-logo" href="/dashboard.html" aria-label="SADS — painel">
        <img src="/static/assets/sads-logo.png?v=${ASSET_VER}" alt="" />
        <span>SADS</span>
      </a>
      <nav class="app-nav">
        ${appNavItems()
          .map((item) => {
            if (item.disabled) {
              return `<span class="app-nav-disabled" title="${item.title || ""}"><span class="ico">${item.icon}</span>${item.label}</span>`;
            }
            const cls = active === item.href ? "active" : "";
            return `<a class="${cls}" data-page="${item.href}" href="/${item.href}"><span class="ico">${item.icon}</span>${item.label}</a>`;
          })
          .join("")}
      </nav>
      <div class="app-sidebar-foot">
        <button type="button" class="btn ghost app-logout" id="nav-logout">Sair</button>
      </div>
    </aside>
    <div class="app-column">
      <header class="app-topbar">
        <div class="app-topbar-title">
          <span class="eyebrow">Área autenticada</span>
          <strong>${s.companyName || "Organização"}</strong>
        </div>
        <div class="app-topbar-user">
          <button type="button" class="btn ghost theme-toggle" data-theme-toggle aria-pressed="false">☀ Claro</button>
          <div class="app-user-meta">
            <strong>${s.employeeName || "—"}</strong>
            <span>${s.employeeEmail || s.role || ""}</span>
          </div>
          <div class="app-avatar" aria-hidden="true">${initials}</div>
        </div>
      </header>
      <div class="app-content" id="app-content"></div>
    </div>
  `;

  main.classList.add("app-wrap");
  shell.querySelector("#app-content").appendChild(main);
  nav.replaceWith(shell);
  applyTheme(getTheme());

  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.onclick = () => toggleTheme();
  });

  const logoutBtn = document.getElementById("nav-logout");
  if (logoutBtn) {
    logoutBtn.onclick = async () => {
      try {
        await api("/api/v1/auth/logout", { method: "POST" });
      } catch {
        /* ignore */
      }
      clearSession();
      location.href = "/";
    };
  }
}

function renderNav(active) {
  const s = getSession();
  ensureBrandAssets();
  const logged = isLoggedIn();

  if (logged && document.getElementById("nav") && document.querySelector("main") && !document.body.classList.contains("report-body")) {
    mountAppShell(active, s);
    return;
  }

  const el = document.getElementById("nav");
  if (!el) return;

  const links = logged
    ? [
        ["dashboard.html", "Painel", true],
        ["project-new.html", "Novo projeto", true],
        ["materials.html", "Materiais", true],
        ["applications.html", "Aplicacoes", true],
        ["employee.html", "Equipe", true],
        ["#", "Chat (Fase B)", false],
      ]
    : [
        ["", "Inicio", true],
        ["login.html", "Login", true],
        ["register.html", "Criar conta", true],
      ];

  el.innerHTML = `
    <div class="nav-brand">
      <a href="${logged ? "/dashboard.html" : "/"}" aria-label="SADS — inicio">
        <img src="/static/assets/sads-logo.png?v=${ASSET_VER}" alt="SADS" />
        <span class="brand-text">
          <span class="brand-tag">Sistema de Apoio a Decisao para Fomento a Inovacao</span>
        </span>
      </a>
    </div>
    <div class="nav-links">
      ${links
        .map(([href, label, enabled]) => {
          if (!enabled) {
            return `<span class="nav-disabled" title="Disponivel na Fase B">${label}</span>`;
          }
          const cls = active === href ? "active" : "";
          const url = href === "" ? "/" : `/${href}`;
          return `<a class="${cls}" href="${url}">${label}</a>`;
        })
        .join("")}
    </div>
    <div class="nav-user">
      ${
        logged
          ? `<span title="${s.employeeEmail || ""}">${s.employeeName || "—"} · ${s.companyName || ""}</span>
             <button class="btn ghost" type="button" id="nav-logout" style="margin-top:0;padding:0.35rem 0.7rem;font-size:0.8rem">Sair</button>`
          : `<a class="btn ghost" style="margin-top:0;padding:0.35rem 0.7rem;font-size:0.8rem" href="/login.html">Entrar</a>`
      }
    </div>
  `;
  const logoutBtn = document.getElementById("nav-logout");
  if (logoutBtn) {
    logoutBtn.onclick = async () => {
      try {
        await api("/api/v1/auth/logout", { method: "POST" });
      } catch {
        /* ignore */
      }
      clearSession();
      location.href = "/";
    };
  }
}

function showAlert(boxId, message, kind = "error") {
  const box = document.getElementById(boxId);
  if (!box) return;
  box.className = `alert ${kind}`;
  box.textContent = message;
  box.hidden = false;
}

function hideAlert(boxId) {
  const box = document.getElementById(boxId);
  if (!box) return;
  box.hidden = true;
}
