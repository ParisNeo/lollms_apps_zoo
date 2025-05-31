// static/script.js

// Function to update status message
function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('status-message');
    if (!statusDiv) {
        console.warn("Status message div not found.");
        console.log(`STATUS (${type.toUpperCase()}): ${message}`);
        return;
    }
    statusDiv.textContent = message;
    statusDiv.className = 'text-sm p-1 rounded-md'; // Reset classes and add base styling
    if (type === 'error') {
        statusDiv.classList.add('text-red-700', 'dark:text-red-300', 'bg-red-100', 'dark:bg-red-900');
    } else if (type === 'warning') {
        statusDiv.classList.add('text-yellow-700', 'dark:text-yellow-300', 'bg-yellow-100', 'dark:bg-yellow-900');
    } else if (type === 'success') {
        statusDiv.classList.add('text-green-700', 'dark:text-green-300', 'bg-green-100', 'dark:bg-green-900');
    } else { // info
        statusDiv.classList.add('text-blue-700', 'dark:text-blue-300', 'bg-blue-100', 'dark:bg-blue-900');
    }
    console.log(`STATUS (${type.toUpperCase()}): ${message}`);
}

function showLoading(element, isLoading, loadingText = 'Loading...', originalText = null) {
    if (!element) return;
    if (isLoading) {
        element.disabled = true;
        element.classList.add('opacity-75', 'cursor-wait');
        if (originalText !== null) {
            element.dataset.originalText = originalText;
        } else if (!element.dataset.originalText) {
            element.dataset.originalText = element.textContent;
        }
        element.textContent = loadingText;
    } else {
        element.disabled = false;
        element.classList.remove('opacity-75', 'cursor-wait');
        if (element.dataset.originalText) {
             element.textContent = element.dataset.originalText;
             delete element.dataset.originalText; // Clean up
        }
    }
}

async function handleResponse(response) {
    if (!response.ok) {
        let errorData;
        try { errorData = await response.json(); } catch (e) {
            const textResponse = await response.text();
            errorData = { detail: textResponse || `HTTP error! status: ${response.status}` };
        }
        const errorMessage = errorData.detail || `HTTP error! status: ${response.status}`;
        showStatus(errorMessage, 'error');
        throw new Error(errorMessage);
    }
    return response.json();
}

const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');
function activateTab(tabId) {
    tabButtons.forEach(button => {
        const isActive = button.id === `${tabId}-btn`;
        button.classList.toggle('active', isActive);
        button.classList.toggle('bg-white', isActive);
        button.classList.toggle('dark:bg-gray-700', isActive);
        button.classList.toggle('text-blue-600', isActive);
        button.classList.toggle('dark:text-blue-400', isActive);
        button.classList.toggle('border-blue-500', isActive); // Active border
        button.classList.toggle('bg-gray-200', !isActive);
        button.classList.toggle('dark:bg-gray-900', !isActive);
        button.classList.toggle('text-gray-600', !isActive);
        button.classList.toggle('dark:text-gray-400', !isActive);
        button.classList.toggle('border-transparent', !isActive); // Inactive border
    });
    tabContents.forEach(content => {
        content.classList.toggle('active', content.id === `${tabId}-content`);
        content.style.display = content.id === `${tabId}-content` ? 'flex' : 'none';
    });
}
tabButtons.forEach(button => button.addEventListener('click', () => {
    if (!button.disabled) activateTab(button.id.replace('-btn', ''));
}));

const subTabButtons = document.querySelectorAll('.sub-tab-button');
const subTabContents = document.querySelectorAll('.sub-tab-content');
function activateSubTab(tabId) {
    subTabButtons.forEach(button => {
        const isActive = button.id === `${tabId}-btn`;
        button.classList.toggle('active', isActive);
        button.classList.toggle('bg-white', isActive);
        button.classList.toggle('dark:bg-gray-700', isActive);
        button.classList.toggle('text-blue-600', isActive);
        button.classList.toggle('dark:text-blue-400', isActive);
        button.classList.toggle('border-blue-500', isActive);

        button.classList.toggle('bg-gray-200', !isActive);
        button.classList.toggle('dark:bg-gray-900', !isActive);
        button.classList.toggle('text-gray-900', !isActive && !document.documentElement.classList.contains('dark'));
        button.classList.toggle('text-gray-100', !isActive && document.documentElement.classList.contains('dark'));
        button.classList.toggle('border-transparent', !isActive);

    });
    subTabContents.forEach(content => {
        content.style.display = content.id === `${tabId}-content` ? (content.tagName === 'TEXTAREA' ? 'block' : 'flex') : 'none';
    });
}
subTabButtons.forEach(button => button.addEventListener('click', () => activateSubTab(button.id.replace('-btn', ''))));

// --- Element Selectors ---
const folderPathInput = document.getElementById('folder-path-input');
const loadTreeBtn = document.getElementById('load-tree-btn');
const browseServerFolderBtn = document.getElementById('browse-server-folder-btn');
const presetList = document.getElementById('preset-list');
const customFoldersInput = document.getElementById('custom-folders-input');
const customExtensionsInput = document.getElementById('custom-extensions-input');
const customPatternsInput = document.getElementById('custom-patterns-input');
const dynamicExcludeInput = document.getElementById('dynamic-exclude-input');
const customInclusionsInput = document.getElementById('custom-inclusions-input');
const maxFileSizeInput = document.getElementById('max-file-size-input');
const saveOutputCheckbox = document.getElementById('save-output-checkbox');
const docList = document.getElementById('doc-list');
const addDocsInput = document.getElementById('add-docs-input');
const addDocsBtn = document.getElementById('add-docs-btn');
const removeDocsBtn = document.getElementById('remove-docs-btn');
const clearDocsBtn = document.getElementById('clear-docs-btn');
const refreshTreeBtn = document.getElementById('refresh-tree-btn');
const expandAllBtn = document.getElementById('expand-all-btn');
const collapseAllBtn = document.getElementById('collapse-all-btn');
const checkAllTextBtn = document.getElementById('check-all-text-btn');
const uncheckAllBtn = document.getElementById('uncheck-all-btn');
const fileTreeContainer = document.getElementById('file-tree-container');
const templateSelect = document.getElementById('template-select');
const loadTemplateBtn = document.getElementById('load-template-btn');
const saveTemplateBtn = document.getElementById('save-template-btn');
const manageTemplateBtn = document.getElementById('manage-template-btn');
const customPromptTextarea = document.getElementById('custom-prompt-textarea');
const generateBtn = document.getElementById('generate-btn');
const rawOutputTextarea = document.getElementById('raw-output-textarea');
const renderedOutputDiv = document.getElementById('rendered-output-div');
const copyRawBtn = document.getElementById('copy-raw-btn');
const clearOutputBtn = document.getElementById('clear-output-btn');
const themeToggle = document.getElementById('theme-toggle');
const resetSettingsBtn = document.getElementById('reset-settings-btn');

