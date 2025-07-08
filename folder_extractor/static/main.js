// static/script.js

function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('status-message');
    if (!statusDiv) { console.warn("Status div not found."); console.log(`STATUS (${type.toUpperCase()}): ${message}`); return; }
    statusDiv.textContent = message;
    statusDiv.className = 'text-sm p-1 rounded-md min-w-[200px] text-center truncate'; 
    if (type === 'error') statusDiv.classList.add('text-red-700', 'dark:text-red-300', 'bg-red-100', 'dark:bg-red-900');
    else if (type === 'warning') statusDiv.classList.add('text-yellow-700', 'dark:text-yellow-300', 'bg-yellow-100', 'dark:bg-yellow-900');
    else if (type === 'success') statusDiv.classList.add('text-green-700', 'dark:text-green-300', 'bg-green-100', 'dark:bg-green-900');
    else statusDiv.classList.add('text-blue-700', 'dark:text-blue-300', 'bg-blue-100', 'dark:bg-blue-900');
    console.log(`STATUS (${type.toUpperCase()}): ${message}`);
}

function showLoading(element, isLoading, loadingText = 'Loading...', originalText = null) {
    if (!element) return;
    if (isLoading) {
        element.disabled = true; element.classList.add('opacity-75', 'cursor-wait');
        if (originalText !== null) element.dataset.originalText = originalText;
        else if (!element.dataset.originalText) element.dataset.originalText = element.textContent;
        element.textContent = loadingText;
    } else {
        element.disabled = false; element.classList.remove('opacity-75', 'cursor-wait');
        if (element.dataset.originalText) { element.textContent = element.dataset.originalText; delete element.dataset.originalText; }
    }
}

async function handleResponse(response) {
    if (!response.ok) {
        let errorData;
        try { errorData = await response.json(); } catch (e) { errorData = { detail: (await response.text()) || `HTTP error! status: ${response.status}` }; }
        const errorMessage = errorData.detail || `HTTP error! status: ${response.status}`;
        showStatus(errorMessage, 'error'); throw new Error(errorMessage);
    }
    return response.json();
}

const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');
function activateTab(tabId) {
    tabButtons.forEach(button => {
        const isActive = button.id === `${tabId}-btn`;
        button.classList.toggle('active', isActive); button.classList.toggle('bg-white', isActive); button.classList.toggle('dark:bg-gray-700', isActive);
        button.classList.toggle('text-blue-600', isActive); button.classList.toggle('dark:text-blue-400', isActive); button.classList.toggle('border-blue-500', isActive);
        button.classList.toggle('bg-gray-200', !isActive); button.classList.toggle('dark:bg-gray-900', !isActive);
        button.classList.toggle('text-gray-600', !isActive); button.classList.toggle('dark:text-gray-400', !isActive); button.classList.toggle('border-transparent', !isActive);
    });
    tabContents.forEach(content => {
        content.classList.toggle('active', content.id === `${tabId}-content`);
        content.style.display = content.id === `${tabId}-content` ? 'flex' : 'none';
    });
}
tabButtons.forEach(button => button.addEventListener('click', () => { if (!button.disabled) activateTab(button.id.replace('-btn', '')); }));

const subTabButtons = document.querySelectorAll('.sub-tab-button');
const subTabContents = document.querySelectorAll('.sub-tab-content');
function activateSubTab(tabId) {
    subTabButtons.forEach(button => {
        const isActive = button.id === `${tabId}-btn`;
        button.classList.toggle('active', isActive); button.classList.toggle('bg-white', isActive); button.classList.toggle('dark:bg-gray-700', isActive);
        button.classList.toggle('text-blue-600', isActive); button.classList.toggle('dark:text-blue-400', isActive); button.classList.toggle('border-blue-500', isActive);
        button.classList.toggle('bg-gray-200', !isActive); button.classList.toggle('dark:bg-gray-900', !isActive);
        button.classList.toggle('text-gray-900', !isActive && !document.documentElement.classList.contains('dark'));
        button.classList.toggle('text-gray-100', !isActive && document.documentElement.classList.contains('dark'));
        button.classList.toggle('border-transparent', !isActive);
    });
    subTabContents.forEach(content => { content.style.display = content.id === `${tabId}-content` ? (content.tagName === 'TEXTAREA' ? 'block' : 'flex') : 'none'; });
}
subTabButtons.forEach(button => button.addEventListener('click', () => activateSubTab(button.id.replace('-btn', ''))));

const S = id => document.getElementById(id);
const folderPathInput = S('folder-path-input'), loadTreeBtn = S('load-tree-btn'), browseServerFolderBtn = S('browse-server-folder-btn'),
      presetList = S('preset-list'), customFoldersInput = S('custom-folders-input'), customExtensionsInput = S('custom-extensions-input'),
      customPatternsInput = S('custom-patterns-input'), dynamicExcludeInput = S('dynamic-exclude-input'), customInclusionsInput = S('custom-inclusions-input'),
      maxFileSizeInput = S('max-file-size-input'), saveOutputCheckbox = S('save-output-checkbox'), docList = S('doc-list'),
      addDocsInput = S('add-docs-input'), addDocsBtn = S('add-docs-btn'), removeDocsBtn = S('remove-docs-btn'), clearDocsBtn = S('clear-docs-btn'),
      refreshTreeBtn = S('refresh-tree-btn'), expandAllBtn = S('expand-all-btn'), collapseAllBtn = S('collapse-all-btn'),
      checkAllTextBtn = S('check-all-text-btn'), uncheckAllBtn = S('uncheck-all-btn'), fileTreeContainer = S('file-tree-container'),
      templateSelect = S('template-select'), loadTemplateBtn = S('load-template-btn'), saveTemplateBtn = S('save-template-btn'),
      manageTemplateBtn = S('manage-template-btn'), customPromptTextarea = S('custom-prompt-textarea'), generateBtn = S('generate-btn'),
      rawOutputTextarea = S('raw-output-textarea'), renderedOutputDiv = S('rendered-output-div'), copyRawBtn = S('copy-raw-btn'),
      clearOutputBtn = S('clear-output-btn'), themeToggle = S('theme-toggle'), resetSettingsBtn = S('reset-settings-btn');

