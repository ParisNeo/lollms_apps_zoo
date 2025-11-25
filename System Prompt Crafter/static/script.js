document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 App initialized - DOM loaded');

  // ==========================================
  // UI ELEMENT REFERENCES
  // ==========================================
  const elements = {
    // Input elements
    ideaTextarea: document.getElementById('idea'),
    craftorModelSelect: document.getElementById('craftor-model'),
    testerModelSelect: document.getElementById('tester-model'),
    
    // Buttons
    startCraftingBtn: document.getElementById('start-crafting-btn'),
    runRefineBtn: document.getElementById('run-refine-btn'),
    startOverBtn: document.getElementById('start-over-btn'),
    
    // Sections
    setupSection: document.getElementById('setup-section'),
    workbenchSection: document.getElementById('workbench-section'),
    resultsSection: document.getElementById('results-section'),
    successSection: document.getElementById('success-section'),
    
    // Output elements
    systemPromptTextarea: document.getElementById('system-prompt'),
    testPromptsList: document.getElementById('test-prompts-list'),
    testResultsContainer: document.getElementById('test-results-container'),
    analysisOutput: document.getElementById('analysis-output'),
    finalPromptTextarea: document.getElementById('final-prompt'),
    spinner: document.getElementById('spinner')
  };

  // Validate all elements exist
  console.log('📋 Validating UI elements...');
  Object.entries(elements).forEach(([key, element]) => {
    if (!element) {
      console.error(`❌ Missing element: ${key}`);
    } else {
      console.log(`✅ Found element: ${key}`);
    }
  });

  // ==========================================
  // STATE MANAGEMENT
  // ==========================================
  const state = {
    currentTestPrompts: []
  };

  // ==========================================
  // API FUNCTIONS
  // ==========================================
  const api = {
    getModels: async () => {
      console.log('📡 API: Fetching models from /api/v1/list_models');
      try {
        const response = await fetch('/api/v1/list_models');
        console.log('📥 Response status:', response.status, response.statusText);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Models received:', data);
        return data;
      } catch (error) {
        console.error('❌ Error fetching models:', error);
        throw error;
      }
    },

    startCrafting: async (request) => {
      console.log('📡 API: Starting crafting with idea:', request.idea.substring(0, 50) + '...');
      try {
        const response = await fetch('/api/v1/start_crafting', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request)
        });
        console.log('📥 Start crafting response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Crafting data received:', {
          systemPromptLength: data.system_prompt?.length,
          testPromptsCount: data.test_prompts?.length,
          judgingCriteriaLength: data.judging_criteria?.length
        });
        return data;
      } catch (error) {
        console.error('❌ Error in startCrafting:', error);
        throw error;
      }
    },

    runTest: async (request) => {
      console.log('📡 API: Running test with', request.test_prompts.length, 'prompts');
      try {
        const response = await fetch('/api/v1/run_test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request)
        });
        console.log('📥 Run test response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Test results received:', data.length, 'results');
        return data;
      } catch (error) {
        console.error('❌ Error in runTest:', error);
        throw error;
      }
    },

    analyzeAndRefine: async (request) => {
      console.log('📡 API: Analyzing and refining with', request.test_results.length, 'results');
      try {
        const response = await fetch('/api/v1/analyze_and_refine', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request)
        });
        console.log('📥 Analyze response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Analysis received, status:', data.status);
        return data;
      } catch (error) {
        console.error('❌ Error in analyzeAndRefine:', error);
        throw error;
      }
    }
  };

  // ==========================================
  // UI UPDATE FUNCTIONS
  // ==========================================
  const ui = {
    showSpinner: (show) => {
      console.log(show ? '⏳ Showing spinner' : '✓ Hiding spinner');
      elements.spinner.classList.toggle('hidden', !show);
    },

    disableButtons: (disabled) => {
      console.log(disabled ? '🔒 Disabling buttons' : '🔓 Enabling buttons');
      elements.startCraftingBtn.disabled = disabled;
      elements.runRefineBtn.disabled = disabled;
    },

    populateModels: async () => {
      console.log('🔄 Starting to populate models...');
      try {
        const models = await api.getModels();
        
        if (!Array.isArray(models)) {
          console.error('❌ Models response is not an array:', models);
          throw new Error('Invalid models format');
        }

        console.log('📝 Populating', models.length, 'models into selects');
        
        elements.craftorModelSelect.innerHTML = '';
        elements.testerModelSelect.innerHTML = '';
        
        models.forEach((model, index) => {
        console.log(`  ${index + 1}. Adding model:`, model);

        const option1 = document.createElement('option');
        option1.value = model.model_name;
        option1.textContent = model.model_name;
        elements.craftorModelSelect.appendChild(option1);

        const option2 = document.createElement('option');
        option2.value = model.model_name;
        option2.textContent = model.model_name;
        elements.testerModelSelect.appendChild(option2);
        });
        
        elements.craftorModelSelect.disabled = false;
        elements.testerModelSelect.disabled = false;
        console.log('✅ Models populated successfully');
      } catch (error) {
        console.error('❌ Failed to populate models:', error);
        elements.craftorModelSelect.innerHTML = '<option>Error loading models</option>';
        elements.testerModelSelect.innerHTML = '<option>Error loading models</option>';
        alert('Failed to load models. Check console for details.');
      }
    },

    updateTestPrompts: (prompts) => {
      console.log('📝 Updating test prompts UI with', prompts.length, 'prompts');
      elements.testPromptsList.innerHTML = '';
      
      prompts.forEach((prompt, index) => {
        console.log(`  ${index + 1}. ${prompt.substring(0, 50)}...`);
        const li = document.createElement('li');
        li.textContent = prompt;
        elements.testPromptsList.appendChild(li);
      });
    },

    displayTestResults: (results) => {
      console.log('📊 Displaying', results.length, 'test results');
      elements.testResultsContainer.innerHTML = '<h3>Test Executions</h3>';
      
      results.forEach((result, index) => {
        console.log(`  Result ${index + 1}:`, {
          userPrompt: result.user_prompt?.substring(0, 50),
          responseLength: result.ai_response?.length
        });
        
        const div = document.createElement('div');
        div.className = 'result-pair';
        div.innerHTML = `
          <div><strong>User Prompt:</strong> "${result.user_prompt}"</div>
          <div><strong>AI Response:</strong></div>
          <pre>${result.ai_response.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</pre>
        `;
        elements.testResultsContainer.appendChild(div);
      });
    },

    resetUI: () => {
      console.log('🔄 Resetting UI to initial state');
      elements.setupSection.classList.remove('hidden');
      elements.workbenchSection.classList.add('hidden');
      elements.resultsSection.classList.add('hidden');
      elements.successSection.classList.add('hidden');
      elements.ideaTextarea.value = '';
      elements.systemPromptTextarea.value = '';
      elements.testResultsContainer.innerHTML = '';
      elements.analysisOutput.textContent = '';
      state.currentTestPrompts = [];
      ui.disableButtons(false);
      console.log('✅ UI reset complete');
    }
  };

  // ==========================================
  // EVENT HANDLERS
  // ==========================================
  elements.startCraftingBtn.addEventListener('click', async () => {
    console.log('🎨 Start Crafting button clicked');
    const idea = elements.ideaTextarea.value.trim();
    
    if (!idea) {
      console.warn('⚠️ No idea entered');
      alert('Please enter an idea for your system prompt.');
      return;
    }

    console.log('📝 Idea entered:', idea.substring(0, 100) + '...');
    ui.disableButtons(true);
    ui.showSpinner(true);
    elements.workbenchSection.classList.remove('hidden');
    elements.resultsSection.classList.remove('hidden');
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });

    try {
      const data = await api.startCrafting({
        idea: idea,
        craftor_model: elements.craftorModelSelect.value
      });
      
      elements.systemPromptTextarea.value = data.system_prompt;
      state.currentTestPrompts = data.test_prompts;
      ui.updateTestPrompts(state.currentTestPrompts);
      elements.analysisOutput.textContent = `Initial Judging Criteria:\n\n${data.judging_criteria}`;
      elements.testResultsContainer.innerHTML = '';
      
      console.log('✅ Crafting complete');
    } catch (error) {
      console.error('❌ Crafting failed:', error);
      elements.analysisOutput.textContent = `Error: ${error.message}`;
    } finally {
      ui.disableButtons(false);
      ui.showSpinner(false);
    }
  });

  elements.runRefineBtn.addEventListener('click', async () => {
    console.log('🔬 Run & Refine button clicked');
    const system_prompt = elements.systemPromptTextarea.value.trim();
    
    if (!system_prompt || state.currentTestPrompts.length === 0) {
      console.warn('⚠️ Missing system prompt or test cases');
      alert('System prompt and test cases must be present.');
      return;
    }

    console.log('🧪 Starting test run with', state.currentTestPrompts.length, 'prompts');
    ui.disableButtons(true);
    ui.showSpinner(true);
    elements.resultsSection.classList.remove('hidden');
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    elements.testResultsContainer.innerHTML = '';
    elements.analysisOutput.textContent = '';

    try {
      // Run the test
      console.log('⏳ Running tests...');
      const test_results = await api.runTest({
        system_prompt: system_prompt,
        test_prompts: state.currentTestPrompts,
        tester_model: elements.testerModelSelect.value
      });
      ui.displayTestResults(test_results);
      
      // Analyze and refine
      console.log('⏳ Analyzing results...');
      const analysis_result = await api.analyzeAndRefine({
        system_prompt: system_prompt,
        test_results: test_results,
        craftor_model: elements.craftorModelSelect.value
      });
      elements.analysisOutput.textContent = analysis_result.analysis;

      if (analysis_result.status === 'success') {
        console.log('🎉 Success! Final prompt ready');
        elements.finalPromptTextarea.value = analysis_result.final_prompt;
        elements.successSection.classList.remove('hidden');
        elements.workbenchSection.classList.add('hidden');
        elements.resultsSection.classList.add('hidden');
        elements.successSection.scrollIntoView({ behavior: 'smooth' });
      } else if (analysis_result.status === 'refine') {
        console.log('🔄 Refinement needed, updating prompt');
        elements.systemPromptTextarea.value = analysis_result.refined_prompt;
        state.currentTestPrompts = analysis_result.new_test_prompts;
        ui.updateTestPrompts(state.currentTestPrompts);
        alert("Prompt has been refined. Review the new prompt and test cases, then run the test again.");
        elements.workbenchSection.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (error) {
      console.error('❌ Test/refinement failed:', error);
      elements.analysisOutput.textContent = `Error: ${error.message}`;
    } finally {
      ui.disableButtons(false);
      ui.showSpinner(false);
    }
  });

  elements.startOverBtn.addEventListener('click', () => {
    console.log('🔄 Start Over button clicked');
    ui.resetUI();
  });

  // ==========================================
  // INITIALIZATION
  // ==========================================
  console.log('🎬 Starting initialization...');
  ui.populateModels();
  console.log('✅ Initialization complete');
});