// --- Client State Management ---
const clientState = {
    folderPath: '',
    filterSettings: {
        selected_presets: [], custom_folders: '', custom_extensions: '', custom_patterns: '',
        dynamic_patterns: '', custom_inclusions: '', max_file_size_mb: 1.0,
    },
    saveOutputChecked: false, customPrompt: '', loadedDocPaths: [],
    checkedTreePathsAbs: new Set(), promptTemplates: [], currentTheme: 'light', appVersion: '2.8.1' // Match backend
};

function saveStateToLocalStorage() {
    try {
        localStorage.setItem('folderExtractorState_v' + clientState.appVersion, JSON.stringify(clientState, (key, value) => {
            return (key === 'checkedTreePathsAbs' && value instanceof Set) ? Array.from(value) : value;
        }));
    } catch (e) {
        console.error("Error saving state to localStorage:", e);
        showStatus("Could not save settings to local storage. It might be full or disabled.", "error");
    }
}
function loadStateFromLocalStorage() {
    const savedState = localStorage.getItem('folderExtractorState_v' + clientState.appVersion);
    if (savedState) {
        try {
            const parsedState = JSON.parse(savedState);
            // Basic version check (can be more sophisticated)
            if (parsedState.appVersion !== clientState.appVersion) {
                console.warn(`Loaded state from older version (${parsedState.appVersion}). Current: ${clientState.appVersion}. Resetting to defaults.`);
                resetClientState(false); // Don't show status message yet
            } else {
                Object.assign(clientState, parsedState);
            }
            clientState.checkedTreePathsAbs = new Set(Array.isArray(clientState.checkedTreePathsAbs) ? clientState.checkedTreePathsAbs : []);
            applyStateToUI();
            showStatus('Loaded settings from local storage.');
        } catch (e) {
            console.error('Failed to parse state from local storage:', e);
            resetClientState(); applyStateToUI(); // applyStateToUI calls showStatus
        }
    } else {
        resetClientState(true); // Show "No saved settings"
        applyStateToUI();
    }
}

function resetClientState(showMsg = true) {
    clientState.folderPath = '';
    clientState.filterSettings = {
        selected_presets: [], custom_folders: '', custom_extensions: '', custom_patterns: '',
        dynamic_patterns: '', custom_inclusions: '', max_file_size_mb: 1.0,
    };
    clientState.saveOutputChecked = false;
    clientState.customPrompt = '';
    clientState.loadedDocPaths = [];
    clientState.checkedTreePathsAbs = new Set();
    // Don't reset theme or prompt templates on general reset
    // clientState.currentTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    saveStateToLocalStorage();
    if (showMsg) showStatus('Settings reset to defaults.');
}

function applyStateToUI() {
    folderPathInput.value = clientState.folderPath;
    document.querySelectorAll('.preset-checkbox').forEach(cb => cb.checked = clientState.filterSettings.selected_presets.includes(cb.value));
    customFoldersInput.value = clientState.filterSettings.custom_folders;
    customExtensionsInput.value = clientState.filterSettings.custom_extensions;
    customPatternsInput.value = clientState.filterSettings.custom_patterns;
    dynamicExcludeInput.value = clientState.filterSettings.dynamic_patterns;
    customInclusionsInput.value = clientState.filterSettings.custom_inclusions;
    maxFileSizeInput.value = clientState.filterSettings.max_file_size_mb;
    saveOutputCheckbox.checked = clientState.saveOutputChecked;
    customPromptTextarea.value = clientState.customPrompt;
    updateDocListUI(); // Renders loadedDocPaths
    updateFileTreeDependentUIs(); // Updates buttons based on tree/selections
    
    // Apply theme
    if (clientState.currentTheme === 'dark') {
        document.documentElement.classList.add('dark');
        themeToggle.innerHTML = '☀️'; // Sun icon for light mode
    } else {
        document.documentElement.classList.remove('dark');
        themeToggle.innerHTML = '🌙'; // Moon icon for dark mode
    }
    // Initial tab states
    activateTab('tab1');
    activateSubTab('raw-output'); // Default to raw output
}
function updateClientStateFromUI() {
    clientState.folderPath = folderPathInput.value.trim();
    clientState.filterSettings.selected_presets = Array.from(document.querySelectorAll('.preset-checkbox:checked')).map(cb => cb.value);
    clientState.filterSettings.custom_folders = customFoldersInput.value.trim();
    clientState.filterSettings.custom_extensions = customExtensionsInput.value.trim();
    clientState.filterSettings.custom_patterns = customPatternsInput.value.trim();
    clientState.filterSettings.dynamic_patterns = dynamicExcludeInput.value.trim();
    clientState.filterSettings.custom_inclusions = customInclusionsInput.value.trim();
    clientState.filterSettings.max_file_size_mb = parseFloat(maxFileSizeInput.value) || 1.0;
    clientState.saveOutputChecked = saveOutputCheckbox.checked;
    clientState.customPrompt = customPromptTextarea.value;
    // checkedTreePathsAbs and loadedDocPaths are updated directly by their respective handlers
    saveStateToLocalStorage();
    updateFileTreeDependentUIs();
}