const clientState = {
    folderPath: '',
    filterSettings: { selected_presets: [], custom_folders: '', custom_extensions: '', custom_patterns: '', dynamic_patterns: '', custom_inclusions: '', max_file_size_mb: 1.0 },
    saveOutputChecked: false, customPrompt: '', loadedDocPaths: [],
    checkedTreePathsMap: new Map(), 
    markedForRemovalPaths: new Set(), // Renamed from hardExcludedPathsAbs
    promptTemplates: [], currentTheme: 'light', appVersion: '2.8.3' // Version bump
};

const PRESET_PRESELECTION_RULES = {
    "Python Project": {
        include_ext: [".py", ".pyw", ".pyi", ".md", ".txt", ".ini", ".cfg", ".toml", ".yaml", ".yml", ".json", ".sh", ".cfg", ".conf"],
        include_filenames: ["requirements.txt", "setup.py", "pyproject.toml", "readme.md", "readme", "dockerfile", "docker-compose.yml", ".env.example", "manage.py", "app.py", "main.py", "wsgi.py", "asgi.py", "gunicorn.conf.py"],
        exclude_dirs_for_selection: ["venv", ".venv", "env", ".env", "build", "dist", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis", ".tox", "docs/_build", "htmlcov", "migrations"]
    },
    "Node.js Project": {
        include_ext: [".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx", ".json", ".md", ".txt", ".yaml", ".yml", ".html", ".css", ".scss", ".less", ".vue", ".svelte"],
        include_filenames: ["package.json", "readme.md", "readme", "dockerfile", "docker-compose.yml", ".env.example", "server.js", "app.js", "index.js", "main.js", "vite.config.js", "webpack.config.js", "tsconfig.json", ".eslintrc.json", ".prettierrc.json"],
        exclude_dirs_for_selection: ["node_modules", "build", "dist", ".output", ".nuxt", ".next", "coverage", "public/build", "storybook-static"]
    },
    "Java Project (Maven/Gradle)": {
        include_ext: [".java", ".kt", ".scala", ".xml", ".properties", ".yml", ".yaml", ".md", ".txt", ".gradle", ".json"],
        include_filenames: ["pom.xml", "build.gradle", "readme.md", "readme", "dockerfile", "application.properties", "application.yml", "settings.gradle"],
        exclude_dirs_for_selection: ["target", "build", ".gradle", "bin", "out"]
    },
    "Git Repository": { 
        include_ext: [".md", ".txt", ".yaml", ".yml", ".json", ".xml", ".ini", ".cfg", ".conf", ".sh", ".bat"], 
        include_filenames: ["readme.md", "readme", "license", "contributing.md", "changelog.md", "dockerfile", ".gitignore", ".gitattributes"],
        exclude_dirs_for_selection: [".git", ".vscode", ".idea"] 
    }
};

function saveStateToLocalStorage() {
    try {
        localStorage.setItem('folderExtractorState_v' + clientState.appVersion, JSON.stringify(clientState, (key, value) => {
            if (key === 'checkedTreePathsMap' && value instanceof Map) return Object.fromEntries(value);
            if (key === 'markedForRemovalPaths' && value instanceof Set) return Array.from(value);
            return value;
        }));
    } catch (e) { console.error("Error saving state:", e); showStatus("Could not save settings (localStorage full/disabled).", "error"); }
}

function loadStateFromLocalStorage() {
    const savedStateJSON = localStorage.getItem('folderExtractorState_v' + clientState.appVersion);
    if (savedStateJSON) {
        try {
            const parsedState = JSON.parse(savedStateJSON);
            if (parsedState.appVersion !== clientState.appVersion) {
                console.warn(`State from older version (${parsedState.appVersion}). Resetting.`); resetClientState(false);
            } else { Object.assign(clientState, parsedState); }
            
            clientState.checkedTreePathsMap = new Map(parsedState.checkedTreePathsMap ? Object.entries(parsedState.checkedTreePathsMap) : []);
            clientState.markedForRemovalPaths = new Set(Array.isArray(parsedState.markedForRemovalPaths) ? parsedState.markedForRemovalPaths : []);
            
            applyStateToUI();
            showStatus('Loaded settings from local storage.');
        } catch (e) { console.error('Failed to parse state:', e); resetClientState(); applyStateToUI(); }
    } else { resetClientState(true); applyStateToUI(); }
}

function resetClientState(showMsg = true) {
    clientState.folderPath = '';
    clientState.filterSettings = { selected_presets: [], custom_folders: '', custom_extensions: '', custom_patterns: '', dynamic_patterns: '', custom_inclusions: '', max_file_size_mb: 1.0 };
    clientState.saveOutputChecked = false; clientState.customPrompt = ''; clientState.loadedDocPaths = [];
    clientState.checkedTreePathsMap = new Map();
    clientState.markedForRemovalPaths = new Set();
    saveStateToLocalStorage();
    if (showMsg) showStatus('Settings reset to defaults.');
}

function applyStateToUI() {
    folderPathInput.value = clientState.folderPath;
    document.querySelectorAll('.preset-checkbox').forEach(cb => cb.checked = clientState.filterSettings.selected_presets.includes(cb.value));
    customFoldersInput.value = clientState.filterSettings.custom_folders; customExtensionsInput.value = clientState.filterSettings.custom_extensions;
    customPatternsInput.value = clientState.filterSettings.custom_patterns; dynamicExcludeInput.value = clientState.filterSettings.dynamic_patterns;
    customInclusionsInput.value = clientState.filterSettings.custom_inclusions; maxFileSizeInput.value = clientState.filterSettings.max_file_size_mb;
    saveOutputCheckbox.checked = clientState.saveOutputChecked; customPromptTextarea.value = clientState.customPrompt;
    updateDocListUI(); updateFileTreeDependentUIs(); applyCheckedPathsToTreeVisuals();
    document.documentElement.classList.toggle('dark', clientState.currentTheme === 'dark');
    themeToggle.innerHTML = clientState.currentTheme === 'dark' ? '☀️' : '🌙';
    activateTab('tab1'); activateSubTab('raw-output');
}
function updateClientStateFromUI() {
    clientState.folderPath = folderPathInput.value.trim();
    clientState.filterSettings.selected_presets = Array.from(document.querySelectorAll('.preset-checkbox:checked')).map(cb => cb.value);
    clientState.filterSettings.custom_folders = customFoldersInput.value.trim(); clientState.filterSettings.custom_extensions = customExtensionsInput.value.trim();
    clientState.filterSettings.custom_patterns = customPatternsInput.value.trim(); clientState.filterSettings.dynamic_patterns = dynamicExcludeInput.value.trim();
    clientState.filterSettings.custom_inclusions = customInclusionsInput.value.trim();
    clientState.filterSettings.max_file_size_mb = parseFloat(maxFileSizeInput.value) || 1.0;
    clientState.saveOutputChecked = saveOutputCheckbox.checked; clientState.customPrompt = customPromptTextarea.value;
    saveStateToLocalStorage(); updateFileTreeDependentUIs();
}

function updateFileTreeDependentUIs() {
    const hasFolderPath = !!clientState.folderPath;
    const hasTreeItems = fileTreeContainer.children.length > 0 && fileTreeContainer.querySelector('ul');
    const hasSelections = clientState.checkedTreePathsMap.size > 0;

    tabButtons[1].disabled = !hasFolderPath;
    [refreshTreeBtn, expandAllBtn, collapseAllBtn, checkAllTextBtn, uncheckAllBtn].forEach(btn => btn.disabled = !hasTreeItems);
    generateBtn.disabled = !hasFolderPath || !hasTreeItems || !hasSelections;
}

[folderPathInput, customFoldersInput, customExtensionsInput, customPatternsInput, dynamicExcludeInput, customInclusionsInput, maxFileSizeInput].forEach(input => {
    input.addEventListener('input', updateClientStateFromUI); input.addEventListener('change', updateClientStateFromUI);
});
saveOutputCheckbox.addEventListener('change', updateClientStateFromUI); customPromptTextarea.addEventListener('input', updateClientStateFromUI);
presetList.addEventListener('change', e => { 
    if (e.target.classList.contains('preset-checkbox')) {
        updateClientStateFromUI();
        if (e.target.checked && fileTreeContainer.querySelector('ul')) {
            applyPresetBasedPreselection();
        }
    }
});
resetSettingsBtn.addEventListener('click', () => {
    if (confirm("Reset all settings to default? This clears folder path, filters, and loaded documents.")) {
        resetClientState(); applyStateToUI(); fileTreeContainer.innerHTML = '<p class="text-gray-500 dark:text-gray-400 p-2">Load a project on Tab 1 to see the file tree.</p>'; rawOutputTextarea.value = '';
        renderedOutputDiv.innerHTML = 'Preview here.'; tabButtons[1].disabled = true; tabButtons[2].disabled = true;
    }
});

const presetOptions = ["Python Project", "Node.js Project", "Java Project (Maven/Gradle)", "Git Repository", "IDE/Editor Configs", "Operating System/Misc", "Log Files", "Binary/Archives", "Large Media Files"];
function populatePresetList() { 
    presetList.innerHTML = '';
    presetOptions.forEach(name => {
        const id = `preset-${name.replace(/[\s\/]+/g, '-').replace(/[^\w-]+/g, '')}`;
        const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.id = id; checkbox.value = name;
        checkbox.classList.add('preset-checkbox', 'form-checkbox', 'h-4', 'w-4', 'text-blue-600', 'rounded', 'focus:ring-blue-500', 'dark:focus:ring-offset-gray-800', 'dark:bg-gray-700', 'dark:border-gray-600');
        const label = document.createElement('label'); label.htmlFor = id; label.classList.add('ml-2', 'text-sm', 'text-gray-700', 'dark:text-gray-300', 'cursor-pointer'); label.textContent = name;
        const div = document.createElement('div'); div.classList.add('flex', 'items-center', 'py-1.5', 'px-2', 'my-1', 'rounded-md', 'bg-gray-100', 'dark:bg-gray-800', 'hover:bg-gray-200', 'dark:hover:bg-gray-700');
        div.appendChild(checkbox); div.appendChild(label);
        div.addEventListener('click', (e) => { if (e.target !== checkbox && e.target !== label) { checkbox.checked = !checkbox.checked; checkbox.dispatchEvent(new Event('change', { bubbles: true })); } });
        presetList.appendChild(div);
    });
}

function updateDocListUI() { 
    docList.innerHTML = '';
    if (clientState.loadedDocPaths.length === 0) {
        const li = document.createElement('li'); li.classList.add('text-sm', 'text-gray-500', 'dark:text-gray-400', 'py-2', 'text-center'); li.textContent = 'No documentation files loaded.'; docList.appendChild(li);
    } else {
        clientState.loadedDocPaths.forEach(path => {
            const li = document.createElement('li'); li.classList.add('flex', 'items-center', 'justify-between', 'py-1.5', 'px-2', 'border-b', 'border-gray-200', 'dark:border-gray-700', 'last:border-b-0', 'hover:bg-gray-100', 'dark:hover:bg-gray-700'); li.dataset.path = path;
            const fileName = path.split(/[\/\\]/).pop(); const parentDir = path.split(/[\/\\]/).slice(-2, -1)[0] || '';
            const textSpan = document.createElement('span'); textSpan.classList.add('truncate', 'text-sm', 'text-gray-700', 'dark:text-gray-300'); textSpan.title = path; textSpan.textContent = `${fileName} ${parentDir ? '('+parentDir+')' : ''}`;
            const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.classList.add('doc-checkbox', 'form-checkbox', 'h-4', 'w-4', 'text-blue-600', 'rounded', 'ml-2', 'focus:ring-blue-500');
            li.appendChild(textSpan); li.appendChild(checkbox);
            li.addEventListener('click', e => { if (e.target !== checkbox) checkbox.checked = !checkbox.checked; });
            docList.appendChild(li);
        });
    }
    saveStateToLocalStorage();
}
addDocsBtn.addEventListener('click', () => addDocsInput.click());
addDocsInput.addEventListener('change', async e => { 
    let addedCount = 0; const newPaths = [];
    for (const file of e.target.files) {
        const filePath = file.webkitRelativePath || file.name;
        if (!clientState.loadedDocPaths.includes(filePath)) { newPaths.push(filePath); addedCount++; }
        else { showStatus(`Doc already added: ${file.name}`, 'warning'); }
    }
    if (addedCount > 0) { clientState.loadedDocPaths.push(...newPaths); clientState.loadedDocPaths.sort(); updateDocListUI(); showStatus(`Added ${addedCount} doc(s).`, 'success');}
    addDocsInput.value = '';
});
removeDocsBtn.addEventListener('click', () => { 
    const selectedPaths = Array.from(docList.querySelectorAll('.doc-checkbox:checked')).map(cb => cb.parentElement.dataset.path);
    if (!selectedPaths.length) { showStatus('Select docs to remove.', 'warning'); return; }
    clientState.loadedDocPaths = clientState.loadedDocPaths.filter(p => !selectedPaths.includes(p)); updateDocListUI(); showStatus(`Removed ${selectedPaths.length} doc(s).`, 'success');
});
clearDocsBtn.addEventListener('click', () => { 
    if (!clientState.loadedDocPaths.length) { showStatus('Doc list empty.', 'info'); return; }
    if (confirm('Remove all loaded docs?')) { clientState.loadedDocPaths = []; updateDocListUI(); showStatus('Cleared all docs.', 'success'); }
});

function renderTree(itemsToRender, parentDomElement, isRoot = true) {
    itemsToRender.sort((a, b) => (a.is_dir && !b.is_dir) ? -1 : (!a.is_dir && b.is_dir) ? 1 : a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }));
    itemsToRender.forEach(itemData => {
        const li = document.createElement('li');
        li.classList.add('flex', 'flex-col', 'text-sm');
        const itemRow = document.createElement('div');
        itemRow.classList.add('flex', 'items-center', 'py-0.5', 'hover:bg-gray-100', 'dark:hover:bg-gray-700', 'rounded');
        
        const isMarkedForRemoval = clientState.markedForRemovalPaths.has(itemData.path);
        if (isMarkedForRemoval) {
            li.classList.add('marked-for-removal');
        }

        const removalToggleButton = document.createElement('button');
        removalToggleButton.innerHTML = isMarkedForRemoval ? '↩️' : '✗'; // Undo or X mark
        removalToggleButton.classList.add('removal-toggle-btn', 'text-xs', 'p-0.5', 'mr-1.5', 'border', 'rounded', 'bg-red-200', 'dark:bg-red-700', 'hover:bg-red-300', 'dark:hover:bg-red-600', 'text-red-700', 'dark:text-red-100');
        removalToggleButton.title = isMarkedForRemoval ? 'Restore this item to the project.' : 'Mark this item for removal from the final output.';
        
        const label = document.createElement('label'); // Define label here so it's in scope for the listener
        label.classList.add('flex', 'items-center', 'cursor-pointer', 'flex-grow', 'py-0.5', 'px-1');
        label.dataset.path = itemData.path;
        label.title = itemData.path + (itemData.tooltip ? ` (${itemData.tooltip})` : '');

        removalToggleButton.addEventListener('click', (e) => {
            e.stopPropagation();
            const isNowMarked = li.classList.toggle('marked-for-removal');
            
            if (isNowMarked) { // Item is now marked for removal
                clientState.markedForRemovalPaths.add(itemData.path);
                removalToggleButton.innerHTML = '↩️';
                removalToggleButton.title = 'Restore this item to the project.';

                // Uncheck and remove from selection maps
                clientState.checkedTreePathsMap.delete(itemData.path);
                const checkbox = label.querySelector('.tree-checkbox');
                if (checkbox) checkbox.checked = false;
                const sigButton = label.querySelector('.sig-button');
                if (sigButton) sigButton.classList.remove('active-sig');
                propagateFullCheckToChildren(li, false); // Uncheck all children too
                
                showStatus(`Marked '${itemData.name}' for removal.`, 'info');
            } else { // Item is now restored
                clientState.markedForRemovalPaths.delete(itemData.path);
                removalToggleButton.innerHTML = '✗';
                removalToggleButton.title = 'Mark this item for removal from the final output.';
                showStatus(`Restored '${itemData.name}'.`, 'info');
            }
            saveStateToLocalStorage();
            updateFileTreeDependentUIs();
        });
        itemRow.appendChild(removalToggleButton);

        const checkbox = document.createElement('input'); checkbox.type = 'checkbox';
        checkbox.classList.add('tree-checkbox', 'form-checkbox', 'h-3.5', 'w-3.5', 'text-blue-600', 'border-gray-300', 'rounded', 'mr-1.5', 'flex-shrink-0', 'focus:ring-blue-500', 'dark:bg-gray-700', 'dark:border-gray-600');
        checkbox.disabled = !itemData.can_be_checked; if (itemData.tooltip) checkbox.title = itemData.tooltip;
        if (clientState.checkedTreePathsMap.get(itemData.path) === 'full') checkbox.checked = true;

        const iconSpan = document.createElement('span'); iconSpan.classList.add('icon', 'mr-1.5', 'flex-shrink-0');
        const nameSpan = document.createElement('span'); nameSpan.textContent = itemData.name + (itemData.is_dir ? '/' : ''); nameSpan.classList.add('truncate');
        
        if (itemData.is_signature_candidate) { 
            const sigButton = document.createElement('button'); sigButton.textContent = 'S';
            sigButton.classList.add('sig-button', 'mr-1.5', 'border', 'rounded', 'bg-purple-200', 'dark:bg-purple-600', 'hover:bg-purple-300', 'dark:hover:bg-purple-500', 'text-purple-700', 'dark:text-purple-100');
            sigButton.title = 'Select for Signatures only';
            if (clientState.checkedTreePathsMap.get(itemData.path) === 'signatures') sigButton.classList.add('active-sig');

            sigButton.addEventListener('click', (e) => {
                e.stopPropagation();
                if (li.classList.contains('marked-for-removal')) return; // Don't allow selection on removed items
                const currentSelection = clientState.checkedTreePathsMap.get(itemData.path);
                if (currentSelection === 'signatures') { 
                    clientState.checkedTreePathsMap.delete(itemData.path);
                    sigButton.classList.remove('active-sig');
                } else { 
                    clientState.checkedTreePathsMap.set(itemData.path, 'signatures');
                    sigButton.classList.add('active-sig');
                    if (checkbox.checked) checkbox.checked = false; 
                }
                updateFileTreeDependentUIs(); saveStateToLocalStorage();
            });
            label.appendChild(sigButton);
        }
        
        label.appendChild(checkbox); label.appendChild(iconSpan); label.appendChild(nameSpan);
        
        checkbox.addEventListener('change', (e) => {
            if (li.classList.contains('marked-for-removal')) { e.target.checked = false; return; } // Don't allow selection
            const isChecked = e.target.checked;
            if (isChecked) {
                clientState.checkedTreePathsMap.set(itemData.path, 'full');
                const sigButton = label.querySelector('.sig-button'); 
                if (sigButton) sigButton.classList.remove('active-sig');
            } else { 
                if (clientState.checkedTreePathsMap.get(itemData.path) === 'full') {
                    clientState.checkedTreePathsMap.delete(itemData.path);
                }
            }
            propagateFullCheckToChildren(li, isChecked);
            updateFileTreeDependentUIs(); saveStateToLocalStorage();
        });
        
        let toggleIconElement = null, childrenUl = null;
        if (itemData.is_dir) {
            iconSpan.innerHTML = '📁';
            if (itemData.children && itemData.children.length > 0) {
                li.classList.add('has-children');
                toggleIconElement = document.createElement('span'); toggleIconElement.innerHTML = '▶️';
                toggleIconElement.classList.add('toggle-icon', 'mr-1', 'cursor-pointer', 'text-xs', 'select-none', 'flex-shrink-0');
                childrenUl = document.createElement('ul'); childrenUl.classList.add('list-none', 'p-0', 'm-0', 'ml-4', 'hidden');
                toggleIconElement.addEventListener('click', (e) => { e.stopPropagation(); childrenUl.classList.toggle('hidden'); toggleIconElement.innerHTML = childrenUl.classList.contains('hidden') ? '▶️' : '🔽'; });
                nameSpan.classList.add('cursor-pointer'); nameSpan.addEventListener('click', (e) => { e.stopPropagation(); if (toggleIconElement) toggleIconElement.click(); });
            }
        } else if (itemData.is_text) iconSpan.innerHTML = '📄'; else iconSpan.innerHTML = '▫️';

        if (!itemData.can_be_checked) { label.classList.add('opacity-60', 'cursor-not-allowed'); nameSpan.classList.add('text-gray-500', 'dark:text-gray-400'); }
        
        if (toggleIconElement) itemRow.appendChild(toggleIconElement);
        itemRow.appendChild(label); li.appendChild(itemRow);
        if (childrenUl) { renderTree(itemData.children, childrenUl, false); li.appendChild(childrenUl); }
        parentDomElement.appendChild(li);
    });
}

