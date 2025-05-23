// Function to update status message
function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('status-message');
    statusDiv.textContent = message;
    statusDiv.className = 'text-sm'; // Reset classes
    if (type === 'error') {
        statusDiv.classList.add('text-red-600', 'dark:text-red-400');
    } else if (type === 'warning') {
        statusDiv.classList.add('text-yellow-600', 'dark:text-yellow-400');
    } else {
        statusDiv.classList.add('text-green-600', 'dark:text-green-400');
    }
    console.log(`STATUS (${type.toUpperCase()}): ${message}`);
}

function showLoading(element, isLoading, originalText = null) {
    if (isLoading) {
        element.disabled = true;
        element.classList.add('opacity-50', 'cursor-not-allowed');
        if (originalText !== null) element.dataset.originalText = originalText;
        else if (!element.dataset.originalText) element.dataset.originalText = element.textContent;
        element.textContent = 'Loading...';
    } else {
        element.disabled = false;
        element.classList.remove('opacity-50', 'cursor-not-allowed');
        if (element.dataset.originalText) {
             element.textContent = element.dataset.originalText;
             delete element.dataset.originalText;
        }
    }
}

async function handleResponse(response) {
    if (!response.ok) {
        let errorData;
        try { errorData = await response.json(); } catch (e) {
            errorData = { detail: await response.text() || `HTTP error! status: ${response.status}` };
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
        button.classList.toggle('active', button.id === `${tabId}-btn`);
        button.classList.toggle('bg-white', button.id === `${tabId}-btn`);
        button.classList.toggle('dark:bg-gray-700', button.id === `${tabId}-btn`);
        button.classList.toggle('text-blue-600', button.id === `${tabId}-btn`);
        button.classList.toggle('dark:text-blue-400', button.id === `${tabId}-btn`);
        button.classList.toggle('bg-gray-200', button.id !== `${tabId}-btn`);
        button.classList.toggle('dark:bg-gray-900', button.id !== `${tabId}-btn`);
    });
    tabContents.forEach(content => content.classList.toggle('active', content.id === `${tabId}-content`));
}
tabButtons.forEach(button => button.addEventListener('click', () => activateTab(button.id.replace('-btn', ''))));

const subTabButtons = document.querySelectorAll('.sub-tab-button');
const subTabContents = document.querySelectorAll('.sub-tab-content');
function activateSubTab(tabId) {
    subTabButtons.forEach(button => {
        if (button.id === `${tabId}-btn`) {
            button.classList.add('active', 'bg-white', 'dark:bg-gray-700', 'text-blue-600', 'dark:text-blue-400');
            button.classList.remove('bg-gray-200', 'dark:bg-gray-900', 'text-gray-900', 'dark:text-gray-100');
        } else {
            button.classList.remove('active', 'bg-white', 'dark:bg-gray-700', 'text-blue-600', 'dark:text-blue-400');
            button.classList.add('bg-gray-200', 'dark:bg-gray-900', 'text-gray-900', 'dark:text-gray-100');
        }
    });

    subTabContents.forEach(content => {
        if (content.id === `${tabId}-content`) {
            // content.classList.remove('hidden'); // THIS WAS THE LINE IN THE ORIGINAL CODE
            content.style.display = 'flex'; // Or 'block' if flex is not needed for direct children
        } else {
            // content.classList.add('hidden'); // THIS WAS THE LINE
            content.style.display = 'none';
        }
    });
}
subTabButtons.forEach(button => button.addEventListener('click', () => activateSubTab(button.id.replace('-btn', ''))));

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

const clientState = {
    folderPath: '',
    filterSettings: {
        selected_presets: [], custom_folders: '', custom_extensions: '', custom_patterns: '',
        dynamic_patterns: '', custom_inclusions: '', max_file_size_mb: 1.0,
    },
    saveOutputChecked: false, customPrompt: '', loadedDocPaths: [],
    checkedTreePathsAbs: new Set(), promptTemplates: [], currentTheme: 'light',
};