function updateFileTreeDependentUIs() {
    const hasFolderPath = !!clientState.folderPath;
    const hasTreeItems = fileTreeContainer.children.length > 0 && fileTreeContainer.querySelector('ul');
    const hasCheckedItems = clientState.checkedTreePathsAbs.size > 0;

    // Tab 2 (Project Explorer)
    tabButtons[1].disabled = !hasFolderPath;
    [refreshTreeBtn, expandAllBtn, collapseAllBtn, checkAllTextBtn, uncheckAllBtn].forEach(btn => btn.disabled = !hasTreeItems);
    
    // Tab 3 (Output) - should be disabled if no generation happened, handled by generateBtn logic primarily
    // But also disable if no folder path, as generation is impossible
    // tabButtons[2].disabled = !hasFolderPath; // Re-enable if generation happens

    generateBtn.disabled = !hasFolderPath || !hasTreeItems || !hasCheckedItems;
}


// Event listeners for UI elements to update clientState
folderPathInput.addEventListener('change', updateClientStateFromUI);
[customFoldersInput, customExtensionsInput, customPatternsInput, dynamicExcludeInput, customInclusionsInput, maxFileSizeInput].forEach(input => {
    input.addEventListener('input', updateClientStateFromUI);
    input.addEventListener('change', updateClientStateFromUI); // For selections like number input step
});
saveOutputCheckbox.addEventListener('change', updateClientStateFromUI);
customPromptTextarea.addEventListener('input', updateClientStateFromUI);
presetList.addEventListener('change', e => {
    if (e.target.classList.contains('preset-checkbox')) updateClientStateFromUI();
});
resetSettingsBtn.addEventListener('click', () => {
    if (confirm("Are you sure you want to reset all settings to their defaults? This will clear the folder path, filters, and loaded documents.")) {
        resetClientState();
        applyStateToUI(); // Re-apply to show defaults
        fileTreeContainer.innerHTML = ''; // Clear the tree display
        rawOutputTextarea.value = ''; // Clear output
        renderedOutputDiv.innerHTML = 'Preview here.';
        tabButtons[1].disabled = true; // Disable explorer tab
        tabButtons[2].disabled = true; // Disable output tab
    }
});

const presetOptions = ["Python Project", "Node.js Project", "Java Project (Maven/Gradle)", "Git Repository", "IDE/Editor Configs", "Operating System/Misc", "Log Files", "Binary/Archives", "Large Media Files"];
function populatePresetList() {
    presetList.innerHTML = ''; // Clear existing
    presetOptions.forEach(name => {
        const id = `preset-${name.replace(/[\s\/]+/g, '-').replace(/[^\w-]+/g, '')}`; // Sanitize ID
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = id;
        checkbox.value = name;
        checkbox.classList.add('preset-checkbox', 'form-checkbox', 'h-4', 'w-4', 'text-blue-600', 'rounded', 'focus:ring-blue-500', 'dark:focus:ring-offset-gray-800', 'dark:bg-gray-700', 'dark:border-gray-600');
        
        const label = document.createElement('label');
        label.htmlFor = id;
        label.classList.add('ml-2', 'text-sm', 'text-gray-700', 'dark:text-gray-300', 'cursor-pointer');
        label.textContent = name;

        const div = document.createElement('div');
        div.classList.add('flex', 'items-center', 'py-1.5', 'px-2', 'my-1', 'rounded-md', 'bg-gray-100', 'dark:bg-gray-800', 'hover:bg-gray-200', 'dark:hover:bg-gray-700');
        
        div.appendChild(checkbox);
        div.appendChild(label);
        
        // Make the whole div clickable to toggle the checkbox
        div.addEventListener('click', (e) => {
            // Prevent double-toggle if checkbox or label itself is clicked
            if (e.target !== checkbox && e.target !== label) {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change', { bubbles: true })); // Ensure change event fires
            }
        });
        presetList.appendChild(div);
    });
}