function propagateFullCheckToChildren(listItemElement, isChecked) {
    const isDir = listItemElement.querySelector('.icon').textContent === '📁';
    if (isDir) {
        const childListItems = listItemElement.querySelectorAll('ul > li');
        childListItems.forEach(childLi => {
            const checkbox = childLi.querySelector('div > label > .tree-checkbox:not(:disabled)');
            if (!checkbox) return;
            // Only propagate check action to items that are NOT marked for removal
            if (isChecked && childLi.classList.contains('marked-for-removal')) {
                return; // Skip checking this removed item
            }

            if (checkbox.checked !== isChecked) {
                checkbox.checked = isChecked;
                const childPath = checkbox.closest('label').dataset.path;
                const childSigButton = childLi.querySelector('div > label > .sig-button');
                if (isChecked) { 
                    clientState.checkedTreePathsMap.set(childPath, 'full');
                    if (childSigButton) childSigButton.classList.remove('active-sig');
                } else { 
                    if (clientState.checkedTreePathsMap.get(childPath) === 'full') {
                        clientState.checkedTreePathsMap.delete(childPath);
                    }
                }
            }
        });
    }
}

function applyCheckedPathsToTreeVisuals() {
    fileTreeContainer.querySelectorAll('li').forEach(liItem => {
        const itemRow = liItem.querySelector('div.flex.items-center');
        if(!itemRow) return;

        const label = itemRow.querySelector('label[data-path]');
        if (!label) return;
        const path = label.dataset.path;
        const selectionType = clientState.checkedTreePathsMap.get(path);

        const checkbox = label.querySelector('.tree-checkbox');
        const sigButton = label.querySelector('.sig-button');
        const removalToggleButton = itemRow.querySelector('.removal-toggle-btn');
        
        // Handle marking for removal visual state
        const isMarked = clientState.markedForRemovalPaths.has(path);
        liItem.classList.toggle('marked-for-removal', isMarked);
        if (removalToggleButton) {
            removalToggleButton.innerHTML = isMarked ? '↩️' : '✗';
            removalToggleButton.title = isMarked ? 'Restore this item to the project.' : 'Mark this item for removal from the final output.';
        }

        // Handle selection visual state
        if (checkbox) checkbox.checked = (selectionType === 'full');
        if (sigButton) sigButton.classList.toggle('active-sig', selectionType === 'signatures');
    });
}