function saveStateToLocalStorage() {
    localStorage.setItem('folderExtractorState', JSON.stringify(clientState, (key, value) => {
        return (key === 'checkedTreePathsAbs' && value instanceof Set) ? Array.from(value) : value;
    }));
}
function loadStateFromLocalStorage() {
    const savedState = localStorage.getItem('folderExtractorState');
    if (savedState) {
        try {
            const parsedState = JSON.parse(savedState);
            Object.assign(clientState, parsedState);
            clientState.checkedTreePathsAbs = new Set(Array.isArray(clientState.checkedTreePathsAbs) ? clientState.checkedTreePathsAbs : []);
            applyStateToUI();
            showStatus('Loaded settings from local storage.');
        } catch (e) {
            console.error('Failed to parse state from local storage:', e);
            resetClientState(); applyStateToUI(); showStatus('Failed to load saved settings. Using defaults.', 'error');
        }
    } else {
        resetClientState(); applyStateToUI(); showStatus('No saved settings found. Using defaults.');
    }
}
function resetClientState() {
    clientState.folderPath = '';
    clientState.filterSettings = {
        selected_presets: [], custom_folders: '', custom_extensions: '', custom_patterns: '',
        dynamic_patterns: '', custom_inclusions: '', max_file_size_mb: 1.0,
    };
    clientState.saveOutputChecked = false; clientState.customPrompt = '';
    clientState.loadedDocPaths = []; clientState.checkedTreePathsAbs = new Set();
    clientState.currentTheme = 'light'; saveStateToLocalStorage();
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
    updateDocListUI();
    document.documentElement.classList.toggle('dark', clientState.currentTheme === 'dark');
    tabButtons[1].disabled = !clientState.folderPath; tabButtons[2].disabled = true;
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
    saveStateToLocalStorage();
}
folderPathInput.addEventListener('change', updateClientStateFromUI);
[customFoldersInput, customExtensionsInput, customPatternsInput, dynamicExcludeInput, customInclusionsInput, maxFileSizeInput].forEach(input => input.addEventListener('input', updateClientStateFromUI));
saveOutputCheckbox.addEventListener('change', updateClientStateFromUI);
customPromptTextarea.addEventListener('input', updateClientStateFromUI);
presetList.addEventListener('change', e => e.target.classList.contains('preset-checkbox') && updateClientStateFromUI());

const presetOptions = ["Python Project", "Node.js Project", "C/C++ Project", "Rust Project", "Java Project"];
function populatePresetList() {
    presetList.innerHTML = '';
    presetOptions.forEach(name => {
        const id = `preset-${name.replace(/\s+/g, '-')}`;
        const cb = `<input type="checkbox" id="${id}" value="${name}" class="preset-checkbox form-checkbox h-4 w-4 text-blue-600 rounded focus:ring-blue-500">`;
        const lbl = `<label for="${id}" class="ml-1 mr-2 text-sm">${name}</label>`;
        const div = document.createElement('div');
        div.classList.add('flex', 'items-center', 'py-1', 'px-2', 'rounded-md', 'bg-gray-100', 'dark:bg-gray-700', 'cursor-pointer', 'hover:bg-gray-200', 'dark:hover:bg-gray-600');
        div.innerHTML = cb + lbl;
        div.addEventListener('click', e => { if (e.target !== div.firstChild) { div.firstChild.checked = !div.firstChild.checked; div.firstChild.dispatchEvent(new Event('change')); }});
        presetList.appendChild(div);
    });
}
function updateDocListUI() {
    docList.innerHTML = '';
    clientState.loadedDocPaths.forEach(path => {
        const li = document.createElement('li');
        li.classList.add('flex', 'items-center', 'justify-between', 'py-1', 'px-2', 'border-b', 'border-gray-200', 'dark:border-gray-700', 'last:border-b-0', 'hover:bg-gray-100', 'dark:hover:bg-gray-700', 'cursor-pointer');
        li.dataset.path = path;
        const fileName = path.split(/[\/\\]/).pop(), parentDir = path.split(/[\/\\]/).slice(-2, -1)[0] || '';
        li.innerHTML = `<span class="truncate" title="${path}">${fileName} (${parentDir})</span><input type="checkbox" class="doc-checkbox h-4 w-4 text-blue-600 rounded ml-2">`;
        li.addEventListener('click', e => { if (e.target !== li.lastChild) li.lastChild.checked = !li.lastChild.checked; });
        docList.appendChild(li);
    });
    saveStateToLocalStorage();
}
addDocsBtn.addEventListener('click', () => addDocsInput.click());
addDocsInput.addEventListener('change', async e => {
    let added = 0;
    for (const file of e.target.files) {
        const p = file.path || file.name;
        if (!clientState.loadedDocPaths.includes(p)) { clientState.loadedDocPaths.push(p); added++; }
        else showStatus(`Doc file already added: ${file.name}`, 'warning');
    }
    if (added) { updateDocListUI(); showStatus(`Added ${added} doc file(s).`); }
    addDocsInput.value = '';
});
removeDocsBtn.addEventListener('click', () => {
    const sel = Array.from(docList.querySelectorAll('.doc-checkbox:checked')).map(cb => cb.parentElement.dataset.path);
    if (!sel.length) { showStatus('Select docs to remove.', 'warning'); return; }
    clientState.loadedDocPaths = clientState.loadedDocPaths.filter(p => !sel.includes(p));
    updateDocListUI(); showStatus(`Removed ${sel.length} doc file(s).`);
});
clearDocsBtn.addEventListener('click', () => {
    if (!clientState.loadedDocPaths.length) { showStatus('Doc list is empty.', 'info'); return; }
    if (confirm('Remove all loaded docs?')) { clientState.loadedDocPaths = []; updateDocListUI(); showStatus('Cleared all docs.'); }
});