// --- Documentation Management ---
function updateDocListUI() {
    docList.innerHTML = ''; // Clear previous items
    if (clientState.loadedDocPaths.length === 0) {
        const li = document.createElement('li');
        li.classList.add('text-sm', 'text-gray-500', 'dark:text-gray-400', 'py-2', 'text-center');
        li.textContent = 'No documentation files loaded.';
        docList.appendChild(li);
    } else {
        clientState.loadedDocPaths.forEach(path => {
            const li = document.createElement('li');
            li.classList.add('flex', 'items-center', 'justify-between', 'py-1.5', 'px-2', 'border-b', 'border-gray-200', 'dark:border-gray-700', 'last:border-b-0', 'hover:bg-gray-100', 'dark:hover:bg-gray-700');
            li.dataset.path = path;

            const fileName = path.split(/[\/\\]/).pop();
            const parentDir = path.split(/[\/\\]/).slice(-2, -1)[0] || ''; // Get parent dir name
            
            const textSpan = document.createElement('span');
            textSpan.classList.add('truncate', 'text-sm', 'text-gray-700', 'dark:text-gray-300');
            textSpan.title = path;
            textSpan.textContent = `${fileName} ${parentDir ? '('+parentDir+')' : ''}`;

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.classList.add('doc-checkbox', 'form-checkbox', 'h-4', 'w-4', 'text-blue-600', 'rounded', 'ml-2', 'focus:ring-blue-500');
            
            li.appendChild(textSpan);
            li.appendChild(checkbox);

            // Click on list item toggles its checkbox
            li.addEventListener('click', e => {
                if (e.target !== checkbox) { // Don't interfere if checkbox itself is clicked
                    checkbox.checked = !checkbox.checked;
                }
            });
            docList.appendChild(li);
        });
    }
    saveStateToLocalStorage();
}
addDocsBtn.addEventListener('click', () => addDocsInput.click());
addDocsInput.addEventListener('change', async e => {
    let addedCount = 0;
    const newPaths = [];
    for (const file of e.target.files) {
        // For browser file input, `file.path` is not available for security reasons.
        // We will use `file.name` and store the File object itself if we need to read it later.
        // However, the backend expects paths. This part needs adjustment if truly reading files client-side vs. just paths.
        // For now, assuming backend handles these paths. If these are local paths, backend can't access them.
        // Let's assume these are paths the *server* can access, or we'll need a file upload mechanism.
        const filePath = file.webkitRelativePath || file.name; // webkitRelativePath for folder uploads
        if (!clientState.loadedDocPaths.includes(filePath)) {
            newPaths.push(filePath);
            addedCount++;
        } else {
            showStatus(`Documentation file already added: ${file.name}`, 'warning');
        }
    }
    if (addedCount > 0) {
        clientState.loadedDocPaths.push(...newPaths);
        clientState.loadedDocPaths.sort(); // Keep it sorted
        updateDocListUI();
        showStatus(`Added ${addedCount} documentation file(s).`, 'success');
    }
    addDocsInput.value = ''; // Reset file input
});
removeDocsBtn.addEventListener('click', () => {
    const selectedPaths = Array.from(docList.querySelectorAll('.doc-checkbox:checked')).map(cb => cb.parentElement.dataset.path);
    if (!selectedPaths.length) { showStatus('Select documentation files to remove.', 'warning'); return; }
    clientState.loadedDocPaths = clientState.loadedDocPaths.filter(p => !selectedPaths.includes(p));
    updateDocListUI();
    showStatus(`Removed ${selectedPaths.length} documentation file(s).`, 'success');
});
clearDocsBtn.addEventListener('click', () => {
    if (!clientState.loadedDocPaths.length) { showStatus('Documentation list is already empty.', 'info'); return; }
    if (confirm('Are you sure you want to remove all loaded documentation files?')) {
        clientState.loadedDocPaths = [];
        updateDocListUI();
        showStatus('Cleared all documentation files.', 'success');
    }
});

// --- Project Tree (File Explorer) ---
function renderTree(itemsToRenderInThisLevel, parentDomElementToAppendLi, isRootLevelList = true) {
    // itemsToRenderInThisLevel is expected to be an ARRAY of item objects.
    // parentDomElementToAppendLi is the UL to which the LI elements of this level will be appended.

    itemsToRenderInThisLevel.sort((a, b) => {
        if (a.is_dir && !b.is_dir) return -1; 
        if (!a.is_dir && b.is_dir) return 1;  
        return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
    });

    itemsToRenderInThisLevel.forEach(itemData => {
        const li = document.createElement('li');
        li.classList.add('flex', 'flex-col', 'text-sm'); 

        const labelContainer = document.createElement('div');
        labelContainer.classList.add('flex', 'items-center', 'py-0.5', 'hover:bg-gray-100', 'dark:hover:bg-gray-700', 'rounded');

        const label = document.createElement('label');
        label.classList.add('flex', 'items-center', 'cursor-pointer', 'flex-grow', 'py-0.5', 'px-1');
        label.dataset.path = itemData.path;
        label.title = itemData.path;

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.classList.add('tree-checkbox', 'form-checkbox', 'h-3.5', 'w-3.5', 'text-blue-600', 'border-gray-300', 'rounded', 'mr-2', 'flex-shrink-0', 'focus:ring-blue-500', 'dark:bg-gray-700', 'dark:border-gray-600');
        checkbox.disabled = !itemData.can_be_checked;
        if (itemData.tooltip) checkbox.title = itemData.tooltip;

        if (clientState.checkedTreePathsAbs.has(itemData.path)) checkbox.checked = true;

        checkbox.addEventListener('change', (event) => {
            const path = event.target.closest('label').dataset.path;
            const isChecked = event.target.checked;
            updateCheckedState(path, isChecked, li);
            saveStateToLocalStorage();
            updateFileTreeDependentUIs();
        });

        const iconSpan = document.createElement('span');
        iconSpan.classList.add('icon', 'mr-1.5', 'flex-shrink-0');
        let toggleIconElement = null;
        let childrenUl = null; 

        const nameSpan = document.createElement('span');
        nameSpan.textContent = itemData.name + (itemData.is_dir ? '/' : '');
        nameSpan.classList.add('truncate');

        if (itemData.is_dir) {
            iconSpan.innerHTML = '📁';
            if (itemData.children && itemData.children.length > 0) {
                li.classList.add('has-children');
                toggleIconElement = document.createElement('span');
                toggleIconElement.innerHTML = '▶️'; 
                toggleIconElement.classList.add('toggle-icon', 'mr-1', 'cursor-pointer', 'text-xs', 'select-none', 'flex-shrink-0');

                childrenUl = document.createElement('ul');
                childrenUl.classList.add('list-none', 'p-0', 'm-0', 'ml-4', 'hidden'); 
                // DEBUG: Add a border to see if nested ULs are created and where
                // childrenUl.style.border = "1px dashed red"; 


                toggleIconElement.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isHidden = childrenUl.classList.toggle('hidden');
                    toggleIconElement.innerHTML = isHidden ? '▶️' : '🔽';
                });

                nameSpan.classList.add('cursor-pointer');
                nameSpan.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (toggleIconElement) {
                        toggleIconElement.click();
                    }
                });
            }
        } else if (itemData.is_text) {
            iconSpan.innerHTML = '📄';
        } else {
            iconSpan.innerHTML = '▫️';
        }

        if (!itemData.can_be_checked) {
            label.classList.add('opacity-60', 'cursor-not-allowed');
            nameSpan.classList.add('text-gray-500', 'dark:text-gray-400');
        }

        if (toggleIconElement) labelContainer.appendChild(toggleIconElement);
        label.appendChild(checkbox);
        label.appendChild(iconSpan);
        label.appendChild(nameSpan);
        labelContainer.appendChild(label);
        li.appendChild(labelContainer); 

        if (itemData.is_dir && itemData.children && itemData.children.length > 0 && childrenUl) {
            renderTree(itemData.children, childrenUl, false); 
            li.appendChild(childrenUl); 
        }

        parentDomElementToAppendLi.appendChild(li); 
    });
}