async function performLoadTree() {
    const folderPath = folderPathInput.value.trim();
    if (!folderPath) { showStatus('Please enter a folder path.', 'warning'); return; }
    
    rawOutputTextarea.value = ""; renderedOutputDiv.innerHTML = "Preview here.";
    copyRawBtn.disabled = true; tabButtons[2].disabled = true;

    showLoading(loadTreeBtn, true, 'Loading...', 'Load Project Tree'); showLoading(refreshTreeBtn, true, 'Refreshing...', 'Refresh');
    showStatus('Loading project tree...', 'info'); fileTreeContainer.innerHTML = '<p class="p-4 text-gray-500 dark:text-gray-400">Loading tree...</p>';

    try {
        const response = await fetch('/api/load_project_tree', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                folder_path: folderPath, 
                filters: clientState.filterSettings,
            })
        });
        const data = await handleResponse(response);
        fileTreeContainer.innerHTML = ''; 

        if (data.tree && data.tree.length > 0 && data.tree[0]) {
            const rootNode = data.tree[0]; const topLevelItems = rootNode.children || [];
            const rootUl = document.createElement('ul'); rootUl.classList.add('list-none', 'p-0', 'm-0');
            fileTreeContainer.appendChild(rootUl);

            if (topLevelItems.length > 0) renderTree(topLevelItems, rootUl, true);
            else {
                const emptyMsgLi = document.createElement('li'); emptyMsgLi.textContent = `Folder "${rootNode.name || 'Root'}" empty or all items filtered.`;
                emptyMsgLi.classList.add('text-gray-500','dark:text-gray-400', 'p-1', 'italic'); rootUl.appendChild(emptyMsgLi);
            }
            showStatus(`Tree for "${rootNode.name || folderPath}" loaded.`, 'success');
            applyCheckedPathsToTreeVisuals(); 
            applyPresetBasedPreselection(); 
            tabButtons[1].disabled = false; activateTab('tab2');
        } else {
            fileTreeContainer.innerHTML = '<p class="p-4 text-gray-500 dark:text-gray-400">No items found or folder empty/inaccessible/fully filtered.</p>';
            showStatus('No items found or folder empty/inaccessible/fully filtered.', 'warning'); tabButtons[1].disabled = false;
        }
    } catch (error) {
        console.error('Error loading tree:', error);
        fileTreeContainer.innerHTML = `<p class="p-4 text-red-600 dark:text-red-400">Error loading tree: ${error.message}.</p>`;
        tabButtons[1].disabled = true;
    } finally {
        showLoading(loadTreeBtn, false); showLoading(refreshTreeBtn, false); updateClientStateFromUI();
    }
}
loadTreeBtn.addEventListener('click', performLoadTree); refreshTreeBtn.addEventListener('click', performLoadTree);