// --- Project Tree (File Explorer) - MODIFIED for Collapsible ---
function renderTree(node, parentElement, isRoot = true) {
    const ul = document.createElement('ul');
    ul.classList.add('list-none', 'p-0', 'm-0');
    if (!isRoot) ul.classList.add('ml-4', 'hidden'); // Nested lists are hidden by default

    node.children.sort((a, b) => {
        if (a.is_dir && !b.is_dir) return -1;
        if (!a.is_dir && b.is_dir) return 1;
        return a.name.localeCompare(b.name);
    });

    node.children.forEach(child => {
        const li = document.createElement('li');
        li.classList.add('flex', 'flex-col');
        
        const labelContainer = document.createElement('div'); // Container for label and toggle icon
        labelContainer.classList.add('flex', 'items-center', 'py-1');

        const label = document.createElement('label');
        label.classList.add('flex', 'items-center', 'cursor-pointer', 'flex-grow');
        label.dataset.path = child.path;

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.classList.add('tree-checkbox', 'h-4', 'w-4', 'text-blue-600', 'rounded', 'mr-2', 'flex-shrink-0');
        checkbox.disabled = !child.can_be_checked;
        if (clientState.checkedTreePathsAbs.has(child.path)) checkbox.checked = true;

        checkbox.addEventListener('change', (event) => {
            const path = event.target.closest('label').dataset.path;
            const isChecked = event.target.checked;
            if (isChecked) clientState.checkedTreePathsAbs.add(path);
            else clientState.checkedTreePathsAbs.delete(path);
            saveStateToLocalStorage();
            if (child.is_dir) {
                // Iterate over direct children checkboxes in the DOM
                const childCheckboxes = li.querySelector('ul > li > div > label > .tree-checkbox:not(:disabled)'); // More specific
                if (childCheckboxes) { // If children are rendered
                    li.querySelectorAll('ul > li > div > label > .tree-checkbox:not(:disabled)').forEach(cb => {
                         if (cb.checked !== isChecked) {
                            cb.checked = isChecked;
                            const childPath = cb.closest('label').dataset.path;
                            if (isChecked) clientState.checkedTreePathsAbs.add(childPath);
                            else clientState.checkedTreePathsAbs.delete(childPath);
                        }
                    });
                }
            }
        });

        const iconSpan = document.createElement('span');
        iconSpan.classList.add('icon', 'mr-1');
        let toggleIcon = null;

        if (child.is_dir) {
            iconSpan.innerHTML = '📁';
            if (child.children && child.children.length > 0) {
                toggleIcon = document.createElement('span');
                toggleIcon.innerHTML = '▶️'; // Collapsed by default
                toggleIcon.classList.add('mr-1', 'cursor-pointer', 'text-xs');
                toggleIcon.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent label click
                    const childUl = li.querySelector('ul');
                    if (childUl) {
                        const isHidden = childUl.classList.toggle('hidden');
                        toggleIcon.innerHTML = isHidden ? '▶️' : '🔽';
                    }
                });
            }
        } else if (child.is_text) {
            iconSpan.innerHTML = '📄';
        } else {
            iconSpan.innerHTML = '🗃️';
        }

        const nameSpan = document.createElement('span');
        nameSpan.textContent = child.name + (child.is_dir ? '/' : '');
        nameSpan.classList.add('flex-grow');
        if (child.is_dir && toggleIcon) { // Make folder name also clickable to toggle
            nameSpan.classList.add('cursor-pointer');
            nameSpan.addEventListener('click', () => toggleIcon.click());
        }


        if (toggleIcon) labelContainer.appendChild(toggleIcon);
        label.appendChild(checkbox);
        label.appendChild(iconSpan);
        label.appendChild(nameSpan);
        labelContainer.appendChild(label);
        li.appendChild(labelContainer);

        if (child.is_dir && child.children.length > 0) {
            const childUl = renderTree(child, ul, false); // isRoot = false for children
            li.appendChild(childUl);
            li.classList.add('has-children');
        }
        if (!child.can_be_checked) li.classList.add('disabled');
        ul.appendChild(li);
    });
    parentElement.appendChild(ul);
    return ul;
}