function updateCheckedState(path, isChecked, listItemElement) {
    if (isChecked) {
        clientState.checkedTreePathsAbs.add(path);
    } else {
        clientState.checkedTreePathsAbs.delete(path);
    }

    // If it's a directory, propagate check state to its children in the DOM
    const isDir = listItemElement.querySelector('.icon').textContent === '📁';
    if (isDir) {
        const childCheckboxes = listItemElement.querySelectorAll('ul > li > div > label > .tree-checkbox:not(:disabled)');
        childCheckboxes.forEach(cb => {
            if (cb.checked !== isChecked) {
                cb.checked = isChecked;
                const childPath = cb.closest('label').dataset.path;
                if (isChecked) clientState.checkedTreePathsAbs.add(childPath);
                else clientState.checkedTreePathsAbs.delete(childPath);
            }
        });
    }
}

// In performLoadTree function:
async function performLoadTree() {
    const folderPath = folderPathInput.value.trim();
    if (!folderPath) { showStatus('Please enter a folder path first.', 'warning'); return; }
    
    clientState.checkedTreePathsAbs.clear();
    clientState.loadedDocPaths = []; 
    updateDocListUI();
    rawOutputTextarea.value = "";
    renderedOutputDiv.innerHTML = "Preview here.";
    copyRawBtn.disabled = true;
    tabButtons[2].disabled = true;

    showLoading(loadTreeBtn, true, 'Loading Tree...', 'Load Project Tree');
    showLoading(refreshTreeBtn, true, 'Refreshing...', 'Refresh');
    showStatus('Loading project tree...', 'info');
    fileTreeContainer.innerHTML = '<p class="p-4 text-gray-500 dark:text-gray-400">Loading tree structure...</p>';

    try {
        const response = await fetch('/api/load_project_tree', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: folderPath, filters: clientState.filterSettings })
        });
        const data = await handleResponse(response);
        fileTreeContainer.innerHTML = ''; // Clear "Loading tree..."

        // Debug: Log the received data structure
        // console.log("Received tree data from backend:", JSON.stringify(data.tree, null, 2));

        if (data.tree && data.tree.length > 0 && data.tree[0]) {
            const rootObjectFromBackend = data.tree[0];
            const topLevelItemsToRender = rootObjectFromBackend.children || [];

            const rootUl = document.createElement('ul');
            rootUl.classList.add('list-none', 'p-0', 'm-0');
            fileTreeContainer.appendChild(rootUl);

            if (topLevelItemsToRender.length > 0) {
                renderTree(topLevelItemsToRender, rootUl, true); // Pass children of the root
            } else {
                // If the root folder itself is empty but we want to show its name
                // This part is optional, current behavior will show an empty tree which is fine
                // fileTreeContainer.innerHTML = `<p class="p-4 text-gray-500 dark:text-gray-400">Folder '${rootObjectFromBackend.name || 'root'}' is empty or all items are filtered.</p>`;
                 const emptyMsgLi = document.createElement('li');
                 emptyMsgLi.textContent = `Folder "${rootObjectFromBackend.name || 'Project Root'}" is empty or all items filtered.`;
                 emptyMsgLi.classList.add('text-gray-500','dark:text-gray-400', 'p-1', 'italic');
                 rootUl.appendChild(emptyMsgLi);

            }
            
            showStatus(`Project tree for "${rootObjectFromBackend.name || folderPath}" loaded.`, 'success');
            preselectFilesFromFirstTemplate();
            tabButtons[1].disabled = false;
            activateTab('tab2');
        } else {
            fileTreeContainer.innerHTML = '<p class="p-4 text-gray-500 dark:text-gray-400">No items found based on current filters or folder is empty/inaccessible.</p>';
            showStatus('No items found or folder is empty/inaccessible based on filters.', 'warning');
            tabButtons[1].disabled = false; // Still enable, just show empty state
        }
    } catch (error) {
        console.error('Error loading tree:', error);
        fileTreeContainer.innerHTML = `<p class="p-4 text-red-600 dark:text-red-400">Error loading tree: ${error.message}.<br>Check folder path and server logs.</p>`;
        tabButtons[1].disabled = true;
    } finally {
        showLoading(loadTreeBtn, false, null, 'Load Project Tree');
        showLoading(refreshTreeBtn, false, null, 'Refresh');
        updateClientStateFromUI();
    }
}

loadTreeBtn.addEventListener('click', performLoadTree);
refreshTreeBtn.addEventListener('click', performLoadTree);