browseServerFolderBtn.addEventListener('click', async () => { 
    showLoading(browseServerFolderBtn, true, 'Browsing...', 'Browse Server Folder (Server-Side)'); showStatus('Opening server folder dialog...', 'info');
    try {
        const response = await fetch('/api/browse_server_folder', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
        const data = await handleResponse(response);
        if (data.status === 'success' && data.path) { folderPathInput.value = data.path; updateClientStateFromUI(); showStatus(`Server returned: ${data.path}. Click 'Load Tree'.`, 'success'); }
        else if (data.status === 'cancelled') showStatus('Server folder selection cancelled.', 'info');
        else showStatus(`Unexpected response from server browse: ${JSON.stringify(data)}`, 'error');
    } catch (error) { console.error('Error browsing server folder:', error); showStatus(`Failed to browse server folder: ${error.message}.`, 'error'); }
    finally { showLoading(browseServerFolderBtn, false); }
});

function expandCollapseTree(expand, element = fileTreeContainer) { 
    const toggleIcons = element.querySelectorAll('li.has-children > div > span.toggle-icon');
    toggleIcons.forEach(toggle => {
        const childUl = toggle.closest('li').querySelector('ul');
        if (childUl) {
            const isCurrentlyHidden = childUl.classList.contains('hidden');
            if (expand && isCurrentlyHidden) toggle.click(); else if (!expand && !isCurrentlyHidden) toggle.click();
        }
    });
    if (expand) setTimeout(() => { element.querySelectorAll('li.has-children > ul:not(.hidden)').forEach(ul => expandCollapseTree(expand, ul)); }, 50);
}
expandAllBtn.addEventListener('click', () => expandCollapseTree(true)); collapseAllBtn.addEventListener('click', () => expandCollapseTree(false));

checkAllTextBtn.addEventListener('click', () => {
    showStatus('Checking all for full content...', 'info');
    fileTreeContainer.querySelectorAll('li').forEach(li => {
        if (li.classList.contains('marked-for-removal')) {
            return;
        }
        const checkbox = li.querySelector('.tree-checkbox:not(:disabled)');
        if (checkbox) {
            const path = checkbox.closest('label').dataset.path;
            checkbox.checked = true;
            clientState.checkedTreePathsMap.set(path, 'full');
            const sigButton = checkbox.closest('label').querySelector('.sig-button');
            if (sigButton) sigButton.classList.remove('active-sig');
        }
    });
    saveStateToLocalStorage(); updateFileTreeDependentUIs(); applyCheckedPathsToTreeVisuals();
    showStatus('All checkable items set to "full content".', 'success');
});
uncheckAllBtn.addEventListener('click', () => {
    showStatus('Unchecking all items...', 'info');
    clientState.checkedTreePathsMap.clear();
    fileTreeContainer.querySelectorAll('.tree-checkbox:not(:disabled)').forEach(cb => cb.checked = false);
    fileTreeContainer.querySelectorAll('.sig-button.active-sig').forEach(sb => sb.classList.remove('active-sig'));
    saveStateToLocalStorage(); updateFileTreeDependentUIs();
    showStatus('All items unchecked.', 'success');
});

async function fetchPromptTemplates() { 
    try {
        const response = await fetch('/api/prompt_templates'); const data = await handleResponse(response);
        clientState.promptTemplates = data.map(t => ({ name: t.name, content: t.content })); populateTemplateSelect();
    } catch (error) { console.error('Error fetching prompt templates:', error); showStatus('Failed to load prompt templates.', 'error'); }
}
function populateTemplateSelect() { 
    templateSelect.innerHTML = '<option value="">-- Select Template --</option>';
    clientState.promptTemplates.forEach(t => { const option = document.createElement('option'); option.value = t.name; option.textContent = t.name; templateSelect.appendChild(option); });
    const foundTemplate = clientState.promptTemplates.find(t => t.content.trim() === customPromptTextarea.value.trim());
    if (foundTemplate) templateSelect.value = foundTemplate.name;
}
loadTemplateBtn.addEventListener('click', () => { 
    const selectedName = templateSelect.value; if (!selectedName) { showStatus('No template selected.', 'warning'); return; }
    const template = clientState.promptTemplates.find(t => t.name === selectedName);
    if (template) {
        let content = template.content;
        const folderName = clientState.folderPath ? clientState.folderPath.split(/[\/\\]/).pop() : 'UnknownProject';
        content = content.replace(/{FOLDER_NAME}/g, folderName).replace(/{FOLDER_PATH}/g, clientState.folderPath || 'N/A')
                         .replace(/{DATE}/g, new Date().toISOString().slice(0, 10)).replace(/{TIME}/g, new Date().toLocaleTimeString())
                         .replace(/{DATETIME}/g, new Date().toLocaleString()).replace(/{AUTHOR}/g, 'User')
                         .replace(/{USER_REQUEST}/g, '[Your specific request here]');
        customPromptTextarea.value = content; updateClientStateFromUI(); showStatus(`Loaded template: ${selectedName}`, 'success');
    } else showStatus(`Template '${selectedName}' not found.`, 'error');
});
saveTemplateBtn.addEventListener('click', async () => { 
    const content = customPromptTextarea.value.trim(); if (!content) { showStatus('Prompt empty.', 'warning'); return; }
    let name = prompt('Enter template name:'); if (!name) return; name = name.trim(); if (!name) { alert('Name cannot be empty.'); return; }
    const existing = clientState.promptTemplates.find(t => t.name === name);
    if (existing && existing.content !== content && !confirm(`Template '${name}' exists. Overwrite?`)) return;
    if (existing && existing.content === content) { showStatus(`Template '${name}' already exists.`, 'info'); templateSelect.value = name; return; }
    try {
        const response = await fetch('/api/save_template', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, content }) });
        const data = await handleResponse(response); showStatus(data.message || `Template '${name}' saved.`, data.status.startsWith('success') || data.status.startsWith('reverted') ? 'success' : 'warning');
        await fetchPromptTemplates(); templateSelect.value = name; updateClientStateFromUI();
    } catch (error) { console.error('Error saving template:', error); showStatus(`Failed to save template: ${error.message}`, 'error'); }
});
manageTemplateBtn.addEventListener('click', async () => { 
    const action = prompt("Manage Templates:\n1. Delete/Revert template\n2. Copy template\nEnter action (1 or 2):"); if (!action) return;
    if (action === '1') {
        const nameToDelete = prompt("Enter exact name of template to delete/revert:"); if (!nameToDelete) return;
        const templateToDelete = clientState.promptTemplates.find(t => t.name === nameToDelete); if (!templateToDelete) { showStatus(`Template '${nameToDelete}' not found.`, 'warning'); return; }
        if (!confirm(`Delete/Revert template '${nameToDelete}'?`)) return;
        try {
            const response = await fetch('/api/delete_template', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: templateToDelete.name, content: templateToDelete.content }) });
            const data = await handleResponse(response); showStatus(data.message || `Template '${nameToDelete}' processed.`, data.status.includes('success') || data.status.includes('reverted') || data.status.includes('deleted') ? 'success' : 'warning');
            await fetchPromptTemplates(); if (customPromptTextarea.value === templateToDelete.content) { customPromptTextarea.value = ""; updateClientStateFromUI(); }
        } catch (error) { console.error('Error deleting template:', error); showStatus(`Failed to delete template: ${error.message}`, 'error'); }
    } else if (action === '2') {
        const nameToCopy = prompt("Enter exact name of template to copy:"); if (!nameToCopy) return;
        const original = clientState.promptTemplates.find(t => t.name === nameToCopy); if (!original) { showStatus(`Template '${nameToCopy}' not found.`, 'warning'); return; }
        let newName = `${original.name} (Copy)`; let count = 1; while (clientState.promptTemplates.some(t => t.name === newName)) newName = `${original.name} (Copy ${++count})`;
        if (!confirm(`Copy template '${nameToCopy}' as '${newName}'?`)) return;
        try {
            const response = await fetch('/api/save_template', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newName, content: original.content }) });
            const data = await handleResponse(response); showStatus(data.message || `Template copied as '${newName}'.`, 'success');
            await fetchPromptTemplates(); templateSelect.value = newName; customPromptTextarea.value = original.content; updateClientStateFromUI();
        } catch (error) { console.error('Error copying template:', error); showStatus(`Failed to copy template: ${error.message}`, 'error'); }
    } else showStatus('Invalid action.', 'warning');
});