async function performLoadTree() {
    const folderPath = folderPathInput.value.trim();
    if (!folderPath) { showStatus('Please enter a folder path first.', 'warning'); return; }
    
    showLoading(loadTreeBtn, true, 'Load Project Tree');
    showStatus('Loading project tree...', 'info');
    fileTreeContainer.innerHTML = 'Loading tree...';

    try {
        const response = await fetch('/api/load_project_tree', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: folderPath, filters: clientState.filterSettings })
        });
        const data = await handleResponse(response);
        fileTreeContainer.innerHTML = '';
        if (data.tree && data.tree.length > 0) {
            renderTree({ children: data.tree }, fileTreeContainer, true);
            showStatus('Project tree loaded successfully.');
            applyCheckedPathsToTree(); // Re-apply existing checks
            preselectFilesFromFirstTemplate(); // Attempt pre-selection
            tabButtons[1].disabled = false; activateTab('tab2');
        } else {
            fileTreeContainer.textContent = 'No items found based on filters.';
            showStatus('No items found based on filters.', 'warning');
        }
    } catch (error) {
        console.error('Error loading tree:', error);
        fileTreeContainer.textContent = `Error loading tree: ${error.message}. Check folder path and server logs.`;
        tabButtons[1].disabled = true;
    } finally {
        showLoading(loadTreeBtn, false, 'Load Project Tree');
    }
}
loadTreeBtn.addEventListener('click', performLoadTree);
refreshTreeBtn.addEventListener('click', performLoadTree);