browseServerFolderBtn.addEventListener('click', async () => {
    showLoading(browseServerFolderBtn, true, 'Browsing...', 'Browse Server Folder (Server-Side)');
    showStatus('Opening folder dialog on the server...', 'info');
    try {
        const response = await fetch('/api/browse_server_folder', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
        const data = await handleResponse(response);
        if (data.status === 'success' && data.path) {
            folderPathInput.value = data.path;
            updateClientStateFromUI(); // This will save folderPath
            showStatus(`Server-side dialog returned: ${data.path}. Click 'Load Project Tree' to load it.`, 'success');
            // Optionally, trigger loadTree directly:
            // performLoadTree(); 
        } else if (data.status === 'cancelled') {
            showStatus('Server-side folder selection was cancelled.', 'info');
        } else {
            showStatus(`Unexpected response from server browse: ${JSON.stringify(data)}`, 'error');
        }
    } catch (error) {
        console.error('Error browsing server folder:', error);
        showStatus(`Failed to browse server folder: ${error.message}. Check server logs.`, 'error');
    } finally {
        showLoading(browseServerFolderBtn, false, null, 'Browse Server Folder (Server-Side)');
    }
});

function expandCollapseTree(expand, element = fileTreeContainer) {
    const toggleIcons = element.querySelectorAll('li.has-children > div > span.toggle-icon');
    toggleIcons.forEach(toggle => {
        const childUl = toggle.closest('li').querySelector('ul');
        if (childUl) {
            const isCurrentlyHidden = childUl.classList.contains('hidden');
            if (expand && isCurrentlyHidden) { // If we want to expand AND it's hidden
                toggle.click(); // Simulate click to expand
            } else if (!expand && !isCurrentlyHidden) { // If we want to collapse AND it's visible
                toggle.click(); // Simulate click to collapse
            }
        }
    });
     // If expanding, ensure all children that become visible are also processed.
    if (expand) {
        setTimeout(() => { // Allow DOM to update from clicks
            element.querySelectorAll('li.has-children > ul:not(.hidden)').forEach(visibleChildUl => {
                expandCollapseTree(expand, visibleChildUl);
            });
        }, 50); // Small delay
    }
}
expandAllBtn.addEventListener('click', () => expandCollapseTree(true));
collapseAllBtn.addEventListener('click', () => expandCollapseTree(false));

checkAllTextBtn.addEventListener('click', () => {
    showStatus('Checking all checkable items in tree...', 'info');
    clientState.checkedTreePathsAbs.clear(); // Start fresh
    fileTreeContainer.querySelectorAll('li').forEach(li => {
        const checkbox = li.querySelector('.tree-checkbox');
        if (checkbox && !checkbox.disabled) {
            checkbox.checked = true;
            const path = checkbox.closest('label').dataset.path;
            clientState.checkedTreePathsAbs.add(path);
        }
    });
    saveStateToLocalStorage();
    updateFileTreeDependentUIs();
    showStatus('All checkable items are now checked.', 'success');
});
uncheckAllBtn.addEventListener('click', () => {
    showStatus('Unchecking all items in tree...', 'info');
    clientState.checkedTreePathsAbs.clear();
    fileTreeContainer.querySelectorAll('.tree-checkbox:not(:disabled)').forEach(cb => cb.checked = false);
    saveStateToLocalStorage();
    updateFileTreeDependentUIs();
    showStatus('All items unchecked.', 'success');
});
// This function is not strictly needed if state is managed well, but can be a fallback
function applyCheckedPathsToTree() {
    fileTreeContainer.querySelectorAll('.tree-checkbox').forEach(cb => {
        const path = cb.closest('label').dataset.path;
        cb.checked = clientState.checkedTreePathsAbs.has(path);
    });
}

// --- Prompt Templates ---
async function fetchPromptTemplates() {
    try {
        const response = await fetch('/api/prompt_templates');
        const data = await handleResponse(response);
        clientState.promptTemplates = data.map(t => ({ name: t.name, content: t.content }));
        populateTemplateSelect();
    } catch (error) { console.error('Error fetching prompt templates:', error); showStatus('Failed to load prompt templates.', 'error'); }
}
function populateTemplateSelect() {
    templateSelect.innerHTML = '<option value="">-- Select Template --</option>';
    clientState.promptTemplates.forEach(t => {
        const option = document.createElement('option');
        option.value = t.name;
        option.textContent = t.name;
        templateSelect.appendChild(option);
    });
    // Try to re-select current template if its content matches
    const currentPromptContent = customPromptTextarea.value.trim();
    if (currentPromptContent) {
        const foundTemplate = clientState.promptTemplates.find(t => t.content.trim() === currentPromptContent);
        if (foundTemplate) {
            templateSelect.value = foundTemplate.name;
        }
    }
}
loadTemplateBtn.addEventListener('click', () => {
    const selectedName = templateSelect.value;
    if (!selectedName) { showStatus('No template selected.', 'warning'); return; }
    const template = clientState.promptTemplates.find(t => t.name === selectedName);
    if (template) {
        let content = template.content;
        // Apply placeholders (basic client-side, server does more thorough job if needed for generation)
        const folderName = clientState.folderPath ? clientState.folderPath.split(/[\/\\]/).pop() : 'UnknownProject';
        content = content.replace(/{FOLDER_NAME}/g, folderName);
        content = content.replace(/{FOLDER_PATH}/g, clientState.folderPath || 'N/A');
        content = content.replace(/{DATE}/g, new Date().toISOString().slice(0, 10));
        content = content.replace(/{TIME}/g, new Date().toLocaleTimeString());
        content = content.replace(/{DATETIME}/g, new Date().toLocaleString());
        content = content.replace(/{AUTHOR}/g, 'User'); // Client-side might not know server username
        content = content.replace(/{USER_REQUEST}/g, '[Your specific request here]');
        
        customPromptTextarea.value = content;
        updateClientStateFromUI(); // Save the new prompt to state
        showStatus(`Loaded template: ${selectedName}`, 'success');
    } else {
        showStatus(`Template '${selectedName}' not found.`, 'error');
    }
});
saveTemplateBtn.addEventListener('click', async () => {
    const content = customPromptTextarea.value.trim();
    if (!content) { showStatus('Prompt content is empty. Cannot save empty template.', 'warning'); return; }
    let name = prompt('Enter a name for this template:');
    if (!name) return; // User cancelled
    name = name.trim();
    if (!name) { alert('Template name cannot be empty.'); return; }

    const existingTemplate = clientState.promptTemplates.find(t => t.name === name);
    if (existingTemplate && existingTemplate.content !== content) {
        if (!confirm(`A template named '${name}' already exists with different content. Overwrite it?`)) return;
    } else if (existingTemplate && existingTemplate.content === content) {
        showStatus(`Template '${name}' with the same content already exists.`, 'info');
        templateSelect.value = name; // Ensure it's selected
        return;
    }

    try {
        const response = await fetch('/api/save_template', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, content })
        });
        const data = await handleResponse(response);
        showStatus(data.message || `Template '${name}' saved successfully.`, data.status === 'success' || data.status === 'reverted_to_default' ? 'success' : 'warning');
        await fetchPromptTemplates(); // Refresh list
        templateSelect.value = name; // Select the newly saved/updated template
        updateClientStateFromUI();
    } catch (error) {
        console.error('Error saving template:', error);
        showStatus(`Failed to save template: ${error.message}`, 'error');
    }
});
manageTemplateBtn.addEventListener('click', async () => {
    const action = prompt("Manage Templates:\n1. Delete a template\n2. Copy a template\n\nEnter action number (1 or 2):");
    if (!action) return;

    if (action === '1') {
        const nameToDelete = prompt("Enter the exact name of the template to delete:");
        if (!nameToDelete) return;
        const templateToDelete = clientState.promptTemplates.find(t => t.name === nameToDelete);
        if (!templateToDelete) { showStatus(`Template '${nameToDelete}' not found.`, 'warning'); return; }
        if (!confirm(`Are you sure you want to delete/revert the template '${nameToDelete}'?`)) return;
        try {
            const response = await fetch('/api/delete_template', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // Send full template data as backend might expect it for certain checks
                body: JSON.stringify({ name: templateToDelete.name, content: templateToDelete.content })
            });
            const data = await handleResponse(response);
            showStatus(data.message || `Template '${nameToDelete}' processed.`, data.status.startsWith('success') || data.status.startsWith('reverted') ? 'success' : 'warning');
            await fetchPromptTemplates(); // Refresh list
            if (customPromptTextarea.value === templateToDelete.content) { // If deleted template was active
                customPromptTextarea.value = "";
                updateClientStateFromUI();
            }
        } catch (error) {
            console.error('Error deleting template:', error);
            showStatus(`Failed to delete template: ${error.message}`, 'error');
        }
    } else if (action === '2') {
        const nameToCopy = prompt("Enter the exact name of the template to copy:");
        if (!nameToCopy) return;
        const originalTemplate = clientState.promptTemplates.find(t => t.name === nameToCopy);
        if (!originalTemplate) { showStatus(`Template '${nameToCopy}' not found.`, 'warning'); return; }
        
        let newName = `${originalTemplate.name} (Copy)`;
        let count = 1;
        while (clientState.promptTemplates.some(t => t.name === newName)) {
            newName = `${originalTemplate.name} (Copy ${++count})`;
        }
        if (!confirm(`Copy template '${nameToCopy}' as '${newName}'?`)) return;
        try {
            const response = await fetch('/api/save_template', { // Use save endpoint for copying
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName, content: originalTemplate.content })
            });
            const data = await handleResponse(response);
            showStatus(data.message || `Template copied as '${newName}'.`, 'success');
            await fetchPromptTemplates();
            templateSelect.value = newName; // Select the new copy
            customPromptTextarea.value = originalTemplate.content; // Load its content
            updateClientStateFromUI();
        } catch (error) {
            console.error('Error copying template:', error);
            showStatus(`Failed to copy template: ${error.message}`, 'error');
        }
    } else {
        showStatus('Invalid action selected.', 'warning');
    }
});