generateBtn.addEventListener('click', async () => {
    const currentFolderPath = clientState.folderPath;
    if (!currentFolderPath) { showStatus('Folder path missing (Tab 1).', 'warning'); activateTab('tab1'); return; }
    if (!fileTreeContainer.children.length || !fileTreeContainer.querySelector('ul')) { showStatus('Project tree not loaded/empty (Tab 1/2).', 'warning'); activateTab('tab1'); return; }
    
    const selectedFilesForPayload = Array.from(clientState.checkedTreePathsMap.entries())
        .filter(([path, type]) => !clientState.markedForRemovalPaths.has(path))
        .map(([path, type]) => ({ path, type }));
    
    if (selectedFilesForPayload.length === 0) { 
        if (clientState.checkedTreePathsMap.size > 0) {
            showStatus('All selected files are marked for removal. Nothing to generate.', 'warning');
        } else {
            showStatus('No files selected for content/signatures.', 'warning');
        }
        activateTab('tab2'); 
        return; 
    }

    showLoading(generateBtn, true, 'Generating...', 'Generate Structure Text');
    rawOutputTextarea.value = 'Generating...'; renderedOutputDiv.innerHTML = '<p class="p-4 text-gray-500 dark:text-gray-400">Generating...</p>';
    copyRawBtn.disabled = true; tabButtons[2].disabled = false; activateTab('tab3');
    updateClientStateFromUI(); // Ensure latest custom prompt etc. is captured.

    try {
        const response = await fetch('/api/generate_structure', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                folder_path: currentFolderPath, filters: clientState.filterSettings,
                selected_files_info: selectedFilesForPayload, 
                custom_prompt: clientState.customPrompt, 
                loaded_doc_paths: clientState.loadedDocPaths,
                hard_excluded_paths: Array.from(clientState.markedForRemovalPaths)
            })
        });
        const data = await handleResponse(response);
        rawOutputTextarea.value = data.markdown;
        if (typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') renderedOutputDiv.innerHTML = DOMPurify.sanitize(marked.parse(data.markdown));
        else { renderedOutputDiv.innerHTML = '<p class="text-red-500">Markdown parser/sanitizer not loaded.</p>'; console.error("marked.js or DOMPurify not loaded.");}
        copyRawBtn.disabled = false;

        if (clientState.saveOutputChecked) {
            const projName = currentFolderPath.split(/[\/\\]/).pop() || 'project'; const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T-]/g, '');
            const filename = `folder_structure_${projName}_${timestamp}.md`; const blob = new Blob([data.markdown], { type: 'text/markdown;charset=utf-8' });
            const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = filename;
            document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
            showStatus('Output generated and download initiated.', 'success');
        } else showStatus('Output generated. View on Tab 3.', 'success');
    } catch (error) {
        console.error('Error generating structure text:', error); const errorMsg = `Error generating output: ${error.message}`;
        rawOutputTextarea.value = `\`\`\`error\n${errorMsg}\nCheck console.\n\`\`\``; renderedOutputDiv.innerHTML = `<p class="p-4 text-red-600 dark:text-red-400">${errorMsg}</p>`;
        showStatus(`Generation failed: ${error.message}`, 'error');
    } finally { showLoading(generateBtn, false); }
});

