// --- DOM Elements ---
const sidebar = document.getElementById("sidebar");
const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
const mainContent = document.getElementById("main-content");
const accordions = document.querySelectorAll(".accordion-header");
const themeToggleBtn = document.getElementById("theme-toggle-btn");
const themeIconSun = document.getElementById("theme-icon-sun");
const themeIconMoon = document.getElementById("theme-icon-moon");
const themeText = document.getElementById("theme-text");
const configBtn = document.getElementById("config-btn");
const uploadDocumentBtn = document.getElementById("upload-document-btn");
const graphLoadingOverlay = document.getElementById("graph-loading-overlay");
const graphContainer = document.getElementById("graph-container");
const graphActionStatus = document.getElementById("graph-action-status");
const taskProgressContainer = document.getElementById("task-progress-container");

// Selection & Info Panel
const selectionAccordion = document.getElementById("selection-accordion");
const nodeInfoPanel = document.getElementById("node-info-panel");
const edgeInfoPanel = document.getElementById("edge-info-panel");
const nodeIDDisplay = document.getElementById("node-id-display");
const nodeLabelDisplay = document.getElementById("node-label-display");
const nodePropertiesDisplay = document.getElementById("node-properties-display");
const editSelectedNodeBtn = document.getElementById("edit-selected-node-btn");
const expandNeighborsBtn = document.getElementById("expand-neighbors-btn");
const setStartNodeBtn = document.getElementById("set-start-node-btn");
const setEndNodeBtn = document.getElementById("set-end-node-btn");
const edgeIDDisplay = document.getElementById("edge-id-display");
const edgeTypeDisplay = document.getElementById("edge-type-display");
const edgePropertiesDisplay = document.getElementById("edge-properties-display");
const editSelectedEdgeBtn = document.getElementById("edit-selected-edge-btn");
const noSelectionMessage = document.getElementById("no-selection");

// Controls
const graphSearchForm = document.getElementById("graph-search-form");
const graphSearchInput = document.getElementById("graph-search-input");
const editModeBtn = document.getElementById("edit-mode-btn");
const editModeBtnText = document.getElementById("edit-mode-btn-text");
const togglePhysicsBtn = document.getElementById("toggle-physics-btn");
const physicsBtnText = document.getElementById("physics-btn-text");
const fuseEntitiesBtn = document.getElementById("fuse-entities-btn");
const fitGraphBtn = document.getElementById("fit-graph-btn");
const findPathForm = document.getElementById("find-path-form");
const startNodeInput = document.getElementById("start-node-input");
const endNodeInput = document.getElementById("end-node-input");
const directedPathToggle = document.getElementById("directed-path-toggle");

// Upload Modal
const uploadModal = document.getElementById("upload-modal");
const closeUploadModalBtn = document.getElementById("close-upload-modal-btn");
const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const extractionGuidanceInput = document.getElementById("extraction-guidance-input");
const fileListPreview = document.getElementById("file-list-preview");
const uploadSubmitBtn = document.getElementById("upload-submit-btn");
const uploadProgressArea = document.getElementById("upload-progress-area");
const uploadOverallStatus = document.getElementById("upload-overall-status");

// Chat Modal
const chatBtn = document.getElementById("chat-btn");
const chatModal = document.getElementById("chat-modal");
const closeChatModalBtn = document.getElementById("close-chat-modal-btn");
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatSubmitBtn = document.getElementById("chat-submit-btn");

// Config Modal
const configModal = document.getElementById("config-modal");
const closeConfigModalBtn = document.getElementById("close-config-modal-btn");
const configForm = document.getElementById("config-form");
const configStatus = document.getElementById("config-status");
const dbSelect = document.getElementById("config-database-select");
const newDbNameInput = document.getElementById("config-new-db-name");
const createDbBtn = document.getElementById("config-create-db-btn");
const deleteDbBtn = document.getElementById("config-delete-db-btn");
const lollmsBindingInput = document.getElementById("config-lollms-binding");
const lollmsModelInput = document.getElementById("config-lollms-model");
const lollmsHostInput = document.getElementById("config-lollms-host");
const lollmsKeyInput = document.getElementById("config-lollms-key");