// --- Generation and Output ---
generateBtn.addEventListener('click', async () => {
    const currentFolderPath = clientState.folderPath; // Use state for consistency
    if (!currentFolderPath) { showStatus('Folder path is missing. Please set it on Tab 1.', 'warning'); activateTab('tab1'); return; }
    if (!fileTreeContainer.children.length || !fileTreeContainer.querySelector('ul')) { showStatus('Project tree not loaded or empty. Load it on Tab 1 or 2.', 'warning'); activateTab('tab1'); return; }
    if (clientState.checkedTreePathsAbs.size === 0) { showStatus('No files or folders selected in the Project Explorer (Tab 2).', 'warning'); activateTab('tab2'); return; }

    showLoading(generateBtn, true, 'Generating...', 'Generate Structure Text');
    rawOutputTextarea.value = 'Generating structure and content... Please wait.';
    renderedOutputDiv.innerHTML = '<p class="p-4 text-gray-500 dark:text-gray-400">Generating... Please wait.</p>';
    copyRawBtn.disabled = true;
    tabButtons[2].disabled = false; // Enable output tab
    activateTab('tab3');
    // activateSubTab('raw-output'); // Ensure raw output is visible initially

    updateClientStateFromUI(); // Ensure latest settings are used

    try {
        const response = await fetch('/api/generate_structure', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                folder_path: currentFolderPath,
                filters: clientState.filterSettings,
                selected_paths_abs: Array.from(clientState.checkedTreePathsAbs),
                custom_prompt: clientState.customPrompt,
                loaded_doc_paths: clientState.loadedDocPaths
            })
        });
        const data = await handleResponse(response);
        rawOutputTextarea.value = data.markdown;
        if (typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') {
            renderedOutputDiv.innerHTML = DOMPurify.sanitize(marked.parse(data.markdown));
        } else {
            renderedOutputDiv.innerHTML = '<p class="text-red-500">Error: Markdown parser or sanitizer not loaded.</p>';
            console.error("marked.js or DOMPurify not loaded for rendering.");
        }
        copyRawBtn.disabled = false;

        if (clientState.saveOutputChecked) {
            const projName = currentFolderPath.split(/[\/\\]/).pop() || 'project_output';
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T-]/g, '');
            const filename = `folder_structure_${projName}_${timestamp}.md`;
            const blob = new Blob([data.markdown], { type: 'text/markdown;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showStatus('Output generated and download initiated.', 'success');
        } else {
            showStatus('Output generated successfully. View on Tab 3.', 'success');
        }
    } catch (error) {
        console.error('Error generating structure text:', error);
        const errorMsg = `Error generating output: ${error.message}`;
        rawOutputTextarea.value = `\`\`\`error\n${errorMsg}\nCheck console for details.\n\`\`\``;
        renderedOutputDiv.innerHTML = `<p class="p-4 text-red-600 dark:text-red-400">${errorMsg}</p>`;
        showStatus(`Generation failed: ${error.message}`, 'error');
    } finally {
        showLoading(generateBtn, false, null, 'Generate Structure Text');
    }
});