browseServerFolderBtn.addEventListener('click', async () => {
    showLoading(browseServerFolderBtn, true, 'Browse Server Folder (Server-Side)');
    showStatus('Opening folder dialog on the server...', 'info');
    try {
        const response = await fetch('/api/browse_server_folder', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
        const data = await handleResponse(response);
        if (data.status === 'success' && data.path) {
            folderPathInput.value = data.path; updateClientStateFromUI();
            showStatus(`Server-side dialog returned: ${data.path}. Click 'Load Project Tree' to load it.`, 'success');
        } else if (data.status === 'cancelled') showStatus('Server-side folder selection was cancelled.', 'info');
        else showStatus(`Unexpected response from server: ${JSON.stringify(data)}`, 'error');
    } catch (error) {
        console.error('Error browsing server folder:', error);
        showStatus(`Failed to browse server folder: ${error.message}. Check server logs.`, 'error');
    } finally {
        showLoading(browseServerFolderBtn, false, 'Browse Server Folder (Server-Side)');
    }
});

function expandCollapseTree(expand, element = fileTreeContainer) {
    element.querySelectorAll('li.has-children > div > span.mr-1').forEach(toggle => { // Target toggle icons
        const childUl = toggle.closest('li').querySelector('ul');
        if (childUl) {
            const isHidden = childUl.classList.contains('hidden');
            if ((expand && isHidden) || (!expand && !isHidden)) {
                toggle.click(); // Simulate click to toggle state
            }
        }
    });
    // Recursively apply to children
    if (expand) { // Only recurse on expand to ensure all levels are opened
         element.querySelectorAll('li.has-children > ul').forEach(ul => {
            if (!ul.classList.contains('hidden')) { // If this ul is now visible
                expandCollapseTree(expand, ul);
            }
        });
    }
}
expandAllBtn.addEventListener('click', () => expandCollapseTree(true));
collapseAllBtn.addEventListener('click', () => expandCollapseTree(false));

checkAllTextBtn.addEventListener('click', () => {
    showStatus('Checking all text files in tree...');
    clientState.checkedTreePathsAbs.clear();
    fileTreeContainer.querySelectorAll('.tree-checkbox:not(:disabled)').forEach(cb => {
        const label = cb.closest('label'), path = label.dataset.path, icon = label.querySelector('.icon').textContent;
        if (icon === '📄' || icon === '📁') { // Check text files and folders
            cb.checked = true; clientState.checkedTreePathsAbs.add(path);
        } else { cb.checked = false; clientState.checkedTreePathsAbs.delete(path); }
    });
    saveStateToLocalStorage(); showStatus('All text files checked.');
});
uncheckAllBtn.addEventListener('click', () => {
    showStatus('Unchecking all items in tree...');
    clientState.checkedTreePathsAbs.clear();
    fileTreeContainer.querySelectorAll('.tree-checkbox:not(:disabled)').forEach(cb => cb.checked = false);
    saveStateToLocalStorage(); showStatus('All items unchecked.');
});
function applyCheckedPathsToTree() {
    fileTreeContainer.querySelectorAll('.tree-checkbox').forEach(cb => {
        cb.checked = clientState.checkedTreePathsAbs.has(cb.closest('label').dataset.path);
    });
}

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
    clientState.promptTemplates.forEach(t => templateSelect.innerHTML += `<option value="${t.name}">${t.name}</option>`);
    const currentPromptContent = customPromptTextarea.value.trim();
    const found = clientState.promptTemplates.find(t => t.content.trim() === currentPromptContent);
    templateSelect.value = found ? found.name : '';
}
loadTemplateBtn.addEventListener('click', () => {
    const name = templateSelect.value; if (!name) { showStatus('No template selected.', 'warning'); return; }
    const t = clientState.promptTemplates.find(t => t.name === name);
    if (t) {
        let content = t.content;
        content = content.replace(/{FOLDER_NAME}/g, folderPathInput.value.split(/[\/\\]/).pop() || 'UnknownProject');
        content = content.replace(/{FOLDER_PATH}/g, folderPathInput.value);
        content = content.replace(/{DATE}/g, new Date().toISOString().slice(0, 10));
        content = content.replace(/{TIME}/g, new Date().toLocaleTimeString());
        content = content.replace(/{DATETIME}/g, new Date().toLocaleString());
        content = content.replace(/{AUTHOR}/g, 'Anonymous');
        content = content.replace(/{USER_REQUEST}/g, '[User-defined request should go here]');
        customPromptTextarea.value = content; updateClientStateFromUI(); showStatus(`Loaded template: ${name}`);
    }
});
saveTemplateBtn.addEventListener('click', async () => {
    const content = customPromptTextarea.value.trim(); if (!content) { showStatus('Prompt is empty.', 'warning'); return; }
    let name = prompt('Template name:'); if (!name) return; name = name.trim(); if (!name) { alert('Name empty.'); return; }
    const existing = clientState.promptTemplates.find(t => t.name === name);
    if (existing && existing.content !== content && !confirm(`'${name}' exists. Overwrite?`)) return;
    if (existing && existing.content === content) { showStatus(`'${name}' already saved.`, 'info'); return; }
    try {
        const res = await fetch('/api/save_template', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, content }) });
        const data = await handleResponse(res); showStatus(data.message || `'${name}' saved.`);
        await fetchPromptTemplates(); templateSelect.value = name; updateClientStateFromUI();
    } catch (e) { console.error('Error saving template:', e); showStatus(`Save failed: ${e.message}`, 'error'); }
});
manageTemplateBtn.addEventListener('click', async () => {
    const action = prompt("Manage Templates:\n1. Delete\n2. Copy\nEnter #:"); if (!action) return;
    if (action === '1') {
        const name = prompt("Name of template to delete:"); if (!name) return;
        const t = clientState.promptTemplates.find(t => t.name === name);
        if (!t) { showStatus('Template not found.', 'warning'); return; }
        try {
            const res = await fetch('/api/delete_template', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: t.name, content: t.content }) });
            const data = await handleResponse(res); showStatus(data.message || `'${name}' deleted.`); await fetchPromptTemplates();
        } catch (e) { console.error('Error deleting template:', e); showStatus(`Delete failed: ${e.message}`, 'error'); }
    } else if (action === '2') {
        const name = prompt("Name of template to copy:"); if (!name) return;
        const orig = clientState.promptTemplates.find(t => t.name === name);
        if (!orig) { showStatus('Template not found.', 'warning'); return; }
        let count = 1, newName = `${orig.name} (Copy)`;
        while (clientState.promptTemplates.some(t => t.name === newName)) newName = `${orig.name} (Copy ${++count})`;
        try {
            const res = await fetch('/api/save_template', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newName, content: orig.content }) });
            const data = await handleResponse(res); showStatus(data.message || `Copied as '${newName}'.`);
            await fetchPromptTemplates(); templateSelect.value = newName; updateClientStateFromUI();
        } catch (e) { console.error('Error copying template:', e); showStatus(`Copy failed: ${e.message}`, 'error'); }
    } else showStatus('Invalid action.', 'warning');
});