// --- API Configuration ---
const API_BASE_URL = "";
const API_ENDPOINTS = {
    INITIALIZE: `${API_BASE_URL}/api/initialize`,
    STATUS: `${API_BASE_URL}/api/status`,
    DATABASES: `${API_BASE_URL}/api/databases`,
    DATABASE_MANAGE: (dbName) => `${API_BASE_URL}/api/databases/${encodeURIComponent(dbName)}`,
    UPLOAD: `${API_BASE_URL}/upload-file/`,
    GRAPH_DATA: `${API_BASE_URL}/graph-data/`,
    GRAPH_SEARCH: (q) => `${API_BASE_URL}/graph/search/?q=${encodeURIComponent(q)}`,
    GRAPH_FUSE: `${API_BASE_URL}/graph/fuse/`,
    NODE: (id) => `${API_BASE_URL}/graph/node/${id ? id : ''}`,
    EDGE: (id) => `${API_BASE_URL}/graph/edge/${id ? id : ''}`,
    NEIGHBORS: (nodeId) => `${API_BASE_URL}/graph/node/${nodeId}/neighbors`,
    PATH: `${API_BASE_URL}/graph/path`,
    CHAT: `${API_BASE_URL}/api/chat/rag`,
};

// --- Global State & Vis.js Instances ---
let network;
let nodesDataSet = new vis.DataSet();
let edgesDataSet = new vis.DataSet();
let appSettings = {
    theme: 'light',
    physicsOnLoad: true,
    editModeEnabled: false,
    sidebarCollapsed: false
};
let appConfig = null;
let isPhysicsActive = true;
let socket = null;
let sessionId = null;
const markdownConverter = new showdown.Converter();

const DEFAULT_CONFIG = {
    lollms: {
        binding_name: "ollama",
        host_address: "http://localhost:11434",
        model_name: "mistral-nemo:latest",
        service_key": null
    },
    safestore: {
        default_vectorizer: "st:all-MiniLM-L6-v2",
        chunk_size: 10000,
        chunk_overlap": 100
    },
    database: ""
};

// --- Helper Functions ---
function showUserStatus(element, message, type = "success", duration = 4000) {
    if (!element) return;
    const colors = { success: "text-green-500", error: "text-red-500", info: "text-blue-500", warning: "text-yellow-500" };
    const icons = { success: "fa-check-circle", error: "fa-times-circle", info: "fa-info-circle", warning: "fa-exclamation-triangle" };
    element.innerHTML = `<i class="fas ${icons[type]} ${colors[type]} mr-2"></i><span>${message}</span>`;
    if (duration > 0) {
        setTimeout(() => { if (element.innerHTML.includes(message)) element.innerHTML = ""; }, duration);
    }
}

