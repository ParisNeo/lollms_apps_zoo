document.addEventListener('DOMContentLoaded', () => {
    // --- Global State & Element Selectors ---
    const S = id => document.getElementById(id);
    const
        appTitle = S('app-title'),
        statusMessage = S('status-message'),
        themeToggle = S('theme-toggle'),
        settingsBtn = S('settings-btn'),
        // Views
        projectListView = S('project-list-view'),
        extractorView = S('extractor-view'),
        // Project List View
        projectCardsContainer = S('project-cards-container'),
        addProjectBtn = S('add-project-btn'),
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
        apiKeyToggleBtn = S('api-key-toggle-btn');


    const clientState = {
        currentView: 'projects',
        activeProjectId: null,
        projects: [],
        promptTemplates: [],
        llmSettings: { url: '', api_key: '', model_name: '' },
        filterSettings: {}, 
        checkedTreePathsMap: new Map(),
        markedForRemovalPaths: new Set(),
        customPrompt: '',
        loadedDocPaths: [],
        chatHistory: [],
        isAIGenerating: false,
        modelContextSize: 0,
        currentTokens: 0,
        currentTheme: 'light',
        appVersion: '3.3.0'
    };
    
    const icons = {
        eye: `<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>`,
        eyeSlash: `<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>`
    };

    // --- Utility Functions ---
    function showStatus(message, type = 'info') {
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
            throw new Error(error.message || "A network error occurred.");
        }
    }
    
    // --- View Management ---
    function switchView(viewName, projectId = null) {
        clientState.currentView = viewName;
        if (projectListView) projectListView.classList.toggle('active', viewName === 'projects');
        if (extractorView) extractorView.classList.toggle('active', viewName === 'extractor');
        
        if (viewName === 'extractor') {
            loadProjectIntoExtractor(projectId);
        } else {
            appTitle.textContent = "Folder Extractor";
            clientState.activeProjectId = null;
        }
    }

    // --- Project Management ---
    async function fetchProjects() {
        try {
            clientState.projects = await handleApiResponse(fetch('/api/projects'));
            renderProjectCards();
        } catch (error) {
            showStatus(`Error fetching projects: ${error.message}`, 'error');
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
            return;
        }
        clientState.projects.forEach(p => {
            const card = document.createElement('div');
            card.className = 'project-card bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 flex flex-col cursor-pointer border dark:border-gray-700';
            card.dataset.id = p.id;
            card.innerHTML = `
                <div class="flex-grow">
                    <h3 class="font-bold text-lg text-gray-800 dark:text-gray-100 truncate">${p.name}</h3>
                    <p class="text-xs text-gray-500 dark:text-gray-400 break-all" title="${p.path}">${p.path}</p>
                </div>
                <div class="flex justify-between items-center mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <button class="star-btn p-2 text-gray-400 hover:text-yellow-400 ${p.starred ? 'starred' : ''}" data-action="star" title="Star project">
                        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>
                    </button>
                    <div class="space-x-2">
                        <button class="p-2 text-gray-400 hover:text-blue-500" data-action="edit" title="Edit project"><svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z"></path><path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd"></path></svg></button>
                        <button class="p-2 text-gray-400 hover:text-red-500" data-action="delete" title="Delete project"><svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 012 0v6a1 1 0 11-2 0V8z" clip-rule="evenodd"></path></svg></button>
                    </div>
                </div>`;
            card.addEventListener('click', (e) => {
                const action = e.target.closest('button')?.dataset.action;
                if (action) {
                    e.stopPropagation();
                    handleProjectAction(action, p.id);
                } else {
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
                    await fetchProjects();
                } catch (error) { showStatus(`Error starring project: ${error.message}`, 'error'); }
                break;
            case 'edit':
                const newName = prompt("Enter new project name:", project.name);
                if (newName && newName.trim() !== project.name) {
                    try {
                        await handleApiResponse(fetch(`/api/projects/${projectId}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name: newName.trim() })}));
                        await fetchProjects();
                    } catch (error) { showStatus(`Error updating project: ${error.message}`, 'error'); }
                }
                break;
            case 'delete':
                if (confirm(`Are you sure you want to delete project "${project.name}"?`)) {
                    try {
                        await handleApiResponse(fetch(`/api/projects/${projectId}`, { method: 'DELETE' }));
                        await fetchProjects();
                    } catch (error) { showStatus(`Error deleting project: ${error.message}`, 'error'); }
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
            switchView('projects');
            return;
        }
        
        clientState.activeProjectId = projectId;
        appTitle.textContent = project.name;
        
        const savedState = JSON.parse(localStorage.getItem(`projectState_${projectId}`) || '{}');

        clientState.filterSettings = savedState.filterSettings || { selected_presets: [], custom_folders: '', custom_extensions: '', custom_patterns: '', custom_inclusions: '', max_file_size_mb: 1.0 };
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
    }
    
    function saveProjectState() {
        if (!clientState.activeProjectId) return;
        const stateToSave = {
            filterSettings: clientState.filterSettings,
            checkedTreePathsMap: Object.fromEntries(clientState.checkedTreePathsMap),
            markedForRemovalPaths: Array.from(clientState.markedForRemovalPaths),
            customPrompt: customPromptTextarea.value,
            loadedDocPaths: clientState.loadedDocPaths,
            chatHistory: clientState.chatHistory,
            modelContextSize: clientState.modelContextSize,
            currentTokens: clientState.currentTokens
        };
        localStorage.setItem(`projectState_${clientState.activeProjectId}`, JSON.stringify(stateToSave));
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
        } catch(error) {
            showStatus('Could not load LLM settings.', 'warning');
        }
    }

    async function fetchLlmModels() {
        if (!modalLlmModelSelect) return;
        const currentUrl = modalLlmUrlInput.value.trim();
        if (!currentUrl) {
            showStatus("Please enter an LLM URL first.", "warning");
            return;
        }
        showStatus('Fetching models...', 'info');
        modalLlmModelSelect.disabled = true;
        modalLlmModelSelect.innerHTML = '<option>Fetching...</option>';
        try {
            // Temporarily save settings to use the URL in the modal
            await handleApiResponse(fetch('/api/settings/llm', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify({ url: currentUrl, api_key: modalLlmApiKeyInput.value.trim(), model_name: clientState.llmSettings.model_name })
            }));

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
            } else {
                modalLlmModelSelect.innerHTML = '<option>No models found</option>';
                showStatus('No models found at the specified URL.', 'warning');
            }
        } catch (error) {
            modalLlmModelSelect.innerHTML = `<option>Error fetching</option>`;
            showStatus(`Error fetching models: ${error.message}`, 'error');
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
        } catch(error) {
            showStatus('Could not load prompt templates.', 'error');
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

            const isMarkedForRemoval = clientState.markedForRemovalPaths.has(item.path);
            if (isMarkedForRemoval) li.classList.add('marked-for-removal');
            
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

            if (item.is_signature_candidate) { 
                const sigButton = document.createElement('button');
                sigButton.textContent = 'S';
                sigButton.className = 'sig-button mr-1.5 border rounded bg-purple-200 dark:bg-purple-600 hover:bg-purple-300 dark:hover:bg-purple-500 text-purple-700 dark:text-purple-100';
                sigButton.title = 'Select for Signatures only';
                label.appendChild(sigButton);

                sigButton.addEventListener('click', e => {
                    e.stopPropagation();
                    e.preventDefault();
                    if (li.classList.contains('marked-for-removal')) return;
                    const currentSelection = clientState.checkedTreePathsMap.get(item.path);
                    if (currentSelection === 'signatures') {
                        clientState.checkedTreePathsMap.delete(item.path);
                    } else {
                        clientState.checkedTreePathsMap.set(item.path, 'signatures');
                    }
                    applySelectionsToTree();
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
                });
            }
            
            const updateRemovalState = () => {
                const isMarked = clientState.markedForRemovalPaths.has(item.path);
                li.classList.toggle('marked-for-removal', isMarked);
                removalBtn.innerHTML = isMarked ? '↩️' : '✗';
                removalBtn.title = isMarked ? 'Restore this item' : 'Mark for removal';
            };
            
            removalBtn.addEventListener('click', e => {
                e.stopPropagation();
                const isNowMarked = !clientState.markedForRemovalPaths.has(item.path);
                
                const pathsToUpdate = [item.path];
                if (item.is_dir) {
                    li.querySelectorAll('.item-label').forEach(descLabel => pathsToUpdate.push(descLabel.dataset.path));
                }

                pathsToUpdate.forEach(path => {
                    if (isNowMarked) {
                        clientState.markedForRemovalPaths.add(path);
                        clientState.checkedTreePathsMap.delete(path);
                    } else {
                        clientState.markedForRemovalPaths.delete(path);
                    }
                });
                
                applySelectionsToTree();
                saveProjectState();
            });

            checkbox.addEventListener('change', e => {
                if(li.classList.contains('marked-for-removal')) {
                    e.target.checked = false;
                    return;
                }
                const isChecked = e.target.checked;
                if (isChecked) {
                    clientState.checkedTreePathsMap.set(item.path, 'full');
                } else {
                    clientState.checkedTreePathsMap.delete(item.path);
                }

                if (item.is_dir) {
                    propagateCheckState(li, isChecked);
                }

                applySelectionsToTree();
                saveProjectState();
            });
            
            updateToggleIcon();
            updateRemovalState();
            parentDomElement.appendChild(li);
        });
    }

    function propagateCheckState(listItem, isChecked) {
        listItem.querySelectorAll('li').forEach(childLi => {
            if (childLi.classList.contains('marked-for-removal')) return;

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
    }

    function applySelectionsToTree() {
        document.querySelectorAll('li').forEach(li => {
            const label = li.querySelector('.item-label');
            if(!label) return;
            
            const path = label.dataset.path;
            const isMarked = clientState.markedForRemovalPaths.has(path);
            li.classList.toggle('marked-for-removal', isMarked);
            li.querySelector('.removal-toggle-btn').innerHTML = isMarked ? '↩️' : '✗';

            const checkbox = label.querySelector('.tree-checkbox');
            const sigButton = label.querySelector('.sig-button');
            const selectionType = clientState.checkedTreePathsMap.get(path);
            
            if (checkbox) checkbox.checked = selectionType === 'full';
            if (sigButton) sigButton.classList.toggle('active-sig', selectionType === 'signatures');
        });
        updateExtractorUIStates();
    }


    async function performLoadTree(repopulate = false) {
        if (!clientState.activeProjectId) return;
        const project = clientState.projects.find(p => p.id === clientState.activeProjectId);
        if (!project) return;
        
        if (repopulate) {
            clientState.checkedTreePathsMap.clear();
            clientState.markedForRemovalPaths.clear();
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
                const rootUl = document.createElement('ul');
                rootUl.className = 'list-none p-0 m-0';
                renderTree(response.tree[0].children, rootUl);
                fileTreeContainer.appendChild(rootUl);
                applySelectionsToTree();
                showStatus('Tree loaded successfully.', 'success');
                switchTab('tab2');
            } else {
                if (fileTreeContainer) fileTreeContainer.innerHTML = '<p class="p-4">No files found or folder is empty/filtered.</p>';
                showStatus('No items found in project.', 'warning');
            }
        } catch (error) {
            if (fileTreeContainer) fileTreeContainer.innerHTML = `<p class="p-4 text-red-500">Error: ${error.message}</p>`;
            showStatus(`Error loading tree: ${error.message}`, 'error');
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
            } else {
                 tokenCountDisplay.textContent = `${clientState.currentTokens} tokens (context size unknown)`;
            }

        } catch (error) {
            console.error('Could not count tokens:', error);
            tokenCountDisplay.textContent = 'Token count unavailable';
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
        } else {
            startDiscussionPlaceholder.classList.remove('hidden');
            tokenProgressContainer.classList.add('hidden');
            tokenCountDisplay.textContent = '';
        }
    }

    async function handleSendMessage(messageContent) {
        if (clientState.isAIGenerating || !messageContent.trim()) return;

        if (clientState.modelContextSize > 0 && clientState.currentTokens >= clientState.modelContextSize) {
            showStatus('Context window is full. Please start a new discussion.', 'error');
            return;
        }

        clientState.isAIGenerating = true;
        updateChatUIState();
        
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

        } catch (error) {
            aiBubble.innerHTML = `<p class="text-red-500">Error: ${error.message}</p>`;
            clientState.chatHistory.pop(); // Remove the failed AI message
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
    }

    function attachEventListeners() {
        if (addProjectBtn) addProjectBtn.addEventListener('click', async () => {
            const name = prompt("Enter a name for the new project:");
            if (!name || !name.trim()) return;
            showStatus('Opening server folder dialog...', 'info');
            try {
                const browseResponse = await handleApiResponse(fetch('/api/browse_server_folder', { method: 'POST' }));
                if (browseResponse.status === 'success' && browseResponse.path) {
                    const newProject = { name: name.trim(), path: browseResponse.path, starred: false };
                    await handleApiResponse(fetch('/api/projects', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(newProject) }));
                    showStatus('Project added successfully!', 'success');
                    await fetchProjects();
                } else if (browseResponse.status === 'cancelled') {
                    showStatus('Folder selection cancelled.', 'info');
                }
            } catch (error) {
                showStatus(`Error adding project: ${error.message}`, 'error');
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
            try {
                await handleApiResponse(fetch('/api/settings/llm', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(settings)}));
                showStatus('LLM settings saved.', 'success');
                clientState.llmSettings = settings;
                if (settingsModal) settingsModal.classList.add('hidden');
            } catch (error) {
                showStatus(`Error saving LLM settings: ${error.message}`, 'error');
            }
        });
        
        if (settingsBtn) settingsBtn.addEventListener('click', () => {
            settingsModal.classList.remove('hidden');
        });
        if (modalCloseSettingsBtn) modalCloseSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));
        if (refreshModelsBtn) refreshModelsBtn.addEventListener('click', fetchLlmModels);

        if (setDefaultLollmsBtn) setDefaultLollmsBtn.addEventListener('click', () => {
            if (modalLlmUrlInput) {
                modalLlmUrlInput.value = 'http://localhost:9642/v1';
                showStatus('Default Lollms URL has been set.', 'info');
            }
        });

        if (apiKeyToggleBtn) {
            apiKeyToggleBtn.innerHTML = icons.eye;
            apiKeyToggleBtn.addEventListener('click', () => {
                if (modalLlmApiKeyInput.type === 'password') {
                    modalLlmApiKeyInput.type = 'text';
                    apiKeyToggleBtn.innerHTML = icons.eyeSlash;
                } else {
                    modalLlmApiKeyInput.type = 'password';
                    apiKeyToggleBtn.innerHTML = icons.eye;
                }
            });
        }
        
        if (addDocsBtn) addDocsBtn.addEventListener('click', () => addDocsInput.click());
        if (addDocsInput) addDocsInput.addEventListener('change', (e) => {
            const newPaths = Array.from(e.target.files).map(file => file.name); // Using name for simplicity
            clientState.loadedDocPaths = [...new Set([...clientState.loadedDocPaths, ...newPaths])].sort();
            updateDocListUI();
            e.target.value = ''; // Reset file input
        });
        if (removeDocsBtn) removeDocsBtn.addEventListener('click', () => {
            const selected = Array.from(docList.querySelectorAll('.doc-checkbox:checked')).map(cb => cb.closest('li').dataset.path);
            clientState.loadedDocPaths = clientState.loadedDocPaths.filter(p => !selected.includes(p));
            updateDocListUI();
        });
        if (clearDocsBtn) clearDocsBtn.addEventListener('click', () => {
            clientState.loadedDocPaths = [];
            updateDocListUI();
        });

        if (loadTemplateBtn) loadTemplateBtn.addEventListener('click', () => {
            const selectedName = templateSelect.value;
            if (!selectedName) { showStatus('No template selected.', 'warning'); return; }
            const template = clientState.promptTemplates.find(t => t.name === selectedName);
            if (template && customPromptTextarea) {
                customPromptTextarea.value = template.content;
                updateExtractorClientStateFromUI();
                showStatus(`Loaded template: ${selectedName}`, 'success');
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
        if(refreshTreeBtn) refreshTreeBtn.addEventListener('click', () => refreshChoiceModal.classList.remove('hidden'));
        if(refreshCancelBtn) refreshCancelBtn.addEventListener('click', () => refreshChoiceModal.classList.add('hidden'));
        if(refreshPreserveBtn) refreshPreserveBtn.addEventListener('click', () => {
            refreshChoiceModal.classList.add('hidden');
            performLoadTree(false);
        });
        if(refreshRepopulateBtn) refreshRepopulateBtn.addEventListener('click', () => {
            refreshChoiceModal.classList.add('hidden');
            performLoadTree(true);
        });
        if(aiSelectBtn) aiSelectBtn.addEventListener('click', async () => {
            const userGoal = customPromptTextarea.value.trim();
            if (!userGoal) {
                showStatus("Please describe your goal in the 'Custom Instructions' text area first.", 'warning');
                return;
            }
            if (!clientState.llmSettings.url || !clientState.llmSettings.model_name) {
                showStatus("Please configure LLM URL and select a model in Settings first.", "error");
                return;
            }
            showStatus('AI is analyzing your goal and selecting files...', 'info');
            try {
                const project = clientState.projects.find(p => p.id === clientState.activeProjectId);
                const response = await handleApiResponse(fetch('/api/llm_select_files', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ project_path: project.path, user_goal: userGoal, filters: clientState.filterSettings })
                }));
                if (response.files && response.files.length > 0) {
                    let selectionCount = 0;
                    response.files.forEach(path => { 
                        if (!clientState.markedForRemovalPaths.has(path) && !clientState.checkedTreePathsMap.has(path)) {
                            selectionCount++; 
                        }
                        clientState.checkedTreePathsMap.set(path, 'full'); 
                    });
                    applySelectionsToTree();
                    showStatus(`AI selected ${selectionCount} new file(s) based on your instructions.`, 'success');
                } else {
                    showStatus('AI did not suggest any files.', 'warning');
                }
            } catch(error) { showStatus(`AI selection failed: ${error.message}`, 'error'); }
        });
        if(generateBtn) generateBtn.addEventListener('click', async () => {
            const project = clientState.projects.find(p => p.id === clientState.activeProjectId);
            const selectedFiles = Array.from(clientState.checkedTreePathsMap.entries()).map(([path, type]) => ({ path, type }));
            if (selectedFiles.length === 0) { showStatus('No files selected.', 'warning'); return; }
            showStatus('Generating output...', 'info');
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
            } catch (error) {
                rawOutputTextarea.value = `Error: ${error.message}`;
                renderedOutputDiv.innerHTML = `<p class="text-red-500">Error: ${error.message}</p>`;
                showStatus(`Generation failed: ${error.message}`, 'error');
            } finally { updateExtractorUIStates(); }
        });
        if(copyRawBtn) copyRawBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(rawOutputTextarea.value).then(() => showStatus('Copied to clipboard!', 'success'), () => showStatus('Failed to copy.', 'error'));
        });
        if(checkAllTextBtn) checkAllTextBtn.addEventListener('click', () => {
            document.querySelectorAll('.tree-checkbox:not(:disabled)').forEach(cb => {
                const li = cb.closest('li');
                if (!li.classList.contains('marked-for-removal')) {
                    const path = cb.closest('.item-label').dataset.path;
                    clientState.checkedTreePathsMap.set(path, 'full');
                }
            });
            applySelectionsToTree();
        });
        if(uncheckAllBtn) uncheckAllBtn.addEventListener('click', () => {
            clientState.checkedTreePathsMap.clear();
            applySelectionsToTree();
        });
        if(themeToggle) themeToggle.addEventListener('click', () => {
            const isDark = document.documentElement.classList.toggle('dark');
            clientState.currentTheme = isDark ? 'dark' : 'light';
            themeToggle.innerHTML = isDark ? '☀️' : '🌙';
            localStorage.setItem('theme', clientState.currentTheme);
        });

        // Chat Event Listeners
        if (startDiscussionBtn) startDiscussionBtn.addEventListener('click', async () => {
            const context = rawOutputTextarea.value;
            if (!context) {
                showStatus('Generate output on Tab 3 first.', 'warning');
                return;
            }
            if (!clientState.llmSettings.url || !clientState.llmSettings.model_name) {
                showStatus('Please configure LLM URL and select a model in Settings first.', 'error');
                return;
            }
            showStatus("Initializing discussion...", "info");
            try {
                const sizeResponse = await handleApiResponse(fetch('/api/context_size'));
                clientState.modelContextSize = sizeResponse.context_size;
                showStatus("Context size loaded.", "success");
            } catch(e) {
                showStatus(`Could not fetch model context size: ${e.message}`, 'warning');
                clientState.modelContextSize = 0;
            }

            clientState.chatHistory = [{ role: 'system', content: `The user has provided the following project context. Your task is to act as an expert software developer and assist them with their requests based on this context.\n\n---\n\n${context}` }];
            renderChatHistory(); // Clear placeholder
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
    }

    initialize();
});
