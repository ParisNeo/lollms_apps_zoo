document.addEventListener('DOMContentLoaded', () => {
    const API_URL = '/api';
    const TAUX_COTISATIONS = 0.2188;
    let currentSessionId = null;
    let currentBaseNetSalary = 0;
    let currentAnnualCP = 0;
    let currentMetrics = {};
    let currentConfig = {};
    const workDays = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'];
    let selectedForComparison = [];

    const bodyEl = document.body;
    const htmlEl = document.documentElement;
    const homeScreen = document.getElementById('home-screen');
    const calculatorScreen = document.getElementById('calculator-screen');
    const sessionList = document.getElementById('session-list');
    const newSessionBtn = document.getElementById('new-session-btn');
    const backToHomeBtn = document.getElementById('back-to-home-btn');
    const simForm = document.getElementById('sim-form');
    const planningGrid = document.getElementById('planning-grid');
    const typeContratSelect = document.getElementById('type-contrat');
    const semainesIncompleteGroup = document.getElementById('semaines-incomplete-group');
    const toastContainer = document.getElementById('toast-container');
    const spinnerOverlay = document.getElementById('spinner-overlay');
    const joursAccueilMoisInput = document.getElementById('jours-accueil-mois');
    const printBtn = document.getElementById('print-btn');
    const baseResultsContainer = document.getElementById('base-results');
    const monthlyResultsDisplay = document.getElementById('monthly-results-display');
    const printTitle = document.getElementById('print-title');
    const fraisEntretienInput = document.getElementById('frais-entretien');
    const resultsContainer = document.getElementById('results-container');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const compareBtn = document.getElementById('compare-btn');
    const comparisonModal = document.getElementById('comparison-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const comparisonContent = document.getElementById('comparison-content');
    
    const engagementBtn = document.getElementById('engagement-btn');
    const engagementModal = document.getElementById('engagement-modal');
    const closeEngagementModalBtn = document.getElementById('close-engagement-modal-btn');
    const engagementContent = document.getElementById('engagement-content');
    const engagementTitle = document.getElementById('engagement-title');
    const printEngagementBtn = document.getElementById('print-engagement-btn');
    const printSummaryContainer = document.getElementById('print-summary-container');

    const ICONS = {
        add: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>`,
        back: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/></svg>`,
        edit: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M12.854.146a.5.5 0 0 0-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 0 0 0-.708l-3-3zm-1.55 1.55L3.5 10.44V13h2.56l7.79-7.79-2.56-2.56zM2 2a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-3.5l-1-1V12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h3.5l1-1H2z"/></svg>`,
        trash: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>`,
        duplicate: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2Zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H6ZM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1H2Z"/></svg>`,
        print: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M2.5 8a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/><path d="M5 1a2 2 0 0 0-2 2v2H2a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1v1a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-1h1a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-1V3a2 2 0 0 0-2-2H5zM4 3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2H4V3zm1 5a2 2 0 0 0-2 2v1H2a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v-1a2 2 0 0 0-2-2H5zm7 2v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1z"/></svg>`,
        propagate: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8.5 2.134a.5.5 0 0 0-1 0L3.56 6.06a.5.5 0 0 0 .44 1.44h8a.5.5 0 0 0 .44-1.44L8.5 2.134zM12.56 8.56l-3.94 3.939a.5.5 0 0 1-.44.061H4.5a.5.5 0 0 1 0-1h3.62l3.94-3.94a.5.5 0 1 1 .707.707z"/></svg>`,
        sun: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16"><path d="M8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0 1a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM8 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 0zm0 13a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 13zm8-5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2a.5.5 0 0 1 .5.5zM3 8a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2A.5.5 0 0 1 3 8zm10.657-5.657a.5.5 0 0 1 0 .707l-1.414 1.415a.5.5 0 1 1-.707-.708l1.414-1.414a.5.5 0 0 1 .707 0zm-9.193 9.193a.5.5 0 0 1 0 .707L3.05 13.657a.5.5 0 0 1-.707-.707l1.414-1.414a.5.5 0 0 1 .707 0zm9.193 2.121a.5.5 0 0 1-.707 0l-1.414-1.414a.5.5 0 0 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .707zM4.464 4.465a.5.5 0 0 1-.707 0L2.343 3.05a.5.5 0 1 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .707z"/></svg>`,
        moon: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16"><path d="M6 .278a.768.768 0 0 1 .08.858 7.208 7.208 0 0 0-.878 3.46c0 4.021 3.278 7.277 7.318 7.277.527 0 1.04-.055 1.533-.16a.787.787 0 0 1 .81.316.733.733 0 0 1-.031.893A8.349 8.349 0 0 1 8.344 16C3.734 16 0 12.286 0 7.71 0 4.266 2.114 1.312 5.124.06A.752.752 0 0 1 6 .278zM4.858 1.311A7.269 7.269 0 0 0 7.71 14.995c.621 0 1.22-.064 1.79-.185a.757.757 0 0 1 .57-.833A6.72 6.72 0 0 0 11.231 3.48a.757.757 0 0 1-.84-.57A7.269 7.269 0 0 0 4.858 1.311z"/></svg>`,
        compare: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5 10.5a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5zm0-2a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0-2a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/><path d="M3 0h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2zm10 1H3a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1z"/></svg>`,
        plusCircle: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus-circle" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/></svg>`,
        minusCircle: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-dash-circle" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M4 8a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7A.5.5 0 0 1 4 8z"/></svg>`,
        contract: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2zm10-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1z"/><path d="M4.5 5.5a.5.5 0 0 0 0 1h7a.5.5 0 0 0 0-1h-7zm0 2a.5.5 0 0 0 0 1h7a.5.5 0 0 0 0-1h-7zm0 2a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1h-4z"/></svg>`
    };

    const showSpinner = () => spinnerOverlay.classList.remove('hidden');
    const hideSpinner = () => spinnerOverlay.classList.add('hidden');
    
    const showToast = (message, type = 'success') => {
        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
        toast.className = `p-4 rounded-lg text-white shadow-lg animate-toast-in ${bgColor}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.remove('animate-toast-in');
            toast.classList.add('animate-toast-out');
            toast.addEventListener('animationend', () => toast.remove());
        }, 4000);
    };
    
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            htmlEl.classList.add('dark');
            themeToggleBtn.innerHTML = ICONS.sun;
            themeToggleBtn.title = `Passer au thème clair`;
        } else {
            htmlEl.classList.remove('dark');
            themeToggleBtn.innerHTML = ICONS.moon;
            themeToggleBtn.title = `Passer au thème sombre`;
        }
    };
    
    const toggleTheme = () => {
        const newTheme = htmlEl.classList.contains('dark') ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };

    const showHomeScreen = () => { homeScreen.classList.remove('hidden'); calculatorScreen.classList.add('hidden'); loadSessions(); };
    const showCalculatorScreen = (isNew = true) => {
        homeScreen.classList.add('hidden'); calculatorScreen.classList.remove('hidden'); resultsContainer.classList.add('hidden');
        simForm.reset(); createPlanningGrid(); semainesIncompleteGroup.classList.add('hidden');
        document.getElementById('date-debut-contrat').valueAsDate = new Date();
        fraisEntretienInput.value = "3.73"; document.getElementById('tarif-horaire-net').value = "4.50";
        document.getElementById('calculator-title').textContent = isNew ? 'Nouvelle Simulation' : 'Modifier la Simulation'; currentSessionId = null;
    };

    const createDayBlock = (day) => {
        const dayLabel = day.charAt(0).toUpperCase() + day.slice(1);
        const dayBlock = document.createElement('div');
        dayBlock.className = 'bg-slate-50 dark:bg-gray-800 p-3 rounded-lg space-y-2';
        dayBlock.innerHTML = `
            <div class="flex justify-between items-center">
                <label class="font-semibold text-sm">${dayLabel}</label>
                <button type="button" class="text-gray-400 hover:text-primary-DEFAULT transition-colors propagate-btn" data-day="${day}" title="Appliquer à tous les jours">${ICONS.propagate}</button>
            </div>
            <div class="flex gap-2">
                <input type="time" id="${day}-debut" data-day="${day}" class="w-full text-sm rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 shadow-sm focus:border-primary-light focus:ring-primary-light">
                <input type="time" id="${day}-fin" data-day="${day}" class="w-full text-sm rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 shadow-sm focus:border-primary-light focus:ring-primary-light">
            </div>`;
        return dayBlock;
    };
    
    const createPlanningGrid = () => { planningGrid.innerHTML = ''; workDays.forEach(day => planningGrid.appendChild(createDayBlock(day))); };
    
    const handlePropagateDay = (e) => {
        const propagateBtn = e.target.closest('.propagate-btn'); if (!propagateBtn) return;
        const sourceDay = propagateBtn.dataset.day; const debut = document.getElementById(`${sourceDay}-debut`).value; const fin = document.getElementById(`${sourceDay}-fin`).value;
        if (!debut && !fin) { showToast(`Veuillez renseigner les horaires pour ${sourceDay} d'abord.`, 'error'); return; }
        workDays.forEach(day => { if (day !== sourceDay) { document.getElementById(`${day}-debut`).value = debut; document.getElementById(`${day}-fin`).value = fin; } });
        showToast(`Horaires de ${sourceDay} appliqués aux autres jours.`, 'success');
    };

    const updateCompareButton = () => { compareBtn.disabled = selectedForComparison.length < 2; };
    
    const loadSessions = async () => {
        showSpinner(); selectedForComparison = []; updateCompareButton();
        try {
            const response = await fetch(`${API_URL}/sessions`); if (!response.ok) throw new Error('Erreur réseau');
            const sessions = await response.json(); sessionList.innerHTML = '';
            if (sessions.length === 0) { sessionList.innerHTML = "<p class='col-span-full text-center text-gray-500'>Aucune simulation. Cliquez sur 'Nouvelle Simulation' pour commencer.</p>"; } 
            else {
                sessions.forEach(session => {
                    const card = document.createElement('div');
                    card.className = 'bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow flex items-start gap-3';
                    card.innerHTML = `
                        <div class="flex-shrink-0 pt-1">
                            <input type="checkbox" class="session-checkbox h-4 w-4 rounded border-gray-300 text-primary-DEFAULT focus:ring-primary-light" data-id="${session.id}">
                        </div>
                        <div class="flex-grow cursor-pointer session-name" data-id="${session.id}">
                            <p class="font-semibold text-gray-800 dark:text-gray-100">${session.name}</p>
                        </div>
                        <div class="flex-shrink-0 flex items-center gap-1">
                            <button class="btn-icon duplicate-btn" data-id="${session.id}" title="Dupliquer">${ICONS.duplicate}</button>
                            <button class="btn-icon edit-btn" data-id="${session.id}" title="Modifier">${ICONS.edit}</button>
                            <button class="btn-icon delete-btn text-red-500" data-id="${session.id}" data-name="${session.name}" title="Supprimer">${ICONS.trash}</button>
                        </div>`;
                    sessionList.appendChild(card);
                });
            }
        } catch (error) { showToast("Impossible de charger les simulations.", 'error'); } finally { hideSpinner(); }
    };

    const handleSessionClick = async (e) => {
        const target = e.target;
        const editBtn = target.closest('.edit-btn');
        const deleteBtn = target.closest('.delete-btn');
        const sessionNameSpan = target.closest('.session-name');
        const duplicateBtn = target.closest('.duplicate-btn');
        const checkbox = target.closest('.session-checkbox');
    
        if (checkbox) {
            const sessionId = checkbox.dataset.id;
            if (checkbox.checked) { if (!selectedForComparison.includes(sessionId)) selectedForComparison.push(sessionId); } 
            else { selectedForComparison = selectedForComparison.filter(id => id !== sessionId); }
            updateCompareButton();
            return;
        }
    
        if (editBtn || sessionNameSpan) {
            const sessionId = editBtn ? editBtn.dataset.id : sessionNameSpan.dataset.id;
            showSpinner();
            try {
                const response = await fetch(`${API_URL}/sessions/${sessionId}`); if (!response.ok) throw new Error('Session non trouvée');
                const session = await response.json(); showCalculatorScreen(false); populateForm(session);
            } catch (error) { showToast("Erreur lors du chargement de la session.", 'error'); } finally { hideSpinner(); }
        } else if (deleteBtn) {
            const sessionId = deleteBtn.dataset.id;
            const sessionName = deleteBtn.dataset.name;
            if (confirm(`Êtes-vous sûr de vouloir supprimer la simulation "${sessionName}" ?`)) {
                showSpinner();
                try {
                    const response = await fetch(`${API_URL}/sessions/${sessionId}`, { method: 'DELETE' }); if (!response.ok) throw new Error('Erreur serveur');
                    showToast(`La simulation "${sessionName}" a été supprimée.`, 'success');
                    loadSessions();
                } catch (error) { showToast("Erreur lors de la suppression.", 'error'); } finally { hideSpinner(); }
            }
        } else if (duplicateBtn) {
            const sessionId = duplicateBtn.dataset.id;
            showSpinner();
            try {
                const response = await fetch(`${API_URL}/sessions/${sessionId}/duplicate`, { method: 'POST' }); if (!response.ok) throw new Error('Erreur serveur lors de la duplication.');
                const duplicatedSession = await response.json();
                showToast(`Simulation "${duplicatedSession.name}" créée.`, 'success');
                loadSessions();
            } catch (error) { showToast(error.message, 'error'); } finally { hideSpinner(); }
        }
    };
    
    const handleCompare = async () => {
        showSpinner();
        try {
            const promises = selectedForComparison.map(id => fetch(`${API_URL}/sessions/${id}`).then(res => res.json()));
            const sessionsData = await Promise.all(promises);
            const comparisonResults = sessionsData.map(session => ({ name: session.name, ...calculateMetrics(session.config) }));
            const bestOptionIndex = comparisonResults.reduce((minIndex, current, currentIndex, array) => current.coutTotalAnnuel < array[minIndex].coutTotalAnnuel ? currentIndex : minIndex, 0);
            
            const tableHeaders = `
                <thead>
                    <tr class="bg-gray-50 dark:bg-gray-700">
                        <th class="p-3 text-left font-semibold">Simulation</th>
                        <th class="p-3 text-right font-semibold">Coût Annuel Total</th>
                        <th class="p-3 text-right font-semibold">Salaire Net /mois</th>
                        <th class="p-3 text-right font-semibold">Indemnité CP /an</th>
                    </tr>
                </thead>`;

            const tableRows = comparisonResults.map((res, index) => `
                <tr class="border-b dark:border-gray-600 ${index === bestOptionIndex ? 'bg-green-100 dark:bg-green-900/50 font-bold' : ''}">
                    <td class="p-3">${res.name} ${index === bestOptionIndex ? '<span class="text-xs text-green-600 dark:text-green-400 ml-2">(Le + avantageux)</span>' : ''}</td>
                    <td class="p-3 text-right font-mono">${res.coutTotalAnnuel.toFixed(2)} €</td>
                    <td class="p-3 text-right font-mono">${res.salaireMensuelNet.toFixed(2)} €</td>
                    <td class="p-3 text-right font-mono">${res.indemniteCPAnnuelle.toFixed(2)} €</td>
                </tr>`).join('');
            
            comparisonContent.innerHTML = `<table class="w-full text-sm">${tableHeaders}<tbody>${tableRows}</tbody></table>`;
            comparisonModal.classList.remove('hidden');
        } catch (error) { showToast("Erreur lors de la récupération des données pour la comparaison.", 'error'); } finally { hideSpinner(); }
    };
    
    const populateForm = (session) => {
        currentSessionId = session.id;
        document.getElementById('session-name').value = session.name;
        document.getElementById('calculator-title').textContent = `Modifier : ${session.name}`;
        const config = session.config;
        document.getElementById('tarif-horaire-net').value = config.tarif_horaire_net;
        fraisEntretienInput.value = config.frais_entretien_par_jour;
        document.getElementById('date-debut-contrat').value = config.date_debut_contrat;
        typeContratSelect.value = config.type_contrat;
        semainesIncompleteGroup.classList.toggle('hidden', config.type_contrat !== 'annee_incomplete');
        if (config.type_contrat === 'annee_incomplete') { document.getElementById('semaines-travaillees').value = config.semaines_travaillees_par_an; }
        workDays.forEach(day => {
            const debutInput = document.getElementById(`${day}-debut`);
            const finInput = document.getElementById(`${day}-fin`);
            if (debutInput && config.planning[day]) {
                debutInput.value = config.planning[day].debut || '';
                finInput.value = config.planning[day].fin || '';
            }
        });
    };

    const handleFormSubmit = async (e) => {
        e.preventDefault(); if (!simForm.checkValidity()) { showToast('Veuillez remplir tous les champs obligatoires.', 'error'); return; }
        const planning = {};
        workDays.forEach(day => {
            const debut = document.getElementById(`${day}-debut`).value || null;
            const fin = document.getElementById(`${day}-fin`).value || null;
            planning[day] = (debut && fin) ? { debut, fin } : null;
        });
        const sessionData = {
            id: currentSessionId || undefined, name: document.getElementById('session-name').value,
            config: {
                planning,
                tarif_horaire_net: parseFloat(document.getElementById('tarif-horaire-net').value),
                frais_entretien_par_jour: parseFloat(fraisEntretienInput.value),
                type_contrat: typeContratSelect.value,
                semaines_travaillees_par_an: typeContratSelect.value === 'annee_incomplete' ? parseInt(document.getElementById('semaines-travaillees').value) : null,
                date_debut_contrat: document.getElementById('date-debut-contrat').value
            }
        };
        const method = currentSessionId ? 'PUT' : 'POST';
        const url = currentSessionId ? `${API_URL}/sessions/${currentSessionId}` : `${API_URL}/sessions`;
        showSpinner();
        try {
            const response = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sessionData) });
            if (!response.ok) throw new Error('Erreur lors de la sauvegarde.');
            const savedData = await response.json();
            currentSessionId = savedData.id;
            showToast('Simulation enregistrée avec succès !', 'success');
            const simName = savedData.name || "Sans nom";
            printTitle.innerHTML = `Rapport de Simulation<br><span class="text-lg font-normal text-gray-500 dark:text-gray-400">${simName}</span>`;
            runAndDisplayCalculations(savedData.config);
        } catch (error) { showToast(error.message, 'error'); } finally { hideSpinner(); }
    };
    
    const calculateMetrics = (config) => {
        let totalSeconds = 0, joursTravailles = 0;
        workDays.forEach(day => {
            const pDay = config.planning[day];
            if (pDay && pDay.debut && pDay.fin) {
                const start = new Date(`1970-01-01T${pDay.debut}Z`);
                const end = new Date(`1970-01-01T${pDay.fin}Z`);
                if (end > start) { totalSeconds += (end - start) / 1000; joursTravailles++; }
            }
        });
        const heuresSemaine = totalSeconds / 3600;
        const tarifHoraireBrut = config.tarif_horaire_net / (1 - TAUX_COTISATIONS);
        const semainesAnnualisees = config.type_contrat === 'annee_complete' ? 47 : (config.semaines_travaillees_par_an || 0);
        const semainesContrat = config.type_contrat === 'annee_complete' ? 52 : semainesAnnualisees;
        const salaireMensuelBrut = (tarifHoraireBrut * heuresSemaine * semainesContrat) / 12;
        const salaireMensuelNet = salaireMensuelBrut * (1 - TAUX_COTISATIONS);
        const heuresMensualisees = (heuresSemaine * semainesContrat) / 12;
        const joursActiviteMensualises = (joursTravailles * semainesAnnualisees) / 12;
        let indemniteCPAnnuelle = 0, joursAcquis = 0, indemnite10pourcent = 0, indemniteMaintien = 0;
        if (config.type_contrat === 'annee_incomplete') {
            joursAcquis = (semainesAnnualisees / 4) * 2.5;
            const salaireBrutTotalAnnuel = salaireMensuelBrut * 12;
            indemnite10pourcent = salaireBrutTotalAnnuel * 0.10;
            indemniteMaintien = (joursAcquis / 6) * heuresSemaine * tarifHoraireBrut;
            indemniteCPAnnuelle = Math.max(indemnite10pourcent, indemniteMaintien);
        }
        const entretienAnnuel = (joursTravailles * semainesAnnualisees) * config.frais_entretien_par_jour;
        const salaireAnnuelNet = salaireMensuelNet * 12;
        const coutTotalAnnuel = salaireAnnuelNet + indemniteCPAnnuelle + entretienAnnuel;
        return {
            heuresSemaine, tarifHoraireBrut, semainesAnnualisees, semainesContrat, salaireMensuelNet, salaireMensuelBrut, salaireAnnuelNet, heuresMensualisees,
            joursActiviteMensualises, indemniteCPAnnuelle, joursAcquis, indemnite10pourcent, indemniteMaintien, coutTotalAnnuel, joursTravailles, entretienAnnuel
        };
    };

    const renderResultItem = (label, value, options = {}) => {
        const { formulaSymbol, formulaNumerical, isHighlighted = false, isFinal = false } = options;
        const hasFormula = !!formulaSymbol;
        
        const buttonHtml = hasFormula 
            ? `<button class="btn-icon details-btn" title="Afficher le détail du calcul">${ICONS.plusCircle}</button>`
            : ``;

        const dataRowClass = `data-row ${isHighlighted ? 'highlight' : ''} ${isFinal ? 'final-row' : ''}`;
        const dataRow = `
            <tr class="${dataRowClass}">
                <td class="label-col"><span>${label}</span></td>
                <td class="value-col"><strong>${value}</strong></td>
                <td class="button-col">${buttonHtml}</td>
            </tr>
        `;
        
        const formulaRow = hasFormula 
            ? `<tr class="formula-row hidden"><td colspan="3" class="p-0"><div class="formula-box">${formulaSymbol ? `\\[ ${formulaSymbol} \\]` : ''}${formulaNumerical ? `<br>\\[ ${formulaNumerical} \\]` : ''}</div></td></tr>`
            : '';

        return dataRow + formulaRow;
    };

    const runAndDisplayCalculations = (config) => {
        const metrics = calculateMetrics(config);
        currentMetrics = metrics;
        currentConfig = config;
        currentBaseNetSalary = metrics.salaireMensuelNet;
        currentAnnualCP = metrics.indemniteCPAnnuelle;

        const {
            coutTotalAnnuel, salaireAnnuelNet, indemniteCPAnnuelle, entretienAnnuel, joursTravailles, semainesAnnualisees, semainesContrat,
            tarifHoraireBrut, salaireMensuelNet, salaireMensuelBrut, heuresSemaine, heuresMensualisees, joursActiviteMensualises,
            joursAcquis, indemnite10pourcent, indemniteMaintien
        } = metrics;
        
        let sectionCounter = 1;

        const buildTable = (rows) => `<table class="result-table"><tbody>${rows.join('')}</tbody></table>`;
        
        // --- Build Input Summary for Printing ---
        const planningRows = workDays.map(day => {
            const p = config.planning[day];
            const time = (p && p.debut && p.fin) ? `${p.debut} - ${p.fin}` : 'Non travaillé';
            return `<tr><td>${day.charAt(0).toUpperCase() + day.slice(1)}</td><td class="text-right font-mono">${time}</td></tr>`;
        }).join('');
        
        const contractTypeStr = config.type_contrat === 'annee_complete' ? 'Année Complète' : 'Année Incomplète';
        const weeksStr = config.type_contrat === 'annee_incomplete' ? ` (${config.semaines_travaillees_par_an} semaines)` : '';

        printSummaryContainer.innerHTML = `
            <div class="result-card">
                <h3>Résumé des Données d'Entrée</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                    <div>
                        <h4 class="font-semibold text-gray-700 dark:text-gray-300 mb-2">Planning Hebdomadaire</h4>
                        <table class="w-full text-sm">
                           ${planningRows}
                        </table>
                    </div>
                    <div>
                        <h4 class="font-semibold text-gray-700 dark:text-gray-300 mb-2">Conditions du Contrat</h4>
                        <table class="w-full text-sm">
                            <tr><td>Type de contrat</td><td class="text-right font-mono">${contractTypeStr}${weeksStr}</td></tr>
                            <tr><td>Tarif horaire net</td><td class="text-right font-mono">${config.tarif_horaire_net.toFixed(2)} €</td></tr>
                            <tr><td>Indemnité d'entretien</td><td class="text-right font-mono">${config.frais_entretien_par_jour.toFixed(2)} € / jour</td></tr>
                            <tr><td>Date de début</td><td class="text-right font-mono">${new Date(config.date_debut_contrat + 'T00:00:00').toLocaleDateString('fr-FR')}</td></tr>
                        </table>
                    </div>
                </div>
            </div>
        `;


        let cpTable = '';
        if (config.type_contrat === 'annee_incomplete') {
            const cpRows = [
                renderResultItem('Jours ouvrables acquis / an', `${joursAcquis.toFixed(2)} jours`, { formulaSymbol: `\\frac{\\text{Sem. travaillées}}{4} \\times 2.5`, formulaNumerical: `\\frac{${semainesAnnualisees}}{4} \\times 2.5` }),
                renderResultItem('Indemnité (méthode 10%)', `${indemnite10pourcent.toFixed(2)} €`, { formulaSymbol: `\\text{Sal. Brut Annuel} \\times 0.10`, formulaNumerical: `${(salaireMensuelBrut * 12).toFixed(2)} \\times 0.10` }),
                renderResultItem('Indemnité (maintien de salaire)', `${indemniteMaintien.toFixed(2)} €`, { formulaSymbol: `\\frac{\\text{Jours Acquis}}{6} \\times \\text{H/Sem} \\times \\text{Tarif Brut}`, formulaNumerical: `\\frac{${joursAcquis.toFixed(2)}}{6} \\times ${heuresSemaine.toFixed(2)} \\times ${tarifHoraireBrut.toFixed(4)}` }),
                renderResultItem('Montant Annuel à Payer', `${indemniteCPAnnuelle.toFixed(2)} €`, { formulaSymbol: `\\max(\\text{10%}, \\text{Maintien})`, isHighlighted: true })
            ];
            cpTable = `<div class="result-card"><h3>${sectionCounter++}. Indemnités de Congés Payés</h3>${buildTable(cpRows)}</div>`;
        }

        const baseRows = [
            renderResultItem('Heures par semaine', `${heuresSemaine.toFixed(2)} h`, { formulaSymbol: `\\sum(\\text{Heures journalières})` }),
            renderResultItem('Tarif horaire NET', `${config.tarif_horaire_net.toFixed(2)} €`),
            renderResultItem('Tarif horaire BRUT', `${tarifHoraireBrut.toFixed(4)} €`, { formulaSymbol: `\\frac{\\text{Tarif Net}}{1 - \\text{Taux Cotis.}}`, formulaNumerical: `\\frac{${config.tarif_horaire_net.toFixed(2)}}{1 - ${TAUX_COTISATIONS}}` }),
            renderResultItem('Semaines d\'accueil / an', `${semainesAnnualisees} sem.`)
        ];
        
        const salaryRows = [
            renderResultItem('Salaire Mensuel BRUT', `${salaireMensuelBrut.toFixed(2)} €`, { formulaSymbol: `\\frac{\\text{Tarif Brut} \\times \\text{H/Sem} \\times \\text{N sem. contrat}}{12}`, formulaNumerical: `\\frac{${tarifHoraireBrut.toFixed(4)} \\times ${heuresSemaine.toFixed(2)} \\times ${semainesContrat}}{12}` }),
            renderResultItem('Salaire Mensuel NET', `${salaireMensuelNet.toFixed(2)} €`, { formulaSymbol: `\\text{Sal. Brut} \\times (1 - \\text{Taux Cotis.})`, formulaNumerical: `${salaireMensuelBrut.toFixed(2)} \\times (1 - ${TAUX_COTISATIONS})` })
        ];

        const pajemploiRows = [
            renderResultItem('Heures à déclarer / mois', `${Math.round(heuresMensualisees)} h`, {formulaSymbol: `\\frac{\\text{H/Sem} \\times \\text{N sem. contrat}}{12}`, formulaNumerical: `\\frac{${heuresSemaine.toFixed(2)} \\times ${semainesContrat}}{12}`}),
            renderResultItem('Jours d\'activité / mois', `${Math.round(joursActiviteMensualises)} jours`, {formulaSymbol: `\\frac{\\text{Jours/sem} \\times \\text{Sem. accueil}}{12}`, formulaNumerical: `\\frac{${joursTravailles} \\times ${semainesAnnualisees}}{12}`})
        ];

        const maintenanceRows = [renderResultItem('Indemnité annuelle', `${entretienAnnuel.toFixed(2)} €`, { formulaSymbol: `(\\text{Jours/sem} \\times \\text{Sem. accueil}) \\times \\text{Frais/jour}`, formulaNumerical: `(${joursTravailles} \\times ${semainesAnnualisees}) \\times ${config.frais_entretien_par_jour.toFixed(2)}` })];

        const summaryRows = [
            renderResultItem('Salaire Net Annuel de base', `${salaireAnnuelNet.toFixed(2)} €`),
            renderResultItem('+ Indemnité CP Annuelle', `+ ${indemniteCPAnnuelle.toFixed(2)} €`),
            renderResultItem('+ Indemnités d\'Entretien Annuelles', `+ ${entretienAnnuel.toFixed(2)} €`),
            renderResultItem('COÛT TOTAL ANNUEL ESTIMÉ', `${coutTotalAnnuel.toFixed(2)} €`, { isFinal: true })
        ];

        baseResultsContainer.innerHTML = `
            <div class="result-card">
                <h3>${sectionCounter++}. Données de Base</h3>
                ${buildTable(baseRows)}
            </div>
            <div class="result-card">
                <h3>${sectionCounter++}. Salaire Mensuel de Base</h3>
                ${buildTable(salaryRows)}
                <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <h4 class="text-sm font-semibold mb-2 text-gray-600 dark:text-gray-400">Pour la déclaration Pajemploi</h4>
                    ${buildTable(pajemploiRows)}
                </div>
            </div>
            ${cpTable}
            <div class="result-card">
                <h3>${sectionCounter++}. Indemnités d'Entretien</h3>
                ${buildTable(maintenanceRows)}
            </div>
            <div class="result-card synthesis-card">
                <h3>${sectionCounter++}. Synthèse du Coût Annuel pour l'Employeur</h3>
                ${buildTable(summaryRows)}
            </div>
        `;
        
        joursAccueilMoisInput.value = '';
        monthlyResultsDisplay.classList.add('hidden');
        resultsContainer.classList.remove('hidden');
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    };

    const handleDetailsToggle = (e) => {
        const button = e.target.closest('.details-btn');
        if (!button) return;

        const dataRow = button.closest('.data-row');
        const formulaRow = dataRow.nextElementSibling;
        
        if (formulaRow && formulaRow.classList.contains('formula-row')) {
            const isHidden = formulaRow.classList.toggle('hidden');
            button.innerHTML = isHidden ? ICONS.plusCircle : ICONS.minusCircle;
            button.title = isHidden ? 'Afficher le détail du calcul' : 'Masquer le détail du calcul';

            if (!isHidden && window.MathJax) {
                MathJax.typesetPromise([formulaRow]);
            }
        }
    };
    
    const calculateMonthlyDeclaration = () => {
        const joursAccueil = parseInt(joursAccueilMoisInput.value, 10);
        const fraisEntretien = parseFloat(fraisEntretienInput.value);
        if (isNaN(joursAccueil) || joursAccueil < 0 || isNaN(fraisEntretien)) { monthlyResultsDisplay.classList.add('hidden'); return; }
        const cpMensuel = currentAnnualCP / 12;
        const totalIndemnites = joursAccueil * fraisEntretien;
        const netTotalAPayer = currentBaseNetSalary + totalIndemnites + cpMensuel;
        document.getElementById('res-decl-salaire-net').textContent = `${currentBaseNetSalary.toFixed(2)} €`;
        document.getElementById('res-decl-cp').textContent = `${cpMensuel.toFixed(2)} €`;
        document.getElementById('res-decl-entretien').textContent = `${totalIndemnites.toFixed(2)} €`;
        document.getElementById('res-decl-total').textContent = `${netTotalAPayer.toFixed(2)} €`;
        monthlyResultsDisplay.classList.remove('hidden');
    };
    
    const showEngagementModal = () => {
        if (!currentConfig.tarif_horaire_net) return;

        const renderItem = (label, value) => `
            <div class="engagement-item">
                <span>${label}</span>
                <strong>${value}</strong>
            </div>`;
        
        engagementTitle.textContent = `Synthèse pour le contrat : ${document.getElementById('session-name').value}`;

        engagementContent.innerHTML = `
            ${renderItem("Durée hebdomadaire de l'accueil", `${currentMetrics.heuresSemaine.toFixed(2)} heures / semaine`)}
            ${renderItem("Durée mensuelle de l'accueil", `${Math.round(currentMetrics.heuresMensualisees)} heures / mois`)}
            ${renderItem("Nombre de semaines d'accueil dans l'année", `${currentMetrics.semainesAnnualisees} semaines / an`)}
            <hr class="my-2 border-gray-300 dark:border-gray-600">
            ${renderItem("Salaire horaire brut", `${currentMetrics.tarifHoraireBrut.toFixed(4)} €`)}
            ${renderItem("Salaire mensuel brut de base", `${currentMetrics.salaireMensuelBrut.toFixed(2)} €`)}
            <hr class="my-2 border-gray-300 dark:border-gray-600">
            ${renderItem("Salaire horaire net", `${currentConfig.tarif_horaire_net.toFixed(2)} €`)}
            ${renderItem("Salaire mensuel net de base", `${currentMetrics.salaireMensuelNet.toFixed(2)} €`)}
        `;
        engagementModal.classList.remove('hidden');
    };

    const init = () => {
        document.getElementById('icon-add').innerHTML = ICONS.add;
        document.getElementById('icon-back').innerHTML = ICONS.back;
        document.getElementById('icon-print').innerHTML = ICONS.print;
        document.getElementById('icon-print-engagement').innerHTML = ICONS.print;
        document.getElementById('icon-compare').innerHTML = ICONS.compare;
        document.getElementById('icon-contract').innerHTML = ICONS.contract;
        
        const savedTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        applyTheme(savedTheme);
        
        themeToggleBtn.addEventListener('click', toggleTheme);
        newSessionBtn.addEventListener('click', () => showCalculatorScreen(true));
        backToHomeBtn.addEventListener('click', showHomeScreen);
        sessionList.addEventListener('click', handleSessionClick);
        planningGrid.addEventListener('click', handlePropagateDay);
        simForm.addEventListener('submit', handleFormSubmit);
        typeContratSelect.addEventListener('change', () => { semainesIncompleteGroup.classList.toggle('hidden', typeContratSelect.value !== 'annee_incomplete'); });
        
        printBtn.addEventListener('click', () => {
            bodyEl.classList.add('printing-report');
            window.print();
        });
        
        engagementBtn.addEventListener('click', showEngagementModal);
        closeEngagementModalBtn.addEventListener('click', () => engagementModal.classList.add('hidden'));
        printEngagementBtn.addEventListener('click', () => {
            bodyEl.classList.add('printing-engagement');
            window.print();
        });

        window.addEventListener('afterprint', () => {
            bodyEl.classList.remove('printing-report');
            bodyEl.classList.remove('printing-engagement');
        });

        joursAccueilMoisInput.addEventListener('input', calculateMonthlyDeclaration);
        fraisEntretienInput.addEventListener('input', calculateMonthlyDeclaration);
        baseResultsContainer.addEventListener('click', handleDetailsToggle);
        compareBtn.addEventListener('click', handleCompare);
        closeModalBtn.addEventListener('click', () => comparisonModal.classList.add('hidden'));
        
        showHomeScreen();
    };

    init();
});