copyRawBtn.addEventListener('click', () => { 
    if (rawOutputTextarea.value) navigator.clipboard.writeText(rawOutputTextarea.value).then(() => showStatus('Raw Markdown copied.', 'success')).catch(err => { console.error('Failed to copy:', err); showStatus('Failed to copy. Check permissions.', 'error'); });
    else showStatus('Nothing to copy.', 'warning');
});
clearOutputBtn.addEventListener('click', () => { 
    rawOutputTextarea.value = ''; renderedOutputDiv.innerHTML = 'Preview here.'; copyRawBtn.disabled = true; showStatus('Output cleared.');
});
themeToggle.addEventListener('click', () => { 
    document.documentElement.classList.toggle('dark'); clientState.currentTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    themeToggle.innerHTML = clientState.currentTheme === 'dark' ? '☀️' : '🌙'; showStatus(`Theme: ${clientState.currentTheme}.`); saveStateToLocalStorage();
});

function getRelativePath(fullPath, rootPath) {
    const normalizedRoot = rootPath.endsWith('/') || rootPath.endsWith('\\') ? rootPath : rootPath + '/';
    if (fullPath.startsWith(normalizedRoot)) {
        return fullPath.substring(normalizedRoot.length);
    }
    return fullPath.split(/[\/\\]/).pop(); 
}

