document.addEventListener('DOMContentLoaded', () => {
    loadCategories();

    document.getElementById('craft-prompt-btn').addEventListener('click', craftPrompt);
    document.getElementById('store-prompt-btn').addEventListener('click', storePrompt);
    document.getElementById('test-llm-btn').addEventListener('click', testWithLLM);
});

const API_BASE_URL = ''; // Flask routes are at root

async function fetchAPI(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        logStatus(`API Error: ${error.message}`, 'error');
        console.error(`API Error at ${endpoint}:`, error);
        throw error; // Re-throw to be caught by caller
    }
}

async function loadCategories() {
    try {
        const data = await fetchAPI('/api/categories');
        populateSelect('subject', data.subjects);
        populateSelect('task', data.tasks);
        populateSelect('test', data.tests);
        logStatus('Categories loaded.');
    } catch (error) {
        logStatus('Failed to load categories.', 'error');
    }
}

function populateSelect(selectId, items) {
    const selectElement = document.getElementById(selectId);
    selectElement.innerHTML = ''; // Clear existing options
    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item;
        option.textContent = item;
        selectElement.appendChild(option);
    });
}

async function addItem(category) {
    const inputElement = document.getElementById(`new-${category}`);
    const newItem = inputElement.value.trim();
    if (!newItem) {
        logStatus(`Please enter a value for new ${category}.`, 'warning');
        return;
    }

    try {
        const response = await fetchAPI(`/api/add_item/${category}`, 'POST', { item: newItem });
        logStatus(response.message, 'success');
        inputElement.value = ''; // Clear input
        // Reload categories to reflect changes
        if (category === 'subject') populateSelect('subject', response.items);
        if (category === 'task') populateSelect('task', response.items);
        if (category === 'test') populateSelect('test', response.items);
        
    } catch (error) {
        logStatus(`Failed to add ${category}: ${error.message}`, 'error');
    }
}

function craftPrompt() {
    const subject = document.getElementById('subject').value;
    const task = document.getElementById('task').value;
    const test = document.getElementById('test').value;

    if (!subject || !task || !test) {
        logStatus('Please select a subject, task, and test item.', 'warning');
        document.getElementById('constructed-prompt').value = '';
        document.getElementById('store-prompt-btn').disabled = true;
        document.getElementById('test-llm-btn').disabled = true;
        return;
    }

    // Simple template, can be made more complex
    const promptText = `Considering the subject of "${subject}", your task is to "${task}". This exercise is designed to test your capability in ${test}. Please proceed.`;
    
    document.getElementById('constructed-prompt').value = promptText;
    logStatus('Prompt crafted successfully.');
    document.getElementById('store-prompt-btn').disabled = false;
    document.getElementById('test-llm-btn').disabled = false;
}

async function storePrompt() {
    const promptText = document.getElementById('constructed-prompt').value;
    if (!promptText) {
        logStatus('No prompt crafted to store.', 'warning');
        return;
    }

    const subject = document.getElementById('subject').value;
    const task = document.getElementById('task').value;
    const test = document.getElementById('test').value;

    logStatus('Storing prompt...');
    document.getElementById('store-prompt-btn').disabled = true;

    try {
        const response = await fetchAPI('/api/store_prompt', 'POST', {
            prompt: promptText,
            subject: subject,
            task: task,
            test: test
        });
        logStatus(response.message, 'success');
    } catch (error) {
        logStatus(`Failed to store prompt: ${error.message}`, 'error');
    } finally {
        document.getElementById('store-prompt-btn').disabled = false; // Re-enable, or keep disabled if one-time store per craft
    }
}

async function testWithLLM() {
    const promptText = document.getElementById('constructed-prompt').value;
    if (!promptText) {
        logStatus('No prompt crafted to test.', 'warning');
        return;
    }

    const llmResponseOutput = document.getElementById('llm-response-output');
    llmResponseOutput.innerHTML = '<div class="loader"></div>'; // Show loader
    logStatus('Sending prompt to LLM...');
    document.getElementById('test-llm-btn').disabled = true;

    try {
        const response = await fetchAPI('/api/test_llm', 'POST', { prompt: promptText });
        llmResponseOutput.textContent = response.response || "LLM returned an empty response.";
        logStatus('LLM response received.', 'success');
    } catch (error) {
        llmResponseOutput.textContent = `Error: ${error.message}`;
        logStatus(`Error communicating with LLM: ${error.message}`, 'error');
    } finally {
        document.getElementById('test-llm-btn').disabled = false;
    }
}

function logStatus(message, type = 'info') {
    const statusLog = document.getElementById('status-log');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.textContent = `[${timestamp}] ${message}`;
    statusLog.prepend(logEntry); // Add to top
    // Optional: Limit number of log entries
    if (statusLog.children.length > 20) {
        statusLog.removeChild(statusLog.lastChild);
    }
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Add a bit more styling for log types in JS (can also be done in CSS)
const style = document.createElement('style');
style.innerHTML = `
    .log-entry.error { color: red; font-weight: bold; }
    .log-entry.success { color: green; }
    .log-entry.warning { color: orange; }
`;
document.head.appendChild(style);