generateBtn.addEventListener('click', async () => {
    const path = folderPathInput.value.trim();
    if (!path) { showStatus('Enter folder path on Tab 1.', 'warning'); activateTab('tab1'); return; }
    if (!fileTreeContainer.children.length) { showStatus('Load project tree first on Tab 1.', 'warning'); activateTab('tab1'); return; }
    if (!clientState.checkedTreePathsAbs.size) { showStatus('Select items in Project Explorer on Tab 2.', 'warning'); activateTab('tab2'); return; }
    showLoading(generateBtn, true, 'Generate Structure Text');
    rawOutputTextarea.value = 'Generating...'; renderedOutputDiv.innerHTML = 'Generating...'; copyRawBtn.disabled = true;
    tabButtons[2].disabled = false; activateTab('tab3'); activateSubTab('raw-output');
    updateClientStateFromUI();
    try {
        const res = await fetch('/api/generate_structure', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: path, filters: clientState.filterSettings,
                selected_paths_abs: Array.from(clientState.checkedTreePathsAbs),
                custom_prompt: clientState.customPrompt, loaded_doc_paths: clientState.loadedDocPaths
            })
        });
        const data = await handleResponse(res);
        rawOutputTextarea.value = data.markdown;
        renderedOutputDiv.innerHTML = DOMPurify.sanitize(marked.parse(data.markdown));
        copyRawBtn.disabled = false;
        if (clientState.saveOutputChecked) {
            const name = `fse_${path.split(/[\/\\]/).pop()||'output'}_${new Date().toISOString().slice(0,19).replace(/[:T]/g,'')}.md`;
            const blob = new Blob([data.markdown],{type:'text/markdown'}); const url=URL.createObjectURL(blob);
            const a=document.createElement('a'); a.href=url; a.download=name; document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
            showStatus('Output generated and downloaded.', 'success');
        } else showStatus('Output generated. View on Tab 3.', 'success');
    } catch (e) {
        console.error('Error generating:', e); rawOutputTextarea.value = `\`\`\`error\nError: ${e.message}\n\`\`\``;
        renderedOutputDiv.innerHTML = `<p class="text-red-500">Error: ${e.message}</p>`; showStatus(`Generate failed: ${e.message}`, 'error');
    } finally { showLoading(generateBtn, false, 'Generate Structure Text'); }
});

