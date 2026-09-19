const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8001" : "";
const state = { files: [], audit: [], running: false };
const steps = ["Security Check", "Task Classification", "Document Extraction", "Document Retrieval", "Reasoning", "Evidence Verification", "Human Approval if required", "Deliverable Generation", "Completed"];
const pageTitles = { dashboard: "Control Center", workspace: "Agent Workspace", files: "Workspace Files", audit: "Audit Log", security: "Security Monitor", settings: "System Settings" };
const qs = (selector) => document.querySelector(selector);
const qsa = (selector) => [...document.querySelectorAll(selector)];

function toast(message) {
  const target = qs("#toast");
  if (!target) return;
  target.textContent = message;
  target.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => target.classList.remove("show"), 2600);
}
function navigate(page) {
  qsa(".page").forEach((item) => item.classList.toggle("active", item.id === page));
  qsa(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.page === page));
  qs("#page-title").textContent = pageTitles[page] || page;
  window.scrollTo({ top: 0, behavior: "smooth" });
}
qsa(".nav-item").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.page)));
qsa("[data-go]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.go)));

function addAudit(event, status = "SUCCESS") {
  state.audit.unshift({ time: new Date().toLocaleString(), event, actor: "Authorized User", status });
  qs("#auditBody").innerHTML = state.audit.map((item) => `<tr><td>${item.time}</td><td>${item.event}</td><td>${item.actor}</td><td class="ok">${item.status}</td></tr>`).join("");
}
function formatBytes(bytes) { return bytes < 1024 ? `${bytes} B` : `${(bytes / 1024).toFixed(1)} KB`; }
function fileKind(name) {
  const extension = name.split(".").pop().toLowerCase();
  if (extension === "pdf") return "PDF";
  if (["xlsx", "xlsm", "xls", "csv", "tsv"].includes(extension)) return "DATA";
  if (["docx", "doc", "txt", "md", "markdown"].includes(extension)) return "DOC";
  if (["pptx", "ppt"].includes(extension)) return "SLIDES";
  if (["png", "jpg", "jpeg", "tif", "tiff"].includes(extension)) return "IMAGE";
  return extension.toUpperCase() || "FILE";
}
function addFiles(fileList) {
  [...fileList].forEach((file) => {
    if (!state.files.some((existing) => existing.name === file.name && existing.size === file.size)) state.files.push(file);
  });
  renderFilePreview();
  renderFiles();
  qs("#fileCount").textContent = state.files.length;
  addAudit(`${fileList.length} file(s) added to workspace`);
  toast(`${fileList.length} file${fileList.length > 1 ? "s" : ""} added`);
}
function removeFile(index) {
  state.files.splice(index, 1);
  renderFilePreview(); renderFiles(); qs("#fileCount").textContent = state.files.length;
}
function renderFilePreview() {
  qs("#filePreview").innerHTML = state.files.map((file, index) => `<div class="file-chip"><span>${fileKind(file.name)}</span><strong>${file.name}</strong><small>${formatBytes(file.size)} · ready</small><button class="secondary-btn" data-remove-file="${index}" aria-label="Remove ${file.name}">×</button></div>`).join("");
  qsa("[data-remove-file]").forEach((button) => button.addEventListener("click", () => removeFile(Number(button.dataset.removeFile))));
}
function renderFiles() {
  const table = qs("#filesTable");
  if (!state.files.length) { table.className = "file-table empty-state"; table.textContent = "No files uploaded in this session."; return; }
  table.className = "file-table";
  table.innerHTML = `<div class="table-wrap"><table><thead><tr><th>FILE</th><th>TYPE</th><th>SIZE</th><th>WORKSPACE</th><th>STATUS</th></tr></thead><tbody>${state.files.map((file) => `<tr><td>${file.name}</td><td>${fileKind(file.name)}</td><td>${formatBytes(file.size)}</td><td>CONTROLLED</td><td class="ok">READY</td></tr>`).join("")}</tbody></table></div>`;
}

const dropzone = qs("#dropzone");
const fileInput = qs("#fileInput");
qs("#browseBtn").onclick = () => fileInput.click();
qs("#filesBrowse").onclick = () => { navigate("workspace"); setTimeout(() => fileInput.click(), 250); };
fileInput.onchange = (event) => addFiles(event.target.files);
["dragenter", "dragover"].forEach((eventName) => dropzone.addEventListener(eventName, (event) => { event.preventDefault(); dropzone.classList.add("drag"); }));
["dragleave", "drop"].forEach((eventName) => dropzone.addEventListener(eventName, (event) => { event.preventDefault(); dropzone.classList.remove("drag"); }));
dropzone.addEventListener("drop", (event) => addFiles(event.dataTransfer.files));

function renderWorkflow(active = -1, done = -1) {
  qs("#workflow").innerHTML = steps.map((step, index) => {
    const className = index <= done ? "done" : index === active ? "active" : "";
    const status = index <= done ? "DONE" : index === active ? "RUNNING" : "WAITING";
    return `<div class="step ${className}"><div class="step-icon">${index <= done ? "✓" : index + 1}</div><div><strong>${step}</strong><small>${["Policy and access validation", "Determining task type", "Reading uploaded formats", "Searching extracted content", "Answering from context", "Checking answer against evidence", "Review gate for sensitive action", "Creating requested deliverable", "Workflow finished"][index]}</small></div><span class="step-status">${status}</span></div>`;
  }).join("");
}
renderWorkflow();

function setResult(answer, evidence, errors = []) {
  qs("#resultBox").classList.remove("empty");
  qs("#resultBox").innerHTML = answer || "No answer was returned.";
  qs("#evidenceList").innerHTML = evidence.length ? evidence.map((item, index) => `<div class="evidence-item"><strong>Reference ${index + 1} · ${item.file}</strong><small>${item.detail}</small><p>${item.content || ""}</p></div>`).join("") : `<div class="empty-state">No matching evidence was found.</div>`;
  qs("#deliverables").innerHTML = `<div class="deliverable"><strong>verified-analysis.txt</strong><small>Generated from the connected backend</small><button class="secondary-btn" id="downloadGenerated">Download</button></div>`;
  qs("#downloadGenerated").onclick = downloadText;
  if (errors.length) toast(`${errors.length} file${errors.length > 1 ? "s" : ""} could not be read`);
}
function downloadText() {
  const blob = new Blob([qs("#resultBox").innerText], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "verified-analysis.txt"; link.click(); URL.revokeObjectURL(link.href);
}
qs("#downloadResult").onclick = downloadText;

async function callBackend(task) {
  const form = new FormData();
  form.append("task", task);
  state.files.forEach((file) => form.append("files", file, file.name));
  const response = await fetch(`${API_BASE}/api/agent/tasks`, { method: "POST", body: form });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Backend request failed");
  return data;
}
async function runAgent() {
  if (state.running) return;
  const task = qs("#taskInput").value.trim();
  if (!task) { toast("Enter a task before running the agent."); qs("#taskInput").focus(); return; }
  if (!state.files.length) { toast("Upload at least one document first."); return; }
  state.running = true; qs("#runTask").disabled = true; qs("#progressState").textContent = "RUNNING"; qs("#activeTasks").textContent = "1"; addAudit("Agent task submitted", "STARTED");
  const request = callBackend(task);
  try {
    for (let index = 0; index < 8; index += 1) { renderWorkflow(index, index - 1); await new Promise((resolve) => setTimeout(resolve, 180)); }
    const data = await request;
    renderWorkflow(8, 8);
    setResult(data.answer, data.evidence || [], data.errors || []);
    qs("#progressState").textContent = data.success ? "COMPLETED" : "FAILED";
    addAudit("Agent workflow completed", data.success ? "SUCCESS" : "FAILED");
    qs("#requestCount").textContent = String(Number(qs("#requestCount").textContent) + 1);
    toast(data.success ? "Workflow completed" : "Workflow returned an error");
  } catch (error) {
    renderWorkflow(-1, -1); qs("#progressState").textContent = "FAILED"; qs("#resultBox").classList.remove("empty"); qs("#resultBox").textContent = error.message; addAudit("Agent workflow failed", "FAILED"); toast(error.message);
  } finally { state.running = false; qs("#runTask").disabled = false; qs("#activeTasks").textContent = "0"; }
}
qs("#runTask").onclick = runAgent;
qs("#notifications").onclick = () => toast("No new security events.");
qsa(".ripple").forEach((button) => button.addEventListener("click", (event) => { const ripple = document.createElement("span"); ripple.className = "ripple-wave"; const rect = button.getBoundingClientRect(); const size = Math.max(rect.width, rect.height); ripple.style.width = ripple.style.height = `${size}px`; ripple.style.left = `${event.clientX - rect.left - size / 2}px`; ripple.style.top = `${event.clientY - rect.top - size / 2}px`; button.appendChild(ripple); setTimeout(() => ripple.remove(), 650); }));
document.addEventListener("keydown", (event) => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); navigate("workspace"); setTimeout(() => qs("#taskInput").focus(), 200); } });