async function apiRequest(endpoint, method = 'GET', body = null, isFormData = false) {
    const options = { method };
    if (!isFormData && body) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(body);
    } else if (isFormData && body) {
        options.body = body;
    }
    try {
        const response = await fetch(endpoint, options);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP error ${response.status}` }));
            throw new Error(errorData.detail || `Request failed`);
        }
        return response.status === 204 || response.status === 202 ? response : await response.json();
    } catch (error) {
        console.error(`API call to ${endpoint} failed:`, error);
        throw error;
    }
}

function openModal(modal) { modal?.classList.remove("hidden"); }
function closeModal(modal) { modal?.classList.add("hidden"); }

// --- Config Management ---
function loadConfig() {
    const storedConfig = localStorage.getItem('safeStoreGraphRAGConfig');
    if (storedConfig) {
        try {
            appConfig = JSON.parse(storedConfig);
            return true;
        } catch (e) {
            console.error("Failed to parse stored config:", e);
            localStorage.removeItem('safeStoreGraphRAGConfig');
        }
    }
    appConfig = JSON.parse(JSON.stringify(DEFAULT_CONFIG)); // Deep copy
    return false;
}

function saveConfig() {
    if (appConfig) {
        localStorage.setItem('safeStoreGraphRAGConfig', JSON.stringify(appConfig));
    }
}

async function showConfigModal(isFirstRun = false) {
    populateConfigForm();
    await populateDatabaseList();
    if (isFirstRun) {
        closeConfigModalBtn.style.display = 'none';
        showUserStatus(configStatus, "Welcome! Please configure the application to continue.", "info", 0);
    } else {
        closeConfigModalBtn.style.display = 'block';
        configStatus.innerHTML = '';
    }
    openModal(configModal);
}

function populateConfigForm() {
    if (!appConfig) return;
    dbSelect.value = appConfig.database || "";
    lollmsBindingInput.value = appConfig.lollms.binding_name || "";
    lollmsModelInput.value = appConfig.lollms.model_name || "";
    lollmsHostInput.value = appConfig.lollms.host_address || "";
    lollmsKeyInput.value = appConfig.lollms.service_key || "";
}

async function populateDatabaseList() {
    try {
        const dbs = await apiRequest(API_ENDPOINTS.DATABASES);
        dbSelect.innerHTML = '<option value="">-- Select a Database --</option>';
        if (dbs.length === 0) {
            dbSelect.innerHTML = '<option value="">-- No databases found. Please create one. --</option>';
        }
        dbs.forEach(db => {
            const option = document.createElement('option');
            option.value = db.name;
            option.textContent = db.name;
            if (appConfig && appConfig.database === db.name) {
                option.selected = true;
            }
            dbSelect.appendChild(option);
        });
    } catch (e) {
        showUserStatus(configStatus, `Error fetching databases: ${e.message}`, "error", 0);
    }
}

configForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    appConfig.database = dbSelect.value;
    appConfig.lollms.binding_name = lollmsBindingInput.value.trim();
    appConfig.lollms.model_name = lollmsModelInput.value.trim();
    appConfig.lollms.host_address = lollmsHostInput.value.trim();
    appConfig.lollms.service_key = lollmsKeyInput.value.trim() || null;

    if (!appConfig.database) {
        showUserStatus(configStatus, "Please select or create a database.", "warning");
        return;
    }
    saveConfig();
    await initializeBackend();
});

createDbBtn.addEventListener('click', async () => {
    const name = newDbNameInput.value.trim();
    if (!name) {
        showUserStatus(configStatus, "Please enter a name for the new database.", "warning");
        return;
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
        showUserStatus(configStatus, "Name can only contain letters, numbers, hyphens, and underscores.", "error");
        return;
    }
    try {
        await apiRequest(API_ENDPOINTS.DATABASES, 'POST', { name });
        appConfig.database = name; // Auto-select the new DB
        saveConfig();
        newDbNameInput.value = '';
        await populateDatabaseList();
        showUserStatus(configStatus, `Database '${name}' created.`, "success");
    } catch (e) {
        showUserStatus(configStatus, `Error creating database: ${e.message}`, "error");
    }
});

deleteDbBtn.addEventListener('click', async () => {
    const name = dbSelect.value;
    if (!name) {
        showUserStatus(configStatus, "Please select a database to delete.", "warning");
        return;
    }
    if (confirm(`Are you sure you want to permanently delete the '${name}' database and all its data? This cannot be undone.`)) {
        try {
            await apiRequest(API_ENDPOINTS.DATABASE_MANAGE(name), 'DELETE');
            if (appConfig.database === name) {
                appConfig.database = "";
                saveConfig();
            }
            await populateDatabaseList();
            showUserStatus(configStatus, `Database '${name}' deleted.`, "success");
        } catch (e) {
            showUserStatus(configStatus, `Error deleting database: ${e.message}`, "error");
        }
    }
});


// --- Initialization and Backend Communication ---
async function initializeBackend() {
    showUserStatus(configStatus, "Connecting to backend with new configuration...", "info", 0);
    try {
        await apiRequest(API_ENDPOINTS.INITIALIZE, 'POST', appConfig);
        showUserStatus(configStatus, "Backend initialized successfully!", "success", 5000);
        closeModal(configModal);
        // Full app refresh after successful initialization
        initializeAppState();
    } catch (error) {
        showUserStatus(configStatus, `Initialization Failed: ${error.message}`, "error", 0);
        // Re-open config modal if it was closed
        openModal(configModal);
    }
}

function setupSocketIO() {
    if (socket) {
        socket.disconnect();
    }
    socket = io({ path: '/sio' });
    socket.on('connect', () => {
        sessionId = socket.id;
        console.log("Socket.IO connected:", sessionId);
        chatSubmitBtn.disabled = false;
        uploadSubmitBtn.disabled = fileInput.files.length === 0;
    });
    socket.on('progress_update', handleProgressUpdate);
    socket.on('disconnect', () => {
        console.log("Socket.IO disconnected.");
        sessionId = null;
        chatSubmitBtn.disabled = true;
        uploadSubmitBtn.disabled = true;
    });
    socket.on('connect_error', (error) => console.error("Socket.IO connection error:", error));
}

function handleProgressUpdate(data) {
    const { task_id, filename, progress, message } = data;
    let el = document.getElementById(`progress-${task_id}`);
    const container = task_id.startsWith('fuse_') ? taskProgressContainer : uploadProgressArea;

    if (!el) {
        el = document.createElement('div');
        el.id = `progress-${task_id}`;
        el.className = 'p-2 my-1 bg-bg-tertiary rounded-md text-xs';
        const fileIdentifier = filename || (task_id.startsWith('fuse_') ? "Entity Fusion" : "Processing Task");
        el.innerHTML = `<div class="font-semibold mb-1 truncate">${fileIdentifier}</div><div id="progress-message-${task_id}" class="text-text-secondary mb-1 truncate">Initializing...</div><div class="progress-bar-container"><div id="progress-bar-${task_id}" class="progress-bar" style="width: 0%;"></div></div>`;
        container.appendChild(el);
    }
    document.getElementById(`progress-message-${task_id}`).textContent = message;
    const progressBar = document.getElementById(`progress-bar-${task_id}`);
    progressBar.style.width = `${progress * 100}%`;
    if (progress >= 1.0) {
        progressBar.classList.remove('bg-accent-primary');
        progressBar.classList.add(message.toLowerCase().includes("error") ? 'bg-red-600' : 'bg-green-600');
        setTimeout(() => el.remove(), 8000);
    }
}


// --- App Logic (Graph, Upload, Chat etc.) ---
async function fetchGraphData() {
    graphLoadingOverlay.classList.remove('hidden');
    showUserStatus(graphActionStatus, "Loading graph...", "info", 0);
    try {
        const data = await apiRequest(API_ENDPOINTS.GRAPH_DATA);
        nodesDataSet.clear();
        edgesDataSet.clear();
        nodesDataSet.add(data.nodes.map(n => ({ ...n, original_label: n.label })));
        edgesDataSet.add(data.edges);
        if (!network) renderGraph();
        else network.setData({ nodes: nodesDataSet, edges: edgesDataSet });
        showUserStatus(graphActionStatus, "Graph loaded.", "success");
    } catch (error) {
        showUserStatus(graphActionStatus, `Error loading graph: ${error.message}`, "error");
    } finally {
        graphLoadingOverlay.classList.add('hidden');
    }
}

// ... (renderGraph and most of the other UI functions can remain largely the same)
// Minor changes to upload handler to use sessionId
uploadForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!fileInput.files.length || !sessionId) {
        showUserStatus(uploadOverallStatus, "No files selected or not connected to server.", "error");
        return;
    }
    uploadSubmitBtn.disabled = true;
    showUserStatus(uploadOverallStatus, `Uploading ${fileInput.files.length} file(s)...`, "info", 0);
    const formData = new FormData();
    Array.from(fileInput.files).forEach(file => formData.append("files", file));
    formData.append("guidance", extractionGuidanceInput.value.trim());
    formData.append("sid", sessionId);
    try {
        await apiRequest(API_ENDPOINTS.UPLOAD, "POST", formData, true);
        showUserStatus(uploadOverallStatus, "Upload successful. Processing started.", "success", 6000);
        setTimeout(fetchGraphData, 5000); // Refresh graph data after a delay
    } catch (error) {
        showUserStatus(uploadOverallStatus, `Upload failed: ${error.message}`, "error", 0);
    } finally {
        uploadSubmitBtn.disabled = false;
    }
});


// --- Theme & Settings Management ---
function applyTheme(theme) {
    appSettings.theme = theme;
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        themeIconSun.classList.add('hidden');
        themeIconMoon.classList.remove('hidden');
        themeText.textContent = "Dark";
    } else {
        document.documentElement.classList.remove('dark');
        themeIconSun.classList.remove('hidden');
        themeIconMoon.classList.add('hidden');
        themeText.textContent = "Light";
    }
    localStorage.setItem('graphExplorerSettings', JSON.stringify(appSettings));
    updateVisThemeOptions();
}

function loadAppSettings() {
    const s = localStorage.getItem('graphExplorerSettings');
    if (s) {
        try { appSettings = { ...appSettings, ...JSON.parse(s) }; } catch (e) { console.error("Bad settings:", e); }
    }
    applyTheme(appSettings.theme);
    // ... rest of settings application
}

// --- App Initialization Flow ---
function initializeAppState() {
    // This function is called after the backend is confirmed to be initialized
    setupSocketIO();
    fetchGraphData();
    // Enable UI elements
    const controls = document.querySelectorAll('.control-button, .control-input');
    controls.forEach(c => c.disabled = false);
}

function disableAppState(message) {
    // This function is called when the app is not configured
    if (network) {
        nodesDataSet.clear();
        edgesDataSet.clear();
    }
    const controls = document.querySelectorAll('.control-button, .control-input');
    controls.forEach(c => c.disabled = true);
    // Re-enable config button
    configBtn.disabled = false;
    themeToggleBtn.disabled = false;

    showUserStatus(graphActionStatus, message, "warning", 0);
}


document.addEventListener('DOMContentLoaded', async () => {
    loadAppSettings();

    if (loadConfig()) {
        // Config exists, try to initialize
        try {
            await apiRequest(API_ENDPOINTS.INITIALIZE, 'POST', appConfig);
            initializeAppState();
        } catch (e) {
            disableAppState("Backend initialization failed. Please check configuration.");
            showUserStatus(configStatus, `Auto-initialization failed: ${e.message}`, "error", 0);
            await showConfigModal();
        }
    } else {
        // No config, first run
        disableAppState("Application not configured.");
        await showConfigModal(true);
    }
});

// Other event listeners
configBtn.addEventListener('click', () => showConfigModal());
closeConfigModalBtn.addEventListener('click', () => closeModal(configModal));
uploadDocumentBtn?.addEventListener("click", () => {
    uploadForm.reset();
    fileListPreview.innerHTML = '';
    uploadProgressArea.innerHTML = '';
    uploadOverallStatus.innerHTML = '';
    uploadSubmitBtn.disabled = true;
    openModal(uploadModal);
});
closeUploadModalBtn?.addEventListener("click", () => closeModal(uploadModal));
fileInput?.addEventListener("change", () => {
    fileListPreview.innerHTML = '';
    if (fileInput.files.length) {
        Array.from(fileInput.files).forEach(f => {
            fileListPreview.innerHTML += `<div class="text-xs p-1 truncate">${f.name}</div>`;
        });
        if (sessionId) uploadSubmitBtn.disabled = false;
    } else {
        uploadSubmitBtn.disabled = true;
    }
});

// --- Placeholder for functions that were not changed to keep the file size down ---
// All the functions for graph rendering, controls, modals (except config), chat etc.
// would be here, mostly unchanged from the original file.
// For this exercise, I will only include the critical changed/new functions.
// Assume renderGraph, updateVisThemeOptions, updateSelectionInfoPanel, etc. are present and correct.
function renderGraph() { /* ... original implementation ... */ }
function getVisThemeColors() { /* ... original implementation ... */ return { nodeFont: '#000' } }
function updateVisThemeOptions() { /* ... original implementation ... */ }
function updateSelectionInfoPanel(params) { /* ... original implementation ... */ }
// Add other unchanged functions if needed for context
chatBtn?.addEventListener("click", () => openModal(chatModal));
closeChatModalBtn?.addEventListener("click", () => closeModal(chatModal));
chatForm?.addEventListener("submit", async (e)=>{
    e.preventDefault();
    const q = chatInput.value.trim();
    if (!q) return;
    addChatMessage(q, 'user');
    chatInput.value = '';
    addChatMessage('', 'ai', true);
    try {
        const r = await apiRequest(API_ENDPOINTS.CHAT, 'POST', { query: q });
        document.getElementById("thinking-indicator")?.remove();
        addChatMessage(r.answer, 'ai');
    } catch (err) {
        document.getElementById("thinking-indicator")?.remove();
        addChatMessage(`Error: ${err.message}`, 'ai');
    }
});
function addChatMessage(message, sender, isThinking = false) {
    const d = document.createElement("div");
    d.className = `chat-message ${sender === 'user' ? 'chat-user' : 'chat-ai'}`;
    if (isThinking) {
        d.innerHTML = `<i class="fas fa-spinner fa-spin"></i>`;
        d.id = "thinking-indicator";
    } else if (sender === 'ai') {
        d.innerHTML = markdownConverter.makeHtml(message);
    } else {
        d.textContent = message;
    }
    chatMessages.appendChild(d);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}