copyRawBtn.addEventListener('click', () => navigator.clipboard.writeText(rawOutputTextarea.value).then(()=>showStatus('Raw MD copied.', 'info')).catch(e=>showStatus('Copy failed: '+e,'error')));
clearOutputBtn.addEventListener('click', () => { rawOutputTextarea.value=''; renderedOutputDiv.innerHTML='Preview here.'; copyRawBtn.disabled=true; showStatus('Output cleared.'); });
themeToggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    clientState.currentTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    showStatus(`Theme: ${clientState.currentTheme}.`); saveStateToLocalStorage();
});


// --- Pre-selection Logic ---
function fnmatch(pattern, string) {
    // Basic glob to regex conversion
    // Does not support [abc] character classes, only * and ?
    const re = new RegExp('^' + pattern.replace(/\./g, '\\.').replace(/\*/g, '.*').replace(/\?/g, '.') + '$');
    return re.test(string);
}

function preselectFilesFromFirstTemplate() {
    if (clientState.promptTemplates.length === 0 || !clientState.promptTemplates[0]) {
        showStatus("No templates available for pre-selection.", "warning");
        return;
    }
    const firstTemplateContent = clientState.promptTemplates[0].content;

    // Convention: Look for patterns in a specific comment block
    // Example: <!-- PRESELECT_PATTERNS: *.py, src/*.js, README.md -->
    const patternMatch = firstTemplateContent.match(/<!--\s*PRESELECT_PATTERNS:\s*([^->]+)\s*-->/i);
    if (!patternMatch || !patternMatch[1]) {
        showStatus("No pre-selection patterns found in the first template.", "info");
        return;
    }

    const patterns = patternMatch[1].split(',').map(p => p.trim()).filter(p => p);
    if (patterns.length === 0) {
        showStatus("No valid pre-selection patterns extracted from the first template.", "info");
        return;
    }
    showStatus(`Attempting pre-selection with patterns: ${patterns.join(', ')}`, "info");

    let preselectedCount = 0;
    const rootFolderPath = folderPathInput.value.trim();
    if (!rootFolderPath) return;

    fileTreeContainer.querySelectorAll('.tree-checkbox:not(:disabled)').forEach(checkbox => {
        const label = checkbox.closest('label');
        const fullPath = label.dataset.path; // Absolute path
        
        // Get path relative to the project root for matching
        let relativePath = fullPath;
        if (fullPath.startsWith(rootFolderPath)) {
            relativePath = fullPath.substring(rootFolderPath.length).replace(/^[\/\\]+/, ''); // Remove leading slash
        }

        for (const pattern of patterns) {
            // fnmatch expects simple string, not full path for sub-matches sometimes
            // For now, we'll match against relative path and also just the name for simple patterns
            const nameOnly = fullPath.split(/[\/\\]/).pop();
            if (fnmatch(pattern, relativePath) || fnmatch(pattern, nameOnly)) {
                checkbox.checked = true;
                clientState.checkedTreePathsAbs.add(fullPath);
                preselectedCount++;
                break; // Move to next file if matched by one pattern
            }
        }
    });

    if (preselectedCount > 0) {
        saveStateToLocalStorage();
        showStatus(`Pre-selected ${preselectedCount} items based on first template patterns.`, "success");
    } else {
        showStatus("No items matched pre-selection patterns.", "info");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    populatePresetList();
    loadStateFromLocalStorage();
    fetchPromptTemplates();
    showStatus('Ready. Enter project folder and load tree.');
});