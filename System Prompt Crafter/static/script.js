document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const ideaTextarea = document.getElementById('idea');
    const craftorModelSelect = document.getElementById('craftor-model');
    const testerModelSelect = document.getElementById('tester-model');
    const startCraftingBtn = document.getElementById('start-crafting-btn');
    const runRefineBtn = document.getElementById('run-refine-btn');
    const startOverBtn = document.getElementById('start-over-btn');

    const setupSection = document.getElementById('setup-section');
    const workbenchSection = document.getElementById('workbench-section');
    const resultsSection = document.getElementById('results-section');
    const successSection = document.getElementById('success-section');

    const systemPromptTextarea = document.getElementById('system-prompt');
    const testPromptsList = document.getElementById('test-prompts-list');
    const testResultsContainer = document.getElementById('test-results-container');
    const analysisOutput = document.getElementById('analysis-output');
    const finalPromptTextarea = document.getElementById('final-prompt');
    const spinner = document.getElementById('spinner');

    // State
    let currentTestPrompts = [];

    // --- API Functions ---
    const api = {
        getModels: () => fetch('/api/v1/list_models').then(res => res.json()),
        startCrafting: (idea) => fetch('/api/v1/start_crafting', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea })
        }).then(res => res.json()),
        runTest: (system_prompt, test_prompts) => fetch('/api/v1/run_test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ system_prompt, test_prompts })
        }).then(res => res.json()),
        analyzeAndRefine: (system_prompt, test_results) => fetch('/api/v1/analyze_and_refine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ system_prompt, test_results })
        }).then(res => res.json())
    };

    // --- UI Update Functions ---
    const showSpinner = (show) => spinner.classList.toggle('hidden', !show);
    const disableButtons = (disabled) => {
        startCraftingBtn.disabled = disabled;
        runRefineBtn.disabled = disabled;
    };

    const populateModels = async () => {
        try {
            const models = await api.getModels();
            craftorModelSelect.innerHTML = '';
            testerModelSelect.innerHTML = '';
            models.forEach(model => {
                craftorModelSelect.innerHTML += `<option value="${model}">${model}</option>`;
                testerModelSelect.innerHTML += `<option value="${model}">${model}</option>`;
            });
            craftorModelSelect.disabled = false;
            testerModelSelect.disabled = false;
        } catch (error) {
            console.error("Failed to load models:", error);
            craftorModelSelect.innerHTML = '<option>Error loading models</option>';
            testerModelSelect.innerHTML = '<option>Error loading models</option>';
        }
    };
    
    const updateTestPromptsUI = (prompts) => {
        testPromptsList.innerHTML = '';
        prompts.forEach(prompt => {
            const li = document.createElement('li');
            li.textContent = prompt;
            testPromptsList.appendChild(li);
        });
    };

    const displayTestResults = (results) => {
        testResultsContainer.innerHTML = '<h3>Test Executions</h3>';
        results.forEach(result => {
            const div = document.createElement('div');
            div.className = 'result-pair';
            div.innerHTML = `
                <h4>User Prompt: "${result.user_prompt}"</h4>
                <div class="response">${result.ai_response.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
            `;
            testResultsContainer.appendChild(div);
        });
    };

    const resetUI = () => {
        setupSection.classList.remove('hidden');
        workbenchSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        successSection.classList.add('hidden');
        ideaTextarea.value = '';
        systemPromptTextarea.value = '';
        testResultsContainer.innerHTML = '';
        analysisOutput.textContent = '';
        currentTestPrompts = [];
        disableButtons(false);
    };

    // --- Event Handlers ---
    startCraftingBtn.addEventListener('click', async () => {
        const idea = ideaTextarea.value.trim();
        if (!idea) {
            alert('Please enter an idea for your system prompt.');
            return;
        }
        disableButtons(true);
        showSpinner(true);
        
        workbenchSection.classList.remove('hidden');
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });


        try {
            const data = await api.startCrafting(idea);
            systemPromptTextarea.value = data.system_prompt;
            currentTestPrompts = data.test_prompts;
            updateTestPromptsUI(currentTestPrompts);
            analysisOutput.textContent = `Initial Judging Criteria:\n\n${data.judging_criteria}`;
            testResultsContainer.innerHTML = ''; // Clear previous results
        } catch (error) {
            console.error(error);
            analysisOutput.textContent = `Error: ${error.message}`;
        } finally {
            disableButtons(false);
            showSpinner(false);
        }
    });

    runRefineBtn.addEventListener('click', async () => {
        const system_prompt = systemPromptTextarea.value.trim();
        if (!system_prompt || currentTestPrompts.length === 0) {
            alert('System prompt and test cases must be present.');
            return;
        }

        disableButtons(true);
        showSpinner(true);
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        testResultsContainer.innerHTML = '';
        analysisOutput.textContent = '';

        try {
            // 1. Run the test
            const test_results = await api.runTest(system_prompt, currentTestPrompts);
            displayTestResults(test_results);

            // 2. Analyze and refine
            const analysis_result = await api.analyzeAndRefine(system_prompt, test_results);
            analysisOutput.textContent = analysis_result.analysis;

            if (analysis_result.status === 'success') {
                finalPromptTextarea.value = analysis_result.final_prompt;
                successSection.classList.remove('hidden');
                workbenchSection.classList.add('hidden');
                resultsSection.classList.add('hidden');
                successSection.scrollIntoView({ behavior: 'smooth' });
            } else if (analysis_result.status === 'refine') {
                systemPromptTextarea.value = analysis_result.refined_prompt;
                currentTestPrompts = analysis_result.new_test_prompts;
                updateTestPromptsUI(currentTestPrompts);
                alert("Prompt has been refined. Review the new prompt and test cases, then run the test again.");
                workbenchSection.scrollIntoView({ behavior: 'smooth' });
            }
        } catch (error) {
            console.error(error);
            analysisOutput.textContent = `Error: ${error.message}`;
        } finally {
            disableButtons(false);
            showSpinner(false);
        }
    });

    startOverBtn.addEventListener('click', resetUI);

    // --- Initialization ---
    populateModels();
});
