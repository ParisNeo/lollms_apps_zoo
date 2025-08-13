// folder_extractor/static/main.js
// [UPDATE]

document.addEventListener('DOMContentLoaded', () => {
    // --- Global State & Element Selectors ---
    const S = id => document.getElementById(id);
    const
        appTitle = S('app-title'),
        statusMessage = S('status-message'),
        themeToggle = S('theme-toggle'),
        settingsBtn = S('settings-btn'),
        logsBtn = S('logs-btn'), // New selector for logs button
        // Views
        projectListView = S('project-list-view'),
        extractorView = S('extractor-view'),
        // Project List View
        projectCardsContainer = S('project-cards-container'),
        addProjectBtn = S('add-project-btn'),
        importProjectsBtn = S('import-projects-btn'),
        exportProjectsBtn = S('export-projects-btn'),
        importFileInput = S('import-file-input'),
        // Extractor View
        backToProjectsBtn = S('back-to-projects-btn'),
        folderPathInput = S('folder-path-input'),
        loadTreeBtn = S('load-tree-btn'),
        presetList = S('preset-list'),
        customFoldersInput = S('custom-folders-input'),
        customExtensionsInput = S('custom-extensions-input'),
        customPatternsInput = S('custom-patterns-input'),
        customInclusionsInput = S('custom-inclusions-input'),
        maxFileSizeInput = S('max-file-size-input'),
        docList = S('doc-list'),
        addDocsInput = S('add-docs-input'),
        addDocsBtn = S('add-docs-btn'),
        removeDocsBtn = S('remove-docs-btn'),
        clearDocsBtn = S('clear-docs-btn'),
        // Tab 2
        fileTreeContainer = S('file-tree-container'),
        refreshTreeBtn = S('refresh-tree-btn'),
        aiSelectBtn = S('ai-select-btn'),
        checkAllTextBtn = S('check-all-text-btn'),
        uncheckAllBtn = S('uncheck-all-btn'),
        templateSelect = S('template-select'),
        loadTemplateBtn = S('load-template-btn'),
        savePromptBtn = S('save-prompt-btn'),
        customPromptTextarea = S('custom-prompt-textarea'),
        generateBtn = S('generate-btn'),
        // Tab 3
        rawOutputTextarea = S('raw-output-textarea'),
        renderedOutputDiv = S('rendered-output-div'),
        copyRawBtn = S('copy-raw-btn'),
        // Tab 4 (Discussion)
        startDiscussionBtn = S('start-discussion-btn'),
        startDiscussionPlaceholder = S('start-discussion-placeholder'),
        chatMessagesContainer = S('chat-messages-container'),
        chatForm = S('chat-form'),
        chatInput = S('chat-input'),
        chatSendBtn = S('chat-send-btn'),
        tokenProgressContainer = S('token-progress-container'),
        tokenProgressBar = S('token-progress-bar'),
        tokenCountDisplay = S('token-count-display'),
        // Modals
        refreshChoiceModal = S('refresh-choice-modal'),
        refreshPreserveBtn = S('refresh-preserve-btn'),
        refreshRepopulateBtn = S('refresh-repopulate-btn'),
        refreshCancelBtn = S('refresh-cancel-btn'),
        settingsModal = S('settings-modal'),
        modalLlmSettingsForm = S('modal-llm-settings-form'),
        modalLlmUrlInput = S('modal-llm-url-input'),
        modalLlmApiKeyInput = S('modal-llm-api-key-input'),
        modalLlmModelSelect = S('modal-llm-model-select'),
        refreshModelsBtn = S('refresh-models-btn'),
        modalSaveLlmSettingsBtn = S('modal-save-llm-settings-btn'),
        modalCloseSettingsBtn = S('modal-close-settings-btn'),
        setDefaultLollmsBtn = S('set-default-lollms-btn'),
        apiKeyToggleBtn = S('api-key-toggle-btn'),
        importPromptsBtn = S('import-prompts-btn'),
        exportPromptsBtn = S('export-prompts-btn'),
        importPromptsInput = S('import-prompts-input'),
        // New Logs Modal Selectors
        logsModal = S('logs-modal'),
        logsModalContent = S('logs-modal-content'),
        logsModalClearBtn = S('logs-modal-clear-btn'),
        logsModalCloseBtn = S('logs-modal-close-btn');


    const clientState = {
        currentView: 'projects',
        activeProjectId: null,
        projects: [],
        promptTemplates: [],
        llmSettings: { url: '', api_key: '', model_name: '' },
        filterSettings: {}, 
        checkedTreePathsMap: new Map(), // Stores path -> 'full' or 'signatures'
        markedForRemovalPaths: new Set(), // Stores paths to be excluded completely
        customPrompt: '',
        loadedDocPaths: [],
        chatHistory: [],
        isAIGenerating: false,
        modelContextSize: 0,
        currentTokens: 0,
        currentTheme: 'light',
        appVersion: '3.5.0',
        logMessages: [] // New state for log messages
    };
    
    const icons = {
        eye: `<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>`,
        eyeSlash: `<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>`
    };

    // --- Utility Functions ---
    // Modified showStatus to also push to logs modal
    function showStatus(message, type = 'info', duration = 3000) {
        if (!statusMessage) return;
        statusMessage.textContent = message;
        statusMessage.className = 'text-sm px-3 py-1.5 rounded-lg min-w-[220px] text-center truncate transition-all';
        const typeClasses = {
            error: 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300',
            warning: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300',
            success: 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300',
            info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
        };
        statusMessage.classList.add(...(typeClasses[type] || typeClasses.info).split(' '));
        setTimeout(() => { if (statusMessage.textContent === message) statusMessage.textContent = 'Ready.'; }, duration);

        addLogEntry(message, type); // Also log to modal
    }

    async function handleApiResponse(responsePromise) {
        try {
            const response = await responsePromise;
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: `HTTP Error ${response.status}: ${response.statusText}` }));
                throw new Error(errorData.detail);
            }
            return response.status === 204 ? null : response.json();
        } catch (error) {
            addLogEntry(`API Request Error: ${error.message}`, 'error'); // Log API errors
            throw new Error(error.message || "A network error occurred.");
        }
    }
    
    // --- View Management ---
    function switchView(viewName, projectId = null) {
        clientState.currentView = viewName;
        if (projectListView) projectListView.classList.toggle('active', viewName === 'projects');
        if (extractorView) extractorView.classList.toggle('active', viewName === 'extractor');
        
        if (viewName === 'extractor') {
            addLogEntry(`Switched to Extractor view for project: ${projectId}`, 'info');
            loadProjectIntoExtractor(projectId);
        } else {
            appTitle.textContent = "Folder Extractor";
            clientState.activeProjectId = null;
            addLogEntry('Switched to Project Dashboard view.', 'info');
            fetchProjects();
        }
    }

    // --- Project Management ---
    async function fetchProjects() {
        try {
            clientState.projects = await handleApiResponse(fetch('/api/projects'));
            renderProjectCards();
            addLogEntry('Projects loaded from server.', 'info');
        } catch (error) {
            showStatus(`Error fetching projects: ${error.message}`, 'error');
            addLogEntry(`Error fetching projects: ${error.message}`, 'error');
        }
    }

    function renderProjectCards() {
        if (!projectCardsContainer) return;
        projectCardsContainer.innerHTML = '';
        if (clientState.projects.length === 0) {
            projectCardsContainer.innerHTML = `<div class="col-span-full text-center p-8">
                <h3 class="text-lg font-semibold text-gray-700 dark:text-gray-300">No projects found.</h3>
                <p class="text-gray-500 dark:text-gray-400 mt-2">Click "Add New Project" to get started.</p>
            </div>`;
            addLogEntry('No projects found, displaying empty state.', 'info');
            return;
        }
        clientState.projects.forEach(p => {
            const card = document.createElement('div');
            card.className = 'project-card bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 flex flex-col border dark:border-gray-700';
            card.dataset.id = p.id;
            
            card.innerHTML = `
                <div class="flex items-start justify-between">
                     <div class="flex-grow min-w-0">
                        <h3 class="font-bold text-lg text-gray-800 dark:text-gray-100 truncate cursor-pointer" title="Open project">${p.name}</h3>
                        <p class="text-xs text-gray-500 dark:text-gray-400 break-all" title="${p.path}">${p.path}</p>
                     </div>
                     <input type="checkbox" class="project-export-checkbox form-checkbox h-4 w-4 text-blue-600 border-gray-300 rounded ml-2 flex-shrink-0" title="Select for export">
                </div>
                <div class="flex-grow"></div>
                <div class="flex justify-between items-center mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <button class="star-btn p-2 text-gray-400 hover:text-yellow-400 ${p.starred ? 'starred' : ''}" data-action="star" title="Star project">
                        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>
                    </button>
                    <div class="space-x-1">
                        <button class="card-action-btn" data-action="clone" title="Clone project"><svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.5a1.125 1.125 0 011.125-1.125h7.5a.75.75 0 010 1.5h-7.5a.375.375 0 00-.375.375v11.25c0 .207.168.375.375.375h9.75a.375.375 0 00.375-.375V17.25a.75.75 0 011.5 0z" /><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 8.25v-1.5a2.25 2.25 0 00-2.25-2.25H6.375a2.25 2.25 0 00-2.25 2.25v8.25a2.25 2.25 0 002.25 2.25h2.25m4.5-1.5H18a2.25 2.25 0 002.25-2.25V6a2.25 2.25 0 00-2.25-2.25H18m-4.5 3.75h.008v.008h-.008v-.008z" /></svg></button>
                        <button class="card-action-btn" data-action="edit" title="Edit project"><svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" /></svg></button>
                        <button class="card-action-btn" data-action="delete" title="Delete project"><svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" /></svg></button>
                    </div>
                </div>`;

            card.addEventListener('click', (e) => {
                const action = e.target.closest('button')?.dataset.action;
                const isCheckbox = e.target.matches('.project-export-checkbox');
                
                if (action) {
                    e.stopPropagation();
                    handleProjectAction(action, p.id);
                } else if (!isCheckbox) {
                    switchView('extractor', p.id);
                }
            });
            projectCardsContainer.appendChild(card);
        });
    }

    async function handleProjectAction(action, projectId) {
        const project = clientState.projects.find(p => p.id === projectId);
        if (!project) return;

        switch (action) {
            case 'star':
                try {
                    await handleApiResponse(fetch(`/api/projects/${projectId}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ starred: !project.starred })}));
                    addLogEntry(`Project "${project.name}" starred status toggled.`, 'info');
                    await fetchProjects();
                } catch (error) { showStatus(`Error starring project: ${error.message}`, 'error'); }
                break;
            case 'clone':
                 try {
                    const clonedProject = await handleApiResponse(fetch(`/api/projects/${projectId}/clone`, { method: 'POST' }));
                    const originalState = localStorage.getItem(`projectState_${projectId}`);
                    if (originalState) {
                        localStorage.setItem(`projectState_${clonedProject.id}`, originalState);
                    }
                    showStatus(`Cloned "${project.name}". Settings and selections copied.`, 'success');
                    addLogEntry(`Cloned project "${project.name}" to "${clonedProject.name}".`, 'success');
                    await fetchProjects();
                } catch (error) { showStatus(`Error cloning project: ${error.message}`, 'error'); }
                break;
            case 'edit':
                const newName = prompt("Enter new project name:", project.name);
                if (newName && newName.trim() !== project.name) {
                    try {
                        await handleApiResponse(fetch(`/api/projects/${projectId}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name: newName.trim() })}));
                        showStatus(`Project "${project.name}" renamed to "${newName.trim()}".`, 'success');
                        addLogEntry(`Project "${project.name}" renamed to "${newName.trim()}".`, 'success');
                        await fetchProjects();
                    } catch (error) { showStatus(`Error updating project: ${error.message}`, 'error'); }
                } else {
                    addLogEntry('Project rename cancelled or name not changed.', 'info');
                }
                break;
            case 'delete':
                if (confirm(`Are you sure you want to delete project "${project.name}"?`)) {
                    try {
                        await handleApiResponse(fetch(`/api/projects/${projectId}`, { method: 'DELETE' }));
                        localStorage.removeItem(`projectState_${projectId}`);
                        showStatus(`Project "${project.name}" deleted.`, 'success');
                        addLogEntry(`Project "${project.name}" deleted.`, 'success');
                        await fetchProjects();
                    } catch (error) { showStatus(`Error deleting project: ${error.message}`, 'error'); }
                } else {
                    addLogEntry('Project deletion cancelled.', 'info');
                }
                break;
        }
    }
    
    // --- Extractor Logic ---
    function updateDocListUI() {
        if (!docList) return;
        docList.innerHTML = '';
        if (clientState.loadedDocPaths.length === 0) {
            const li = document.createElement('li');
            li.className = 'text-gray-500 dark:text-gray-400 text-center p-2';
            li.textContent = 'No documents added.';
            docList.appendChild(li);
        } else {
            clientState.loadedDocPaths.forEach(path => {
                const li = document.createElement('li');
                li.className = 'flex items-center justify-between p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded';
                li.dataset.path = path;
                
                const label = document.createElement('label');
                label.className = 'flex items-center text-xs flex-grow cursor-pointer';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'doc-checkbox form-checkbox h-3.5 w-3.5 text-blue-600 border-gray-300 rounded mr-2';
                label.appendChild(checkbox);

                const span = document.createElement('span');
                span.textContent = path;
                span.title = path;
                span.className = 'truncate';
                label.appendChild(span);

                li.appendChild(label);
                docList.appendChild(li);
            });
        }
    }
    
    function loadProjectIntoExtractor(projectId) {
        const project = clientState.projects.find(p => p.id === projectId);
        if (!project) {
            showStatus('Project not found.', 'error');
            addLogEntry('Attempted to load non-existent project.', 'error');
            switchView('projects');
            return;
        }
        
        clientState.activeProjectId = projectId;
        appTitle.textContent = project.name;
        
        const savedState = JSON.parse(localStorage.getItem(`projectState_${projectId}`) || '{}');

        clientState.filterSettings = savedState.filterSettings || { selected_presets: [], custom_folders: '', custom_extensions: '', custom_patterns: '', custom_inclusions: '', max_file_size_mb: 1.0 };
        // Ensure checkedTreePathsMap is initialized as a Map
        clientState.checkedTreePathsMap = new Map(Object.entries(savedState.checkedTreePathsMap || {}));
        clientState.markedForRemovalPaths = new Set(savedState.markedForRemovalPaths || []);
        clientState.customPrompt = savedState.customPrompt || '';
        clientState.loadedDocPaths = savedState.loadedDocPaths || [];
        clientState.chatHistory = savedState.chatHistory || [];
        clientState.modelContextSize = savedState.modelContextSize || 0;
        clientState.currentTokens = savedState.currentTokens || 0;

        folderPathInput.value = project.path;
        maxFileSizeInput.value = clientState.filterSettings.max_file_size_mb;
        customFoldersInput.value = clientState.filterSettings.custom_folders;
        customExtensionsInput.value = clientState.filterSettings.custom_extensions;
        customPatternsInput.value = clientState.filterSettings.custom_patterns;
        customInclusionsInput.value = clientState.filterSettings.custom_inclusions;
        customPromptTextarea.value = clientState.customPrompt;
        
        document.querySelectorAll('.preset-checkbox').forEach(cb => {
            cb.checked = clientState.filterSettings.selected_presets.includes(cb.value);
        });

        updateDocListUI();
        renderChatHistory();
        fileTreeContainer.innerHTML = '<p class="text-gray-500 dark:text-gray-400 p-4 text-center">Click "Load Project Tree" to begin.</p>';
        rawOutputTextarea.value = '';
        renderedOutputDiv.innerHTML = 'A rendered preview will appear here.';
        updateExtractorUIStates();
        updateTokenCountAndProgressBar();
        addLogEntry(`Loaded project "${project.name}" into extractor.`, 'info');
    }
    
    function saveProjectState() {
        if (!clientState.activeProjectId) return;
        const stateToSave = {
            filterSettings: clientState.filterSettings,
            checkedTreePathsMap: Object.fromEntries(clientState.checkedTreePathsMap), // Convert Map to object for JSON
            markedForRemovalPaths: Array.from(clientState.markedForRemovalPaths),
            customPrompt: customPromptTextarea.value,
            loadedDocPaths: clientState.loadedDocPaths,
            chatHistory: clientState.chatHistory,
            modelContextSize: clientState.modelContextSize,
            currentTokens: clientState.currentTokens
        };
        localStorage.setItem(`projectState_${clientState.activeProjectId}`, JSON.stringify(stateToSave));
        addLogEntry('Project state saved to local storage.', 'info');
    }
    
    function updateExtractorClientStateFromUI() {
        if (!clientState.activeProjectId) return;
        clientState.filterSettings = {
            selected_presets: Array.from(document.querySelectorAll('.preset-checkbox:checked')).map(cb => cb.value),
            custom_folders: customFoldersInput.value.trim(),
            custom_extensions: customExtensionsInput.value.trim(),
            custom_patterns: customPatternsInput.value.trim(),
            custom_inclusions: customInclusionsInput.value.trim(),
            max_file_size_mb: parseFloat(maxFileSizeInput.value) || 1.0
        };
        clientState.customPrompt = customPromptTextarea.value;
        saveProjectState();
    }

    // --- LLM & Template Settings ---
    async function fetchLlmSettings() {
        try {
            clientState.llmSettings = await handleApiResponse(fetch('/api/settings/llm'));
            if(modalLlmUrlInput) modalLlmUrlInput.value = clientState.llmSettings.url;
            if(modalLlmApiKeyInput) modalLlmApiKeyInput.value = clientState.llmSettings.api_key;
            if(modalLlmModelSelect) modalLlmModelSelect.value = clientState.llmSettings.model_name || '';
            addLogEntry('LLM settings loaded.', 'info');
        } catch(error) {
            showStatus('Could not load LLM settings.', 'warning');
            addLogEntry(`Error loading LLM settings: ${error.message}`, 'error');
        }
    }

    async function fetchLlmModels() {
        if (!modalLlmModelSelect) return;
        const currentUrl = modalLlmUrlInput.value.trim();
        if (!currentUrl) {
            showStatus("Please enter an LLM URL first.", "warning");
            addLogEntry("Cannot fetch models: LLM URL is empty.", 'warning');
            return;
        }
        showStatus('Fetching models...', 'info');
        modalLlmModelSelect.disabled = true;
        modalLlmModelSelect.innerHTML = '<option>Fetching...</option>';
        try {
            // Temporarily save settings to use the URL in the modal
            // The server-side proxy_lollms_request will handle appending /v1/
            await handleApiResponse(fetch('/api/settings/llm', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({ url: currentUrl, api_key: modalLlmApiKeyInput.value.trim(), model_name: clientState.llmSettings.model_name })
            }));
            addLogEntry(`Attempting to fetch models from: ${currentUrl}`, 'info');

            const models = await handleApiResponse(fetch('/api/llm_models'));
            modalLlmModelSelect.innerHTML = '<option value="">-- Select a model --</option>';
            if (models.length > 0) {
                models.forEach(modelId => {
                    const option = document.createElement('option');
                    option.value = modelId;
                    option.textContent = modelId;
                    modalLlmModelSelect.appendChild(option);
                });
                modalLlmModelSelect.value = clientState.llmSettings.model_name || '';
                showStatus('Models loaded successfully.', 'success');
                addLogEntry(`Successfully loaded ${models.length} models.`, 'success');
            } else {
                modalLlmModelSelect.innerHTML = '<option>No models found</option>';
                showStatus('No models found at the specified URL.', 'warning');
                addLogEntry('No models found at the specified URL.', 'warning');
            }
        } catch (error) {
            modalLlmModelSelect.innerHTML = `<option>Error fetching</option>`;
            showStatus(`Error fetching models: ${error.message}`, 'error');
            addLogEntry(`Failed to fetch models: ${error.message}`, 'error');
        } finally {
            // Restore original settings in case user cancels
            await fetchLlmSettings(); 
            modalLlmModelSelect.disabled = false;
        }
    }
    
    async function fetchPromptTemplates() {
        try {
            clientState.promptTemplates = await handleApiResponse(fetch('/api/prompt_templates'));
            populateTemplateSelect();
            addLogEntry('Prompt templates loaded.', 'info');
        } catch(error) {
            showStatus('Could not load prompt templates.', 'error');
            addLogEntry(`Error loading prompt templates: ${error.message}`, 'error');
        }
    }
    
    function populateTemplateSelect() {
        if (!templateSelect) return;
        const currentVal = templateSelect.value;
        templateSelect.innerHTML = '<option value="">-- Select Template --</option>';
        clientState.promptTemplates.forEach(t => {
            const option = document.createElement('option');
            option.value = t.name;
            option.textContent = t.name;
            templateSelect.appendChild(option);
        });
        templateSelect.value = currentVal;
    }

    // --- Tree Rendering & Manipulation ---
    function renderTree(items, parentDomElement) {
        items.sort((a, b) => (a.is_dir === b.is_dir) ? a.name.localeCompare(b.name, undefined, { numeric: true }) : a.is_dir ? -1 : 1);
        items.forEach(item => {
            const li = document.createElement('li');
            li.className = 'flex flex-col text-sm';
            
            const itemRow = document.createElement('div');
            itemRow.className = 'item-row flex items-center py-0.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded';

            // let isMarkedForRemoval = clientState.markedForRemovalPaths.has(item.path);
            // if (isMarkedForRemoval) li.classList.add('marked-for-removal');
            
            let toggleIcon = null;
            if (item.is_dir && item.children && item.children.length > 0) {
                toggleIcon = document.createElement('span');
                toggleIcon.className = 'toggle-icon mr-1 cursor-pointer text-xs';
                itemRow.appendChild(toggleIcon);
            }

            const removalBtn = document.createElement('button');
            removalBtn.className = 'removal-toggle-btn text-xs p-1 mx-1.5 rounded bg-red-200 dark:bg-red-800 hover:bg-red-300 dark:hover:bg-red-700 text-red-700 dark:text-red-100';
            itemRow.appendChild(removalBtn);

            const label = document.createElement('label');
            label.className = 'item-label flex items-center cursor-pointer flex-grow py-0.5 px-1';
            label.dataset.path = item.path;
            label.title = item.path + (item.tooltip ? ` (${item.tooltip})` : '');
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'tree-checkbox form-checkbox h-3.5 w-3.5 text-blue-600 border-gray-300 rounded mr-1.5 flex-shrink-0 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600';
            checkbox.disabled = !item.can_be_checked;
            label.appendChild(checkbox);

            let sigButton = null;
            if (item.is_signature_candidate) { 
                sigButton = document.createElement('button');
                sigButton.textContent = 'S';
                sigButton.className = 'sig-button mr-1.5 border rounded bg-purple-200 dark:bg-purple-600 hover:bg-purple-300 dark:hover:bg-purple-500 text-purple-700 dark:text-purple-100';
                sigButton.title = 'Toggle Signatures only';
                sigButton.disabled = !item.can_be_checked; // Disable if file cannot be checked
                label.appendChild(sigButton);

                sigButton.addEventListener('click', e => {
                    e.stopPropagation();
                    e.preventDefault();
                    if (li.classList.contains('marked-for-removal') || !item.can_be_checked) return;

                    const currentSelection = clientState.checkedTreePathsMap.get(item.path);
                    if (currentSelection === 'signatures') {
                        clientState.checkedTreePathsMap.delete(item.path); // Toggle off signatures
                        addLogEntry(`Deselected signatures for: ${item.name}`, 'info');
                    } else {
                        clientState.checkedTreePathsMap.set(item.path, 'signatures'); // Set to signatures
                        addLogEntry(`Selected signatures for: ${item.name}`, 'info');
                    }
                    applySelectionsToTree(); // Re-apply selections to update UI
                    saveProjectState();
                });
            }
            
            const iconSpan = document.createElement('span');
            iconSpan.className = 'icon mr-1.5 flex-shrink-0';
            iconSpan.innerHTML = item.is_dir ? '📁' : (item.is_text ? '📄' : '▫️');
            label.appendChild(iconSpan);

            const nameSpan = document.createElement('span');
            nameSpan.textContent = item.name + (item.is_dir ? '/' : '');
            nameSpan.className = 'truncate';
            label.appendChild(nameSpan);

            itemRow.appendChild(label);
            li.appendChild(itemRow);

            let childrenUl = null;
            if (item.is_dir && item.children && item.children.length > 0) {
                childrenUl = document.createElement('ul');
                childrenUl.className = 'list-none p-0 m-0 ml-4 hidden';
                renderTree(item.children, childrenUl);
                li.appendChild(childrenUl);
            }
            
            const updateToggleIcon = () => {
                if(toggleIcon) toggleIcon.innerHTML = childrenUl.classList.contains('hidden') ? '▶️' : '🔽';
            };
            
            if (toggleIcon) {
                toggleIcon.addEventListener('click', (e) => {
                    e.stopPropagation();
                    childrenUl.classList.toggle('hidden');
                    updateToggleIcon();
                    addLogEntry(`Toggled directory: ${item.name}`, 'info');
                });
            }
            
            // Removal button logic
            removalBtn.addEventListener('click', e => {
                e.stopPropagation();
                const isNowMarked = !clientState.markedForRemovalPaths.has(item.path);
                
                const pathsToUpdate = [item.path];
                if (item.is_dir) {
                    // Collect all descendant paths
                    li.querySelectorAll('.item-label').forEach(descLabel => pathsToUpdate.push(descLabel.dataset.path));
                }

                pathsToUpdate.forEach(path => {
                    if (isNowMarked) {
                        clientState.markedForRemovalPaths.add(path);
                        clientState.checkedTreePathsMap.delete(path); // If marked for removal, it cannot be selected
                        addLogEntry(`Marked for removal: ${Path.basename(path)}`, 'info');
                    } else {
                        clientState.markedForRemovalPaths.delete(path);
                        addLogEntry(`Restored from removal: ${Path.basename(path)}`, 'info');
                    }
                });
                
                applySelectionsToTree(); // Re-apply selections to update UI
                saveProjectState();
            });

            // Checkbox logic for 'full' content
            checkbox.addEventListener('change', e => {
                if(li.classList.contains('marked-for-removal') || !item.can_be_checked) {
                    e.target.checked = false; // Prevent checking if removed or uncheckable
                    addLogEntry(`Cannot select removed/uncheckable item: ${item.name}`, 'warning');
                    return;
                }
                const isChecked = e.target.checked;
                if (isChecked) {
                    clientState.checkedTreePathsMap.set(item.path, 'full');
                    addLogEntry(`Selected for full content: ${item.name}`, 'info');
                } else {
                    clientState.checkedTreePathsMap.delete(item.path);
                    addLogEntry(`Deselected: ${item.name}`, 'info');
                }

                if (item.is_dir) {
                    propagateCheckState(li, isChecked); // Propagate full selection only
                }

                applySelectionsToTree(); // Re-apply selections to update UI
                saveProjectState();
            });
            
            updateToggleIcon();
            // Initial application of selection state
            parentDomElement.appendChild(li); // Append before applying selections to ensure elements exist
            applySelectionsToTree(); // Will be called again after rendering loop, but good for immediate state
        });
    }

    function propagateCheckState(listItem, isChecked) {
        // This function now only propagates 'full' selection
        listItem.querySelectorAll('li').forEach(childLi => {
            if (childLi.classList.contains('marked-for-removal')) return; // Do not touch removed items

            const checkbox = childLi.querySelector('.tree-checkbox:not(:disabled)');
            if (checkbox) {
                const path = childLi.querySelector('.item-label').dataset.path;
                if(isChecked) {
                    clientState.checkedTreePathsMap.set(path, 'full');
                } else {
                    clientState.checkedTreePathsMap.delete(path);
                }
            }
        });
        addLogEntry(`Propagated checkbox state for children of directory.`, 'info');
    }

    function applySelectionsToTree() {
        document.querySelectorAll('.file-tree li').forEach(li => { // Use .file-tree li to be more specific
            const label = li.querySelector('.item-label');
            if(!label) return;
            
            const path = label.dataset.path;
            const item = getTreeItemByPath(path); // Helper to get item data (can_be_checked, is_signature_candidate)
            
            if (!item) return; // Should not happen if path comes from rendered tree

            const isMarked = clientState.markedForRemovalPaths.has(path);
            li.classList.toggle('marked-for-removal', isMarked);
            
            const removalBtn = li.querySelector('.removal-toggle-btn');
            if (removalBtn) removalBtn.innerHTML = isMarked ? '↩️' : '✗';

            const checkbox = label.querySelector('.tree-checkbox');
            const sigButton = label.querySelector('.sig-button');
            const selectionType = clientState.checkedTreePathsMap.get(path);
            
            // Disable selection controls if marked for removal
            if (checkbox) checkbox.disabled = isMarked || !item.can_be_checked;
            if (sigButton) sigButton.disabled = isMarked || !item.can_be_checked;

            // Apply visual state
            if (checkbox) checkbox.checked = (selectionType === 'full');
            if (sigButton) sigButton.classList.toggle('active-sig', selectionType === 'signatures');

            // If marked for removal, ensure no selection is active visually
            if (isMarked) {
                if (checkbox) checkbox.checked = false;
                if (sigButton) sigButton.classList.remove('active-sig');
            }
        });
        updateExtractorUIStates();
    }

    // Helper function to find item data from the original tree structure
    // This assumes the tree structure is stored somewhere or accessible
    // For now, will traverse the actual DOM tree and read attributes, or ideally,
    // we'd store the full tree in clientState after loading.
    let _cachedTreeData = []; // Store the full tree response
    function getTreeItemByPath(targetPath) {
        function findInTree(nodes) {
            for (const node of nodes) {
                if (node.path === targetPath) {
                    return node;
                }
                if (node.children) {
                    const found = findInTree(node.children);
                    if (found) return found;
                }
            }
            return null;
        }
        return findInTree(_cachedTreeData);
    }


    async function performLoadTree(repopulate = false) {
        if (!clientState.activeProjectId) return;
        const project = clientState.projects.find(p => p.id === clientState.activeProjectId);
        if (!project) return;
        
        if (repopulate) {
            clientState.checkedTreePathsMap.clear();
            clientState.markedForRemovalPaths.clear();
            addLogEntry('Repopulating tree: clearing all existing selections and removals.', 'info');
        }

        showStatus('Loading project tree...', 'info');
        if (fileTreeContainer) fileTreeContainer.innerHTML = '<p class="p-4">Loading...</p>';
        
        try {
            const response = await handleApiResponse(fetch('/api/load_project_tree', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_path: project.path, filters: clientState.filterSettings })
            }));
            
            if (fileTreeContainer) fileTreeContainer.innerHTML = '';
            if (response.tree && response.tree.length > 0) {
                _cachedTreeData = response.tree; // Cache the tree data
                const rootUl = document.createElement('ul');
                rootUl.className = 'list-none p-0 m-0';
                renderTree(response.tree[0].children, rootUl);
                fileTreeContainer.appendChild(rootUl);
                applySelectionsToTree(); // Apply selections after the entire tree is rendered
                showStatus('Tree loaded successfully.', 'success');
                addLogEntry('Project tree loaded successfully.', 'success');
                switchTab('tab2');
            } else {
                if (fileTreeContainer) fileTreeContainer.innerHTML = '<p class="p-4">No files found or folder is empty/filtered.</p>';
                showStatus('No items found in project.', 'warning');
                addLogEntry('No items found in project tree or all filtered out.', 'warning');
            }
        } catch (error) {
            if (fileTreeContainer) fileTreeContainer.innerHTML = `<p class="p-4 text-red-500">Error: ${error.message}</p>`;
            showStatus(`Error loading tree: ${error.message}`, 'error');
            addLogEntry(`Failed to load project tree: ${error.message}`, 'error');
        } finally {
            updateExtractorUIStates();
        }
    }
    
    // --- Chat & Tokenizer Logic ---
    async function updateTokenCountAndProgressBar() {
        if (clientState.chatHistory.length === 0 || !clientState.llmSettings.model_name) {
            tokenProgressContainer.classList.add('hidden');
            tokenCountDisplay.textContent = '';
            return;
        }

        const fullText = clientState.chatHistory.map(m => m.content).join('\n');
        
        try {
            const response = await handleApiResponse(fetch('/api/count_tokens', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text: fullText })
            }));
            clientState.currentTokens = response.count;
            saveProjectState();

            if (clientState.modelContextSize > 0) {
                tokenProgressContainer.classList.remove('hidden');
                const percentage = (clientState.currentTokens / clientState.modelContextSize) * 100;
                tokenProgressBar.style.width = `${Math.min(percentage, 100)}%`;
                
                tokenProgressBar.className = 'h-2.5 rounded-full transition-all duration-300';
                if (percentage >= 90) {
                    tokenProgressBar.classList.add('progress-bar-danger');
                } else if (percentage >= 75) {
                    tokenProgressBar.classList.add('progress-bar-warn');
                } else {
                    tokenProgressBar.classList.add('progress-bar-safe');
                }
                tokenCountDisplay.textContent = `${clientState.currentTokens} / ${clientState.modelContextSize} tokens`;
                addLogEntry(`Token usage updated: ${clientState.currentTokens}/${clientState.modelContextSize}`, 'info');
            } else {
                 tokenCountDisplay.textContent = `${clientState.currentTokens} tokens (context size unknown)`;
                 addLogEntry(`Token count: ${clientState.currentTokens} (model context size unknown)`, 'info');
            }

        } catch (error) {
            console.error('Could not count tokens:', error);
            tokenCountDisplay.textContent = 'Token count unavailable';
            addLogEntry(`Failed to count tokens: ${error.message}`, 'error');
        }
    }

    function renderChatMessage(content, role) {
        if (!chatMessagesContainer) return;
        
        startDiscussionPlaceholder.classList.add('hidden');

        const messageWrapper = document.createElement('div');
        messageWrapper.className = `chat-message flex w-full ${role === 'user' ? 'justify-end' : 'justify-start'}`;
        
        const bubbleContainer = document.createElement('div');
        bubbleContainer.className = 'flex flex-col max-w-[85%]';

        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role} markdown-body`;
        bubble.innerHTML = DOMPurify.sanitize(marked.parse(content));

        bubbleContainer.appendChild(bubble)
        messageWrapper.appendChild(bubbleContainer);
        chatMessagesContainer.appendChild(messageWrapper);
        
        addCopyButtonsToCodeBlocks(bubble);

        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        return bubble;
    }

    function renderChatHistory() {
        if (!chatMessagesContainer) return;
        chatMessagesContainer.innerHTML = '';
        chatMessagesContainer.appendChild(startDiscussionPlaceholder);

        if (clientState.chatHistory.length > 0) {
            startDiscussionPlaceholder.classList.add('hidden');
            clientState.chatHistory.forEach(msg => renderChatMessage(msg.content, msg.role));
            addLogEntry('Rendered chat history.', 'info');
        } else {
            startDiscussionPlaceholder.classList.remove('hidden');
            tokenProgressContainer.classList.add('hidden');
            tokenCountDisplay.textContent = '';
            addLogEntry('Chat history is empty, showing start discussion placeholder.', 'info');
        }
    }

    async function handleSendMessage(messageContent) {
        if (clientState.isAIGenerating || !messageContent.trim()) {
            if (!messageContent.trim()) {
                addLogEntry('Attempted to send empty chat message.', 'warning');
            }
            return;
        }

        if (clientState.modelContextSize > 0 && clientState.currentTokens >= clientState.modelContextSize) {
            showStatus('Context window is full. Please start a new discussion.', 'error');
            addLogEntry('Chat context window is full.', 'error');
            return;
        }

        clientState.isAIGenerating = true;
        updateChatUIState();
        addLogEntry('Sending chat message to AI.', 'info');
        
        const userMessage = { role: 'user', content: messageContent };
        clientState.chatHistory.push(userMessage);
        renderChatMessage(userMessage.content, userMessage.role);
        await updateTokenCountAndProgressBar();

        const aiMessage = { role: 'assistant', content: '' };
        clientState.chatHistory.push(aiMessage);
        const aiBubble = renderChatMessage('<span class="thinking-indicator">...</span>', 'assistant');

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: clientState.chatHistory.slice(0, -1) }) // Send all but the empty AI message
            });

            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.substring(6);
                        if (dataStr.trim() === '[DONE]') break;
                        try {
                            const data = JSON.parse(dataStr);
                            if(data.error) {
                                throw new Error(data.error);
                            }
                            if (data.choices && data.choices[0].delta && data.choices[0].delta.content) {
                                const token = data.choices[0].delta.content;
                                fullResponse += token;
                                aiBubble.innerHTML = DOMPurify.sanitize(marked.parse(fullResponse + '...'));
                            }
                        } catch (e) {
                            // Might be an incomplete JSON object, ignore for now
                        }
                    }
                }
            }
            
            aiMessage.content = fullResponse;
            aiBubble.innerHTML = DOMPurify.sanitize(marked.parse(fullResponse));
            addCopyButtonsToCodeBlocks(aiBubble);
            await updateTokenCountAndProgressBar();
            addLogEntry('AI response received successfully.', 'success');

        } catch (error) {
            aiBubble.innerHTML = `<p class="text-red-500">Error: ${error.message}</p>`;
            clientState.chatHistory.pop(); // Remove the failed AI message
            addLogEntry(`Error during AI chat: ${error.message}`, 'error');
        } finally {
            clientState.isAIGenerating = false;
            updateChatUIState();
            saveProjectState();
        }
    }

    function addCopyButtonsToCodeBlocks(parentElement) {
        const codeBlocks = parentElement.querySelectorAll('pre');
        codeBlocks.forEach(block => {
            const btn = document.createElement('button');
            btn.textContent = 'Copy';
            btn.className = 'code-block-copy-btn';
            btn.addEventListener('click', () => {
                const code = block.querySelector('code').innerText;
                navigator.clipboard.writeText(code).then(
                    () => showStatus('Code copied!', 'success'),
                    () => showStatus('Failed to copy code.', 'error')
                );
            });
            block.appendChild(btn);
        });
    }

    function updateChatUIState() {
        chatSendBtn.disabled = clientState.isAIGenerating;
        chatInput.disabled = clientState.isAIGenerating;
        if(clientState.isAIGenerating) {
            chatInput.placeholder = 'AI is responding...';
        } else {
            chatInput.placeholder = "Type your message, or 'next' to continue a phased response...";
        }
    }

    // --- New Logging Modal Functions ---
    function addLogEntry(message, type = 'info') {
        const timestamp = new Date().toLocaleString();
        clientState.logMessages.push({ timestamp, type, message });
        
        // Keep only the last 200 messages to prevent excessive memory usage
        const MAX_LOG_MESSAGES = 200;
        if (clientState.logMessages.length > MAX_LOG_MESSAGES) {
            clientState.logMessages.splice(0, clientState.logMessages.length - MAX_LOG_MESSAGES);
        }
        renderLogModalContent();
    }

    function renderLogModalContent() {
        if (!logsModalContent) return;
        logsModalContent.innerHTML = ''; // Clear existing content
        if (clientState.logMessages.length === 0) {
            logsModalContent.innerHTML = '<p class="text-gray-500 dark:text-gray-400 text-center">No log messages yet.</p>';
            return;
        }

        clientState.logMessages.forEach(entry => {
            const logDiv = document.createElement('div');
            logDiv.className = `log-entry log-entry.${entry.type}`;
            logDiv.innerHTML = `<strong>[${entry.timestamp}] [${entry.type.toUpperCase()}]</strong> ${entry.message}`;
            logsModalContent.appendChild(logDiv);
        });
        logsModalContent.scrollTop = logsModalContent.scrollHeight; // Auto-scroll to bottom
    }

    function openLogsModal() {
        if (logsModal) logsModal.classList.remove('hidden');
        renderLogModalContent(); // Render content when opening
        addLogEntry('Logs modal opened.', 'info');
    }

    function closeLogsModal() {
        if (logsModal) logsModal.classList.add('hidden');
        addLogEntry('Logs modal closed.', 'info');
    }

    function clearLogs() {
        clientState.logMessages = [];
        renderLogModalContent();
        addLogEntry('All logs cleared.', 'info');
        showStatus('All logs cleared.', 'info');
    }

    // --- Event Listeners & UI Updates ---
    function updateExtractorUIStates() {
        const hasTree = fileTreeContainer && fileTreeContainer.querySelector('ul');
        const hasSelections = clientState.checkedTreePathsMap.size > 0;
        const hasOutput = rawOutputTextarea && rawOutputTextarea.value.length > 0;
        
        const tab2Btn = S('tab2-btn'), tab3Btn = S('tab3-btn'), tab4Btn = S('tab4-btn');

        if(tab2Btn) tab2Btn.disabled = !hasTree;
        if(tab3Btn) tab3Btn.disabled = !hasTree;
        if(tab4Btn) tab4Btn.disabled = !hasOutput;

        if(generateBtn) generateBtn.disabled = !hasTree || !hasSelections;
        if(copyRawBtn) copyRawBtn.disabled = !hasOutput;
        [refreshTreeBtn, aiSelectBtn, checkAllTextBtn, uncheckAllBtn].forEach(b => { if(b) b.disabled = !hasTree });
    }
    
    function switchTab(tabId) {
        document.querySelectorAll('.tab-button').forEach(btn => {
            const isActive = btn.id === `${tabId}-btn`;
            btn.classList.toggle('active', isActive);
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-content`);
        });
        addLogEntry(`Switched to tab: ${tabId.replace('tab', '')}`, 'info');
    }

    function attachEventListeners() {
        if (addProjectBtn) addProjectBtn.addEventListener('click', async () => {
            const name = prompt("Enter a name for the new project:");
            if (!name || !name.trim()) return;
            showStatus('Opening server folder dialog...', 'info');
            addLogEntry('Requesting server folder browse dialog.', 'info');
            try {
                const browseResponse = await handleApiResponse(fetch('/api/browse_server_folder', { method: 'POST' }));
                if (browseResponse.status === 'success' && browseResponse.path) {
                    const newProject = { name: name.trim(), path: browseResponse.path, starred: false };
                    await handleApiResponse(fetch('/api/projects', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(newProject) }));
                    showStatus('Project added successfully!', 'success');
                    addLogEntry(`New project "${name.trim()}" added at "${browseResponse.path}".`, 'success');
                    await fetchProjects();
                } else if (browseResponse.status === 'cancelled') {
                    showStatus('Folder selection cancelled.', 'info');
                    addLogEntry('Server folder browse cancelled.', 'info');
                }
            } catch (error) {
                showStatus(`Error adding project: ${error.message}`, 'error');
            }
        });

        if (importProjectsBtn) importProjectsBtn.addEventListener('click', () => importFileInput.click());
        if (importFileInput) importFileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) {
                addLogEntry('No file selected for project import.', 'warning');
                return;
            }

            addLogEntry(`Attempting to import projects from file: ${file.name}`, 'info');
            const reader = new FileReader();
            reader.onload = async (event) => {
                try {
                    const projects = JSON.parse(event.target.result);
                    if (!Array.isArray(projects)) throw new Error('JSON file is not an array.');
                    
                    const response = await handleApiResponse(fetch('/api/projects/import', {
                        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(projects)
                    }));

                    showStatus(`Successfully imported ${response.length} new project(s).`, 'success');
                    addLogEntry(`Successfully imported ${response.length} new project(s) from "${file.name}".`, 'success');
                    await fetchProjects();
                } catch (error) {
                    showStatus(`Import failed: ${error.message}`, 'error');
                    addLogEntry(`Project import failed: ${error.message}`, 'error');
                } finally {
                    e.target.value = ''; // Reset file input
                }
            };
            reader.readAsText(file);
        });

        if (exportProjectsBtn) exportProjectsBtn.addEventListener('click', async () => {
            const selectedIds = Array.from(document.querySelectorAll('.project-export-checkbox:checked'))
                                     .map(cb => cb.closest('.project-card').dataset.id);
            if (selectedIds.length === 0) {
                showStatus('Please select at least one project to export.', 'warning');
                addLogEntry('No projects selected for export.', 'warning');
                return;
            }
            addLogEntry(`Attempting to export ${selectedIds.length} projects.`, 'info');
            try {
                const projectsToExport = await handleApiResponse(fetch('/api/projects/export', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ project_ids: selectedIds })
                }));

                const blob = new Blob([JSON.stringify(projectsToExport, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `folder_extractor_projects_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                showStatus('Projects exported successfully.', 'success');
                addLogEntry(`Successfully exported ${projectsToExport.length} projects.`, 'success');
            } catch (error) {
                showStatus(`Export failed: ${error.message}`, 'error');
                addLogEntry(`Project export failed: ${error.message}`, 'error');
            }
        });

        if (modalLlmSettingsForm) modalLlmSettingsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if(modalSaveLlmSettingsBtn) modalSaveLlmSettingsBtn.click();
        });
        
        if (modalSaveLlmSettingsBtn) modalSaveLlmSettingsBtn.addEventListener('click', async () => {
             const settings = { 
                url: modalLlmUrlInput.value.trim(), 
                api_key: modalLlmApiKeyInput.value.trim(),
                model_name: modalLlmModelSelect.value
             };
            addLogEntry('Saving LLM settings.', 'info');
            try {
                await handleApiResponse(fetch('/api/settings/llm', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(settings)}));
                showStatus('LLM settings saved.', 'success');
                addLogEntry('LLM settings saved successfully.', 'success');
                clientState.llmSettings = settings;
                if (settingsModal) settingsModal.classList.add('hidden');
            } catch (error) {
                showStatus(`Error saving LLM settings: ${error.message}`, 'error');
                addLogEntry(`Failed to save LLM settings: ${error.message}`, 'error');
            }
        });
        
        if (settingsBtn) settingsBtn.addEventListener('click', () => {
            settingsModal.classList.remove('hidden');
            addLogEntry('Settings modal opened.', 'info');
        });
        if (modalCloseSettingsBtn) modalCloseSettingsBtn.addEventListener('click', () => {
            settingsModal.classList.add('hidden');
            addLogEntry('Settings modal closed.', 'info');
        });

        // Event listeners for the new logs modal
        if (logsBtn) logsBtn.addEventListener('click', openLogsModal);
        if (logsModalCloseBtn) logsModalCloseBtn.addEventListener('click', closeLogsModal);
        if (logsModalClearBtn) logsModalClearBtn.addEventListener('click', clearLogs);

        if (refreshModelsBtn) refreshModelsBtn.addEventListener('click', fetchLlmModels);

        if (setDefaultLollmsBtn) setDefaultLollmsBtn.addEventListener('click', () => {
            if (modalLlmUrlInput) {
                // Changed default URL to base address
                modalLlmUrlInput.value = 'http://localhost:9642';
                showStatus('Default Lollms URL has been set.', 'info');
                addLogEntry('Default Lollms URL set to http://localhost:9642.', 'info');
            }
        });

        if (apiKeyToggleBtn) {
            apiKeyToggleBtn.innerHTML = icons.eye;
            apiKeyToggleBtn.addEventListener('click', () => {
                if (modalLlmApiKeyInput.type === 'password') {
                    modalLlmApiKeyInput.type = 'text';
                    apiKeyToggleBtn.innerHTML = icons.eyeSlash;
                    addLogEntry('API Key visibility toggled ON.', 'info');
                } else {
                    modalLlmApiKeyInput.type = 'password';
                    apiKeyToggleBtn.innerHTML = icons.eye;
                    addLogEntry('API Key visibility toggled OFF.', 'info');
                }
            });
        }
        
        if (addDocsBtn) addDocsBtn.addEventListener('click', () => addDocsInput.click());
        if (addDocsInput) addDocsInput.addEventListener('change', (e) => {
            const newPaths = Array.from(e.target.files).map(file => file.name); // Using name for simplicity
            clientState.loadedDocPaths = [...new Set([...clientState.loadedDocPaths, ...newPaths])].sort();
            updateDocListUI();
            addLogEntry(`Added ${newPaths.length} documentation files.`, 'info');
            e.target.value = ''; // Reset file input
        });
        if (removeDocsBtn) removeDocsBtn.addEventListener('click', () => {
            const selected = Array.from(docList.querySelectorAll('.doc-checkbox:checked')).map(cb => cb.closest('li').dataset.path);
            clientState.loadedDocPaths = clientState.loadedDocPaths.filter(p => !selected.includes(p));
            updateDocListUI();
            addLogEntry(`Removed ${selected.length} selected documentation files.`, 'info');
        });
        if (clearDocsBtn) clearDocsBtn.addEventListener('click', () => {
            clientState.loadedDocPaths = [];
            updateDocListUI();
            addLogEntry('Cleared all documentation files.', 'info');
        });

        if (loadTemplateBtn) loadTemplateBtn.addEventListener('click', () => {
            const selectedName = templateSelect.value;
            if (!selectedName) { showStatus('No template selected.', 'warning'); addLogEntry('Load template attempted with no template selected.', 'warning'); return; }
            const template = clientState.promptTemplates.find(t => t.name === selectedName);
            if (template && customPromptTextarea) {
                customPromptTextarea.value = template.content;
                updateExtractorClientStateFromUI();
                showStatus(`Loaded template: ${selectedName}`, 'success');
                addLogEntry(`Loaded prompt template: "${selectedName}".`, 'success');
            }
        });

        if(savePromptBtn) savePromptBtn.addEventListener('click', async () => {
            const content = customPromptTextarea.value.trim();
            if (!content) {
                showStatus('Prompt is empty, cannot save.', 'warning');
                addLogEntry('Attempted to save empty prompt template.', 'warning');
                return;
            }
            const name = prompt('Enter a name for this new prompt template:');
            if (!name || !name.trim()) {
                addLogEntry('Prompt template save cancelled.', 'info');
                return;
            }

            addLogEntry(`Attempting to save prompt template: "${name.trim()}".`, 'info');
            try {
                await handleApiResponse(fetch('/api/save_template', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name.trim(), content: content })
                }));
                showStatus(`Template "${name.trim()}" saved.`, 'success');
                addLogEntry(`Prompt template "${name.trim()}" saved successfully.`, 'success');
                await fetchPromptTemplates();
                templateSelect.value = name.trim();
            } catch (error) {
                showStatus(`Error saving template: ${error.message}`, 'error');
                addLogEntry(`Failed to save prompt template: ${error.message}`, 'error');
            }
        });

        document.querySelectorAll('.tab-button').forEach(btn => btn.addEventListener('click', () => {
            if (!btn.disabled) switchTab(btn.id.replace('-btn', ''));
        }));
        
        document.querySelectorAll('.sub-tab-button').forEach(btn => {
            btn.addEventListener('click', () => {
                const isRaw = btn.id === 'raw-output-btn';
                S('raw-output-btn').classList.toggle('active', isRaw);
                S('rendered-output-btn').classList.toggle('active', !isRaw);
                S('raw-output-content').classList.toggle('active', isRaw);
                S('rendered-output-content').classList.toggle('active', !isRaw);
                addLogEntry(`Switched output sub-tab to: ${isRaw ? 'Raw Markdown' : 'Rendered Preview'}`, 'info');
            });
        });

        [customFoldersInput, customExtensionsInput, customPatternsInput, customInclusionsInput, maxFileSizeInput, customPromptTextarea]
            .filter(Boolean)
            .forEach(input => {
                input.addEventListener('input', updateExtractorClientStateFromUI);
                input.addEventListener('change', updateExtractorClientStateFromUI);
            });
        
        if(presetList) presetList.addEventListener('change', updateExtractorClientStateFromUI);

        if(backToProjectsBtn) backToProjectsBtn.addEventListener('click', () => switchView('projects'));
        if(loadTreeBtn) loadTreeBtn.addEventListener('click', () => performLoadTree(false));
        if(refreshTreeBtn) refreshTreeBtn.addEventListener('click', () => {
            refreshChoiceModal.classList.remove('hidden');
            addLogEntry('Refresh tree choice modal opened.', 'info');
        });
        if(refreshCancelBtn) refreshCancelBtn.addEventListener('click', () => {
            refreshChoiceModal.classList.add('hidden');
            addLogEntry('Refresh tree cancelled.', 'info');
        });
        if(refreshPreserveBtn) refreshPreserveBtn.addEventListener('click', () => {
            refreshChoiceModal.classList.add('hidden');
            performLoadTree(false);
            addLogEntry('Refreshing tree: preserving selections.', 'info');
        });
        if(refreshRepopulateBtn) refreshRepopulateBtn.addEventListener('click', () => {
            refreshChoiceModal.classList.add('hidden');
            performLoadTree(true);
            addLogEntry('Refreshing tree: repopulating automatically.', 'info');
        });
        if(aiSelectBtn) aiSelectBtn.addEventListener('click', async () => {
            const userGoal = customPromptTextarea.value.trim();
            if (!userGoal) {
                showStatus("Please describe your goal in the 'Custom Instructions' text area first.", 'warning');
                addLogEntry("AI Select: User goal is empty.", 'warning');
                return;
            }
            if (!clientState.llmSettings.url || !clientState.llmSettings.model_name) {
                showStatus("Please configure LLM URL and select a model in Settings first.", "error");
                addLogEntry("AI Select: LLM not configured.", 'error');
                return;
            }
            showStatus('AI is analyzing your goal and selecting files...', 'info');
            addLogEntry('Initiating AI file selection based on user goal.', 'info');
            try {
                const project = clientState.projects.find(p => p.id === clientState.activeProjectId);
                const response = await handleApiResponse(fetch('/api/llm_select_files', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ project_path: project.path, user_goal: userGoal, filters: clientState.filterSettings })
                }));
                
                if (response.files && response.files.length > 0) {
                    let selectionCount = 0;
                    clientState.checkedTreePathsMap.clear(); // Clear existing AI selections
                    response.files.forEach(fileInfo => { // fileInfo is {path: absolutePath, type: "full"|"signatures"}
                        const path = fileInfo.path;
                        const type = fileInfo.type;
                        if (!clientState.markedForRemovalPaths.has(path)) { // Only select if not marked for removal
                            clientState.checkedTreePathsMap.set(path, type); 
                            selectionCount++;
                        }
                    });
                    applySelectionsToTree();
                    showStatus(`AI selected ${selectionCount} file(s) based on your instructions.`, 'success');
                    addLogEntry(`AI successfully selected ${selectionCount} file(s).`, 'success');
                } else {
                    showStatus('AI did not suggest any files.', 'warning');
                    addLogEntry('AI did not suggest any files for selection.', 'warning');
                }
            } catch(error) { showStatus(`AI selection failed: ${error.message}`, 'error'); }
        });
        if(generateBtn) generateBtn.addEventListener('click', async () => {
            const project = clientState.projects.find(p => p.id === clientState.activeProjectId);
            const selectedFiles = Array.from(clientState.checkedTreePathsMap.entries()).map(([path, type]) => ({ path, type }));
            if (selectedFiles.length === 0) { showStatus('No files selected.', 'warning'); addLogEntry('Generation attempted with no files selected.', 'warning'); return; }
            showStatus('Generating output...', 'info');
            addLogEntry('Starting generation of project structure text.', 'info');
            switchTab('tab3');
            rawOutputTextarea.value = 'Generating...';
            renderedOutputDiv.innerHTML = '<p>Generating...</p>';
            try {
                const response = await handleApiResponse(fetch('/api/generate_structure', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        folder_path: project.path, filters: clientState.filterSettings,
                        selected_files_info: selectedFiles, custom_prompt: customPromptTextarea.value,
                        loaded_doc_paths: clientState.loadedDocPaths, hard_excluded_paths: Array.from(clientState.markedForRemovalPaths)
                    })
                }));
                rawOutputTextarea.value = response.markdown;
                renderedOutputDiv.innerHTML = DOMPurify.sanitize(marked.parse(response.markdown));
                showStatus('Output generated successfully.', 'success');
                addLogEntry('Project structure text generated successfully.', 'success');

                clientState.currentTokens = response.token_count;
                clientState.modelContextSize = 0; // Reset context size as this is initial generation
                if (tokenCountDisplay) {
                    tokenCountDisplay.textContent = response.token_count > -1 ? `${response.token_count} tokens (context size unknown)` : '';
                }
                if (tokenProgressContainer) tokenProgressContainer.classList.add('hidden');
                
            } catch (error) {
                rawOutputTextarea.value = `Error: ${error.message}`;
                renderedOutputDiv.innerHTML = `<p class="text-red-500">Error: ${error.message}</p>`;
                showStatus(`Generation failed: ${error.message}`, 'error');
                addLogEntry(`Failed to generate structure text: ${error.message}`, 'error');
            } finally { 
                updateExtractorUIStates(); 
                saveProjectState();
            }
        });
        if(copyRawBtn) copyRawBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(rawOutputTextarea.value).then(() => {
                showStatus('Copied to clipboard!', 'success');
                addLogEntry('Raw Markdown copied to clipboard.', 'success');
            }, () => {
                showStatus('Failed to copy.', 'error');
                addLogEntry('Failed to copy raw Markdown to clipboard.', 'error');
            });
        });
        if(checkAllTextBtn) checkAllTextBtn.addEventListener('click', () => {
            let count = 0;
            // Iterate through _cachedTreeData to get all eligible files
            function collectAllEligibleFiles(nodes) {
                let eligibleFiles = [];
                for (const node of nodes) {
                    if (node.is_dir) {
                        eligibleFiles = eligibleFiles.concat(collectAllEligibleFiles(node.children || []));
                    } else if (node.can_be_checked && !clientState.markedForRemovalPaths.has(node.path)) {
                        eligibleFiles.push(node.path);
                    }
                }
                return eligibleFiles;
            }
            const allEligiblePaths = collectAllEligibleFiles(_cachedTreeData);

            allEligiblePaths.forEach(path => {
                if (clientState.checkedTreePathsMap.get(path) !== 'full') {
                    clientState.checkedTreePathsMap.set(path, 'full');
                    count++;
                }
            });
            applySelectionsToTree();
            showStatus(`Checked all text files. (${count} new selections)`, 'info');
            addLogEntry(`Selected all available text files for full content. (${count} new selections)`, 'info');
            saveProjectState(); // Save state after bulk update
        });
        if(uncheckAllBtn) uncheckAllBtn.addEventListener('click', () => {
            clientState.checkedTreePathsMap.clear();
            applySelectionsToTree();
            showStatus('Unchecked all files.', 'info');
            addLogEntry('All file selections cleared.', 'info');
            saveProjectState(); // Save state after bulk update
        });
        if(themeToggle) themeToggle.addEventListener('click', () => {
            const isDark = document.documentElement.classList.toggle('dark');
            clientState.currentTheme = isDark ? 'dark' : 'light';
            themeToggle.innerHTML = isDark ? '☀️' : '🌙';
            localStorage.setItem('theme', clientState.currentTheme);
            addLogEntry(`Theme toggled to ${clientState.currentTheme}.`, 'info');
        });

        // Chat Event Listeners
        if (startDiscussionBtn) startDiscussionBtn.addEventListener('click', async () => {
            const context = rawOutputTextarea.value;
            if (!context) {
                showStatus('Generate output on Tab 3 first.', 'warning');
                addLogEntry('Cannot start discussion: No project context generated.', 'warning');
                return;
            }
            if (!clientState.llmSettings.url || !clientState.llmSettings.model_name) {
                showStatus('Please configure LLM URL and select a model in Settings first.', 'error');
                addLogEntry('Cannot start discussion: LLM settings incomplete.', 'error');
                return;
            }
            showStatus("Initializing discussion...", "info");
            addLogEntry("Initializing new AI discussion.", 'info');
            try {
                const sizeResponse = await handleApiResponse(fetch('/api/context_size'));
                clientState.modelContextSize = sizeResponse.context_size;
                showStatus("Context size loaded.", "success");
                addLogEntry(`AI model context size fetched: ${clientState.modelContextSize} tokens.`, 'success');
            } catch(e) {
                showStatus(`Could not fetch model context size: ${e.message}`, 'warning');
                addLogEntry(`Failed to fetch AI model context size: ${e.message}`, 'warning');
                clientState.modelContextSize = 0;
            }

            clientState.chatHistory = [{ role: 'system', content: `The user has provided the following project context. Your task is to act as an expert software developer and assist them with their requests based on this context.\n\n---\n\n${context}` }];
            renderChatHistory(); // Clear placeholder
            addLogEntry('Initial project context sent to AI for discussion.', 'info');
            handleSendMessage("Based on the context provided, analyze the project and propose a plan for the user's request as outlined in the initial instructions. If no specific request was made, provide a high-level overview and ask how you can help.");
        });

        if (chatForm) chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = chatInput.value;
            handleSendMessage(message);
            chatInput.value = '';
            chatInput.style.height = 'auto';
        });

        if (chatInput) {
            chatInput.addEventListener('input', () => {
                chatInput.style.height = 'auto';
                chatInput.style.height = (chatInput.scrollHeight) + 'px';
            });
            chatInput.addEventListener('keydown', (e) => {
                if(e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    chatForm.requestSubmit();
                }
            });
        }
        
        // Prompt Management in Settings
        if (importPromptsBtn) importPromptsBtn.addEventListener('click', () => importPromptsInput.click());
        if (importPromptsInput) importPromptsInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) {
                addLogEntry('No file selected for prompt import.', 'warning');
                return;
            }
            addLogEntry(`Attempting to import prompts from file: ${file.name}`, 'info');
            const reader = new FileReader();
            reader.onload = async (event) => {
                try {
                    const prompts = JSON.parse(event.target.result);
                    const { added, updated } = await handleApiResponse(fetch('/api/prompts/import', {
                        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(prompts)
                    }));
                    showStatus(`Imported ${added} new & updated ${updated} prompts.`, 'success');
                    addLogEntry(`Successfully imported ${added} new and updated ${updated} prompts from "${file.name}".`, 'success');
                    await fetchPromptTemplates();
                } catch(error) {
                    showStatus(`Prompt import failed: ${error.message}`, 'error');
                    addLogEntry(`Prompt import failed: ${error.message}`, 'error');
                } finally {
                    e.target.value = '';
                }
            };
            reader.readAsText(file);
        });

        if (exportPromptsBtn) exportPromptsBtn.addEventListener('click', async () => {
            addLogEntry('Attempting to export custom prompt templates.', 'info');
            try {
                const promptsToExport = await handleApiResponse(fetch('/api/prompts/export'));
                if (promptsToExport.length === 0) {
                    showStatus('No custom prompts to export.', 'warning');
                    addLogEntry('No custom prompts found to export.', 'warning');
                    return;
                }
                const blob = new Blob([JSON.stringify(promptsToExport, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'folder_extractor_prompts.json';
                a.click();
                URL.revokeObjectURL(url);
                showStatus('Custom prompts exported.', 'success');
                addLogEntry(`Successfully exported ${promptsToExport.length} custom prompts.`, 'success');
            } catch(error) {
                showStatus(`Export failed: ${error.message}`, 'error');
                addLogEntry(`Prompt export failed: ${error.message}`, 'error');
            }
        });
    }

    // --- Initialization ---
    function initialize() {
        const savedTheme = localStorage.getItem('theme');
        if (themeToggle) {
            const isDark = (savedTheme === 'dark') || (savedTheme === null && window.matchMedia('(prefers-color-scheme: dark)').matches);
            document.documentElement.classList.toggle('dark', isDark);
            clientState.currentTheme = isDark ? 'dark' : 'light';
            themeToggle.innerHTML = isDark ? '☀️' : '🌙';
        }
        
        // Initial log message
        addLogEntry('Application started.', 'info');
        
        populatePresetList();
        attachEventListeners();
        fetchProjects();
        fetchLlmSettings();
        fetchPromptTemplates();
        switchView('projects');
    }

    const presetOptions = ["Python Project", "Node.js Project", "Java Project (Maven/Gradle)", "Git Repository", "IDE/Editor Configs", "Operating System/Misc", "Log Files", "Binary/Archives", "Large Media Files"];
    function populatePresetList() { 
        if (!presetList) return;
        presetList.innerHTML = '';
        presetOptions.forEach(name => {
            const id = `preset-${name.replace(/[\s\/]+/g, '-').replace(/[^\w-]+/g, '')}`;
            const div = document.createElement('div');
            div.className = 'flex items-center p-1';
            div.innerHTML = `<input type="checkbox" id="${id}" value="${name}" class="preset-checkbox form-checkbox h-4 w-4 text-blue-600 rounded focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600">
                             <label for="${id}" class="ml-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">${name}</label>`;
            presetList.appendChild(div);
        });
        addLogEntry('Exclusion presets populated.', 'info');
    }

    initialize();
});