function applyPresetBasedPreselection() {
    if (clientState.filterSettings.selected_presets.length === 0) return;
    if (!fileTreeContainer.querySelector('ul')) return; 

    let appliedRule = null;
    for (const presetName of clientState.filterSettings.selected_presets) {
        if (PRESET_PRESELECTION_RULES[presetName]) {
            appliedRule = PRESET_PRESELECTION_RULES[presetName];
            break; 
        }
    }
    if (!appliedRule) return;

    showStatus(`Applying pre-selection for: ${clientState.filterSettings.selected_presets.find(p => PRESET_PRESELECTION_RULES[p])}...`, 'info');
    let preselectedCount = 0;
    
    fileTreeContainer.querySelectorAll('li').forEach(liItem => {
        if (liItem.classList.contains('marked-for-removal')) return;
        
        const itemRow = liItem.querySelector('div.flex.items-center');
        if(!itemRow) return;
        const label = itemRow.querySelector('label[data-path]');
        if (!label) return;

        const checkbox = label.querySelector('.tree-checkbox:not(:disabled)');
        if (!checkbox) return; 

        const fullPath = label.dataset.path;
        const relativePath = getRelativePath(fullPath, clientState.folderPath);
        const fileName = fullPath.split(/[\/\\]/).pop().toLowerCase();
        const fileExtWithDot = "." + fileName.split('.').pop();

        let shouldSelect = false;

        if (appliedRule.include_ext && appliedRule.include_ext.includes(fileExtWithDot)) {
            shouldSelect = true;
        }
        if (appliedRule.include_filenames && appliedRule.include_filenames.includes(fileName)) {
            shouldSelect = true;
        }
        
        if (shouldSelect && appliedRule.exclude_dirs_for_selection) {
            for (const dirToExclude of appliedRule.exclude_dirs_for_selection) {
                const dirToExcludeNormalized = dirToExclude.endsWith('/') ? dirToExclude : dirToExclude + '/';
                if (relativePath.toLowerCase().startsWith(dirToExcludeNormalized.toLowerCase())) {
                    shouldSelect = false;
                    break;
                }
                 if (relativePath.toLowerCase() === dirToExclude.toLowerCase()) {
                     shouldSelect = false;
                     break;
                }
            }
        }
        
        const isDir = liItem.querySelector('.icon').textContent === '📁';
        if(isDir && shouldSelect) {
            shouldSelect = false;
        }

        if (shouldSelect) {
            if (!clientState.checkedTreePathsMap.has(fullPath) || clientState.checkedTreePathsMap.get(fullPath) !== 'full') {
                 clientState.checkedTreePathsMap.set(fullPath, 'full');
                 preselectedCount++;
            }
        }
    });

    applyCheckedPathsToTreeVisuals(); 
    updateFileTreeDependentUIs();
    saveStateToLocalStorage();

    if (preselectedCount > 0) {
        showStatus(`Pre-selected ${preselectedCount} files based on project type.`, "success");
    } else {
        showStatus("No additional files matched project type pre-selection rules.", "info");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    populatePresetList(); loadStateFromLocalStorage(); fetchPromptTemplates();
    updateFileTreeDependentUIs(); activateTab('tab1'); activateSubTab('raw-output');
    showStatus('Application ready.', 'info');
});