copyRawBtn.addEventListener('click', () => {
    if (rawOutputTextarea.value) {
        navigator.clipboard.writeText(rawOutputTextarea.value)
            .then(() => showStatus('Raw Markdown copied to clipboard.', 'success'))
            .catch(err => {
                console.error('Failed to copy raw output:', err);
                showStatus('Failed to copy. Check browser permissions or console.', 'error');
            });
    } else {
        showStatus('Nothing to copy from raw output.', 'warning');
    }
});
clearOutputBtn.addEventListener('click', () => {
    rawOutputTextarea.value = '';
    renderedOutputDiv.innerHTML = 'Preview here.';
    copyRawBtn.disabled = true;
    showStatus('Output cleared.');
});
themeToggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    clientState.currentTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    themeToggle.innerHTML = clientState.currentTheme === 'dark' ? '☀️' : '🌙';
    showStatus(`Theme switched to ${clientState.currentTheme}.`);
    saveStateToLocalStorage();
});

// --- Pre-selection Logic ---
function globToRegex(glob) {
    // More robust glob to regex:
    // - Escape regex special chars
    // - Convert * to .*
    // - Convert ? to .
    // - Handle ** for multiple directory levels
    // - Anchor to start and end
    let regex = glob.replace(/([.?+^$[\]\\(){}|-])/g, "\\$1"); // Escape special chars
    regex = regex.replace(/\*\*/g, "(.*/)?([^/]+)"); // ** matches zero or more dirs
    regex = regex.replace(/\*/g, "[^/]*");   // * matches anything except slash
    regex = regex.replace(/\?/g, "[^/]");    // ? matches any char except slash
    return new RegExp('^' + regex + '$');
}

function preselectFilesFromFirstTemplate() {
    if (clientState.promptTemplates.length === 0 || !clientState.promptTemplates[0]) {
        showStatus("No templates available for pre-selection.", "info");
        return;
    }
    const firstTemplateContent = clientState.promptTemplates[0].content;
    const patternMatch = firstTemplateContent.match(/<!--\s*PRESELECT_PATTERNS:\s*([^->]+)\s*-->/i);

    if (!patternMatch || !patternMatch[1]) {
        showStatus("No pre-selection patterns found in the first template (<!-- PRESELECT_PATTERNS: ... -->).", "info");
        return;
    }

    const patterns = patternMatch[1].split(',').map(p => p.trim()).filter(p => p);
    if (patterns.length === 0) {
        showStatus("No valid pre-selection patterns extracted from the first template.", "info");
        return;
    }
    showStatus(`Attempting pre-selection with patterns: ${patterns.join(', ')}`, "info");

    let preselectedCount = 0;
    const rootFolderPath = clientState.folderPath; // From state
    if (!rootFolderPath) {
        showStatus("Cannot pre-select: Folder path not set.", "warning");
        return;
    }
    const resolvedRootPath = rootFolderPath.endsWith('/') || rootFolderPath.endsWith('\\') ? rootFolderPath : rootFolderPath + '/';

    fileTreeContainer.querySelectorAll('li').forEach(liItem => {
        const checkbox = liItem.querySelector('.tree-checkbox:not(:disabled)');
        if (!checkbox) return;

        const label = checkbox.closest('label');
        const fullPath = label.dataset.path; // Absolute path from tree data
        
        // Calculate path relative to the project root for matching
        let relativePath = fullPath;
        if (fullPath.startsWith(resolvedRootPath)) {
            relativePath = fullPath.substring(resolvedRootPath.length);
        } else if (fullPath.startsWith(rootFolderPath)) { // Handle if root path didn't have trailing slash initially
             relativePath = fullPath.substring(rootFolderPath.length).replace(/^[\/\\]+/, '');
        }
        
        const nameOnly = fullPath.split(/[\/\\]/).pop();

        for (const globPattern of patterns) {
            try {
                const regexPattern = globToRegex(globPattern);
                if (regexPattern.test(relativePath) || regexPattern.test(nameOnly)) {
                    if (!checkbox.checked) { // Only check if not already checked (e.g. by user)
                        checkbox.checked = true;
                        updateCheckedState(fullPath, true, liItem); // Use helper to update state
                        preselectedCount++;
                    }
                    break; // Move to next file if matched by one pattern
                }
            } catch (e) {
                console.warn(`Invalid glob pattern for pre-selection: '${globPattern}'`, e);
                showStatus(`Warning: Invalid pre-selection pattern: ${globPattern}`, 'warning');
                patterns.splice(patterns.indexOf(globPattern), 1); // Remove invalid pattern for future iterations
            }
        }
    });

    if (preselectedCount > 0) {
        saveStateToLocalStorage(); // Save the new selections
        updateFileTreeDependentUIs();
        showStatus(`Pre-selected ${preselectedCount} items based on first template patterns.`, "success");
    } else {
        showStatus("No new items matched pre-selection patterns.", "info");
    }
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    populatePresetList(); // Dynamic presets
    loadStateFromLocalStorage(); // Load saved state, then apply to UI
    fetchPromptTemplates(); // Fetch and populate templates
    
    // Initial UI state based on loaded/default clientState
    updateFileTreeDependentUIs(); // Set initial disabled states for buttons
    
    // Set initial active tabs (Tab 1, Raw Output)
    activateTab('tab1');
    activateSubTab('raw-output'); // Default to raw output

    showStatus('Application ready. Enter project folder and load tree, or load saved settings.', 'info');
});