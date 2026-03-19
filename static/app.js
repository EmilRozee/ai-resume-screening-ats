const output = document.getElementById("output");
const tokenInput = document.getElementById("token");
const authState = document.getElementById("auth-state");
const roleState = document.getElementById("role-state");
const tabAdmin = document.getElementById("tab-admin");
const tabCandidate = document.getElementById("tab-candidate");

let currentView = "admin";
let currentRole = "guest";

function authHeader() {
  const token = tokenInput.value.trim();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function show(data) {
  output.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

function decodeTokenRole(token) {
  if (!token || token.split(".").length < 2) {
    return "guest";
  }

  try {
    const payloadPart = token.split(".")[1];
    const base64 = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(base64);
    const payload = JSON.parse(json);
    return payload.role || "guest";
  } catch {
    return "guest";
  }
}

function applyView() {
  tabAdmin.classList.toggle("active", currentView === "admin");
  tabCandidate.classList.toggle("active", currentView === "candidate");

  document.querySelectorAll(".role-card").forEach((el) => {
    const cardView = el.dataset.view;
    const hiddenByTab = cardView !== currentView;
    const hiddenByRole = currentRole !== "admin" && cardView === "admin";
    const hiddenByCandidateRole = currentRole !== "candidate" && cardView === "candidate";
    const shouldHide = hiddenByTab || hiddenByRole || hiddenByCandidateRole;
    el.classList.toggle("hidden", shouldHide);
  });
}

function setRoleState(role) {
  currentRole = role || "guest";
  const isLoggedIn = currentRole === "admin" || currentRole === "candidate";

  authState.textContent = isLoggedIn ? "Logged in" : "Not logged in";
  roleState.textContent = `Role: ${currentRole}`;

  if (currentRole === "admin") {
    currentView = "admin";
  }
  if (currentRole === "candidate") {
    currentView = "candidate";
  }

  applyView();
}

async function parseResponse(response) {
  const text = await response.text();
  let data;

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }

  if (!response.ok) {
    throw { status: response.status, data };
  }

  return data;
}

async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    const data = await parseResponse(response);
    show(data);
    return data;
  } catch (err) {
    const payload = {
      error: "Request failed",
      status: err.status || 500,
      details: err.data || err.message || err
    };
    show(payload);
    throw err;
  }
}

document.getElementById("register-btn").addEventListener("click", async () => {
  const username = document.getElementById("reg-username").value.trim();
  const password = document.getElementById("reg-password").value;
  const role = document.getElementById("reg-role").value;

  await apiCall("/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, role })
  });
});

document.getElementById("login-btn").addEventListener("click", async () => {
  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value;

  const data = await apiCall("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  if (data.token) {
    tokenInput.value = data.token;
    setRoleState(decodeTokenRole(data.token));
  }
});

document.getElementById("profile-btn").addEventListener("click", async () => {
  await apiCall("/profile", {
    method: "GET",
    headers: {
      ...authHeader()
    }
  });
});

document.getElementById("create-job-btn").addEventListener("click", async () => {
  const title = document.getElementById("job-title").value.trim();
  const description = document.getElementById("job-description").value.trim();
  const skills_required = document.getElementById("job-skills").value.trim();

  await apiCall("/create-job", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader()
    },
    body: JSON.stringify({ title, description, skills_required })
  });
});

document.getElementById("load-jobs-btn").addEventListener("click", async () => {
  const jobs = await apiCall("/jobs", {
    method: "GET",
    headers: {
      ...authHeader()
    }
  });

  renderJobs(Array.isArray(jobs) ? jobs : []);
});

document.getElementById("load-apps-btn").addEventListener("click", async () => {
  await apiCall("/applications", {
    method: "GET",
    headers: {
      ...authHeader()
    }
  });
});

tabAdmin.addEventListener("click", () => {
  currentView = "admin";
  applyView();
});

tabCandidate.addEventListener("click", () => {
  currentView = "candidate";
  applyView();
});

document.getElementById("logout-btn").addEventListener("click", () => {
  tokenInput.value = "";
  setRoleState("guest");
  show({ message: "Logged out from UI state." });
});

document.getElementById("apply-btn").addEventListener("click", async () => {
  const jobId = document.getElementById("apply-job-id").value.trim();
  const fileInput = document.getElementById("resume-file");
  const file = fileInput.files[0];

  if (!jobId || !file) {
    show({ error: "Job ID and resume file are required" });
    return;
  }

  const formData = new FormData();
  formData.append("resume", file);

  await apiCall(`/apply-job/${jobId}`, {
    method: "POST",
    headers: {
      ...authHeader()
    },
    body: formData
  });
});

function renderJobs(jobs) {
  const list = document.getElementById("jobs-list");
  list.innerHTML = "";

  if (!jobs.length) {
    list.innerHTML = "<p>No jobs found.</p>";
    return;
  }

  jobs.forEach((job) => {
    const el = document.createElement("div");
    el.className = "job-item";
    el.innerHTML = `
      <strong>#${job.id} - ${job.title}</strong>
      <p>${job.description}</p>
      <p><b>Skills:</b> ${job.skills_required || "N/A"}</p>
      <button data-job-id="${job.id}">Use This Job ID</button>
    `;

    const btn = el.querySelector("button");
    btn.addEventListener("click", () => {
      document.getElementById("apply-job-id").value = job.id;
      show({ message: `Job ID ${job.id} selected for apply form.` });
    });

    list.appendChild(el);
  });
}

setRoleState("guest");
