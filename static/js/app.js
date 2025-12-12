// Wowasi_ya Frontend Application
// API base URL
const API_BASE = '/api/v1';

// State management
let currentProject = null;
let currentStep = 1;
let discoveryData = null;
let generatedDocuments = [];

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadRecentProjects();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Project form submission
    document.getElementById('project-form').addEventListener('submit', handleProjectSubmit);

    // Privacy consent checkbox
    document.getElementById('privacy-consent').addEventListener('change', (e) => {
        document.getElementById('approve-btn').disabled = !e.target.checked;
    });

    // Close modal on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

    // Close modal on backdrop click
    document.getElementById('modal').addEventListener('click', (e) => {
        if (e.target.id === 'modal') closeModal();
    });
}

// Check API health
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        if (data.status === 'healthy') {
            updateStatus('Connected', 'green');
        } else {
            updateStatus('Degraded', 'yellow');
        }
    } catch (error) {
        updateStatus('Disconnected', 'red');
        showToast('Unable to connect to server', 'error');
    }
}

// Update connection status indicator
function updateStatus(text, color) {
    const indicator = document.getElementById('status-indicator');
    const colorClasses = {
        green: 'text-green-400',
        yellow: 'text-yellow-400',
        red: 'text-red-400'
    };
    const dotClasses = {
        green: 'bg-green-400',
        yellow: 'bg-yellow-400',
        red: 'bg-red-400'
    };
    indicator.className = `flex items-center text-sm ${colorClasses[color]}`;
    indicator.innerHTML = `
        <span class="w-2 h-2 ${dotClasses[color]} rounded-full mr-2 pulse-dot"></span>
        ${text}
    `;
}

// Load recent projects
async function loadRecentProjects() {
    try {
        const response = await fetch(`${API_BASE}/projects`);
        if (!response.ok) return;

        const projects = await response.json();
        const container = document.getElementById('recent-projects');

        if (projects.length === 0) {
            container.innerHTML = `
                <div class="text-slate-500 text-sm col-span-full text-center py-8">
                    <i class="fas fa-folder-open text-4xl mb-3 block opacity-50"></i>
                    No projects yet. Create your first one above!
                </div>
            `;
            return;
        }

        container.innerHTML = projects.slice(0, 6).map(project => `
            <div class="bg-slate-900 rounded-lg p-4 cursor-pointer card-hover transition-all duration-300"
                 onclick="loadProject('${project.id}')">
                <div class="flex items-start justify-between mb-2">
                    <h4 class="font-medium truncate">${escapeHtml(project.name)}</h4>
                    <span class="text-xs px-2 py-1 rounded ${getStatusClass(project.status)}">${project.status}</span>
                </div>
                <p class="text-sm text-slate-400 line-clamp-2">${escapeHtml(project.description?.substring(0, 100) || '')}</p>
                <p class="text-xs text-slate-500 mt-2">${formatDate(project.created_at)}</p>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load projects:', error);
    }
}

// Handle project form submission
async function handleProjectSubmit(e) {
    e.preventDefault();

    const name = document.getElementById('project-name').value.trim();
    const area = document.getElementById('project-area').value;
    const description = document.getElementById('project-description').value.trim();

    if (!name || !description) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...';

    try {
        // Create project
        const response = await fetch(`${API_BASE}/projects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, area, description })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create project');
        }

        const projectResponse = await response.json();
        // Normalize - API returns project_id, we use id
        currentProject = {
            ...projectResponse,
            id: projectResponse.project_id || projectResponse.id
        };
        console.log('Created project:', currentProject);

        // Get discovery results
        await loadDiscovery(currentProject.id);

        showToast('Project analyzed successfully', 'success');
        setStep(2);
        showDiscovery();

    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Analyze Project</span><i class="fas fa-arrow-right ml-2"></i>';
    }
}

// Load discovery results
async function loadDiscovery(projectId) {
    try {
        const response = await fetch(`${API_BASE}/projects/${projectId}/discovery`);
        if (!response.ok) throw new Error('Failed to load discovery');

        discoveryData = await response.json();
        renderDiscovery();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Render discovery results
function renderDiscovery() {
    if (!discoveryData) return;

    // Domains
    const domainsList = document.getElementById('domains-list');
    const domains = discoveryData.domains || [];
    domainsList.innerHTML = domains.length ? domains.map(d => `
        <div class="flex items-center bg-slate-800 rounded px-3 py-2">
            <i class="fas fa-tag text-blue-400 mr-2"></i>
            <span>${escapeHtml(d)}</span>
        </div>
    `).join('') : '<p class="text-slate-500 text-sm">No domains identified</p>';

    // Stakeholders
    const stakeholdersList = document.getElementById('stakeholders-list');
    const stakeholders = discoveryData.stakeholders || [];
    stakeholdersList.innerHTML = stakeholders.length ? stakeholders.map(s => `
        <div class="flex items-center bg-slate-800 rounded px-3 py-2">
            <i class="fas fa-user text-green-400 mr-2"></i>
            <span>${escapeHtml(s)}</span>
        </div>
    `).join('') : '<p class="text-slate-500 text-sm">No stakeholders identified</p>';

    // Agents
    const agentsList = document.getElementById('agents-list');
    const agents = discoveryData.agents || [];
    agentsList.innerHTML = agents.length ? agents.map(a => `
        <div class="bg-slate-800 rounded px-3 py-2">
            <div class="flex items-center mb-1">
                <i class="fas fa-robot text-purple-400 mr-2"></i>
                <span class="font-medium">${escapeHtml(a.name || a)}</span>
            </div>
            ${a.description ? `<p class="text-xs text-slate-400">${escapeHtml(a.description)}</p>` : ''}
        </div>
    `).join('') : '<p class="text-slate-500 text-sm">No agents generated</p>';
}

// Show privacy review
function showPrivacyReview() {
    setStep(3);

    // Render privacy flags
    const flagsContainer = document.getElementById('privacy-flags');
    const noIssues = document.getElementById('no-privacy-issues');
    const flags = discoveryData?.privacy_flags || [];

    if (flags.length === 0) {
        flagsContainer.classList.add('hidden');
        noIssues.classList.remove('hidden');
    } else {
        flagsContainer.classList.remove('hidden');
        noIssues.classList.add('hidden');
        flagsContainer.innerHTML = flags.map(flag => `
            <div class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <div class="flex items-start">
                    <i class="fas fa-exclamation-triangle text-yellow-400 mr-3 mt-1"></i>
                    <div>
                        <h4 class="font-medium text-yellow-400">${escapeHtml(flag.type || 'Potential PII')}</h4>
                        <p class="text-sm text-slate-400">${escapeHtml(flag.text || flag)}</p>
                        <p class="text-xs text-slate-500 mt-1">Confidence: ${(flag.confidence * 100 || 80).toFixed(0)}%</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Sanitized preview
    document.getElementById('sanitized-preview').textContent =
        discoveryData?.sanitized_description || currentProject?.description || '';

    // Show section
    document.getElementById('section-input').classList.add('hidden');
    document.getElementById('section-discovery').classList.add('hidden');
    document.getElementById('section-privacy').classList.remove('hidden');
    document.getElementById('section-results').classList.add('hidden');
}

// Start document generation
async function startGeneration() {
    if (!currentProject) return;

    setStep(4);
    document.getElementById('section-input').classList.add('hidden');
    document.getElementById('section-discovery').classList.add('hidden');
    document.getElementById('section-privacy').classList.add('hidden');
    document.getElementById('section-results').classList.remove('hidden');

    // Initialize folder tree and activity log
    initializeFolderTree();
    addActivity('Starting document generation...', 'info');

    try {
        // Approve project
        const approveResponse = await fetch(`${API_BASE}/projects/${currentProject.id}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approved: true, use_sanitized: true })
        });

        if (!approveResponse.ok) {
            const err = await approveResponse.json().catch(() => ({}));
            throw new Error(err.detail || 'Failed to approve project');
        }

        addActivity('Project approved, beginning generation', 'success');

        // Poll for status
        pollGenerationStatus();

    } catch (error) {
        addActivity(`Error: ${error.message}`, 'error');
        showToast(error.message, 'error');
    }
}

// Initialize folder tree structure
function initializeFolderTree() {
    const area = document.getElementById('project-area')?.value || '04_Iyeska';
    const projectName = document.getElementById('project-name')?.value || currentProject?.input?.name || 'Project';
    const areaDisplay = area.replace(/^\d+_/, ''); // Remove number prefix for display

    const treeContainer = document.getElementById('folder-tree');
    treeContainer.innerHTML = `
        <div class="text-slate-400">
            <div class="flex items-center">
                <i class="fas fa-folder text-yellow-400 mr-2"></i>
                <span>${escapeHtml(areaDisplay)}</span>
            </div>
            <div class="ml-4 border-l border-slate-700 pl-3 mt-1">
                <div class="flex items-center" id="tree-project">
                    <i class="fas fa-folder-open text-yellow-400 mr-2"></i>
                    <span class="text-white font-medium">${escapeHtml(projectName)}</span>
                    <i class="fas fa-spinner fa-spin text-blue-400 ml-2 text-xs"></i>
                </div>
                <div class="ml-4 border-l border-slate-700 pl-3 mt-1 space-y-1" id="tree-folders">
                    ${['00-Overview', '10-Discovery', '20-Planning', '30-Execution', '40-Comms', '90-Archive'].map(folder => `
                        <div class="flex items-center text-slate-500" id="tree-folder-${folder}">
                            <i class="fas fa-folder mr-2"></i>
                            <span>${folder}</span>
                            <span class="ml-2 text-xs" id="tree-folder-count-${folder}"></span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

// Update folder in tree (mark as created/populated)
function updateFolderTree(folder, docCount) {
    const folderEl = document.getElementById(`tree-folder-${folder}`);
    if (folderEl) {
        folderEl.classList.remove('text-slate-500');
        folderEl.classList.add('text-green-400');
        folderEl.querySelector('i').classList.remove('fa-folder');
        folderEl.querySelector('i').classList.add('fa-folder-open');

        const countEl = document.getElementById(`tree-folder-count-${folder}`);
        if (countEl) {
            countEl.textContent = `(${docCount} file${docCount !== 1 ? 's' : ''})`;
            countEl.classList.add('text-green-400');
        }
    }
}

// Add file to folder tree
function addFileToTree(folder, filename) {
    const foldersContainer = document.getElementById('tree-folders');
    const folderEl = document.getElementById(`tree-folder-${folder}`);

    if (folderEl && foldersContainer) {
        // Check if file already exists
        if (document.getElementById(`tree-file-${filename}`)) return;

        // Create file entry
        const fileEntry = document.createElement('div');
        fileEntry.id = `tree-file-${filename}`;
        fileEntry.className = 'flex items-center text-green-400 ml-4 fade-in';
        fileEntry.innerHTML = `
            <i class="fas fa-file-alt mr-2 text-xs"></i>
            <span class="text-xs">${escapeHtml(filename)}</span>
            <i class="fas fa-check text-green-400 ml-2 text-xs"></i>
        `;

        // Insert after the folder
        folderEl.parentNode.insertBefore(fileEntry, folderEl.nextSibling);

        // Update folder appearance
        folderEl.classList.remove('text-slate-500');
        folderEl.classList.add('text-yellow-400');
        folderEl.querySelector('i').classList.remove('fa-folder');
        folderEl.querySelector('i').classList.add('fa-folder-open');
    }
}

// Add activity log entry
function addActivity(message, type = 'info') {
    const logContainer = document.getElementById('activity-log');
    if (!logContainer) return;

    const colors = {
        info: 'text-blue-400',
        success: 'text-green-400',
        warning: 'text-yellow-400',
        error: 'text-red-400'
    };

    const icons = {
        info: 'fa-info-circle',
        success: 'fa-check-circle',
        warning: 'fa-exclamation-circle',
        error: 'fa-times-circle'
    };

    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `flex items-start ${colors[type]} fade-in`;
    entry.innerHTML = `
        <i class="fas ${icons[type]} mr-2 mt-0.5"></i>
        <span class="text-slate-500 mr-2">[${timestamp}]</span>
        <span>${escapeHtml(message)}</span>
    `;

    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Poll generation status
let lastDocCount = 0;
let seenDocuments = new Set();

async function pollGenerationStatus() {
    const statusEl = document.getElementById('generation-status');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const documentsGrid = document.getElementById('documents-grid');

    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE}/projects/${currentProject.id}/status`);
            if (!response.ok) throw new Error('Failed to get status');

            const status = await response.json();

            // Update progress
            const docCount = status.documents_completed || 0;
            const progress = (docCount / 15) * 100;
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `${docCount} / 15 documents`;
            statusEl.textContent = status.message || 'Generating...';

            // Log activity for new documents
            if (docCount > lastDocCount) {
                addActivity(`Generated ${docCount - lastDocCount} new document(s)`, 'success');
                lastDocCount = docCount;
            }

            // Update folder tree and documents grid
            if (status.documents && status.documents.length > 0) {
                // Track folders with documents
                const folderDocs = {};

                status.documents.forEach(doc => {
                    const folder = doc.folder || '00-Overview';
                    const filename = doc.filename || doc.name + '.md';

                    // Track by folder
                    if (!folderDocs[folder]) folderDocs[folder] = [];
                    folderDocs[folder].push(filename);

                    // Add new files to tree and log
                    if (!seenDocuments.has(filename)) {
                        seenDocuments.add(filename);
                        addFileToTree(folder, filename);
                        addActivity(`Created ${folder}/${filename}`, 'success');
                    }
                });

                // Update folder counts
                Object.entries(folderDocs).forEach(([folder, files]) => {
                    updateFolderTree(folder, files.length);
                });

                // Update documents grid
                documentsGrid.innerHTML = status.documents.map(doc => `
                    <div class="bg-slate-900 rounded-lg p-4 cursor-pointer card-hover transition-all"
                         onclick="viewDocument('${escapeHtml(doc.name)}', \`${escapeHtml(doc.content || '')}\`)">
                        <div class="flex items-center mb-2">
                            <i class="fas fa-file-alt text-green-400 mr-2"></i>
                            <span class="font-medium">${escapeHtml(doc.name)}</span>
                        </div>
                        <p class="text-xs text-slate-400">${escapeHtml(doc.folder || '00-Overview')}</p>
                    </div>
                `).join('');
            }

            // Continue polling or finish
            if (status.status === 'completed') {
                statusEl.textContent = 'All documents generated!';
                addActivity('All 15 documents generated successfully!', 'success');
                addActivity('Syncing to Obsidian vault...', 'info');

                // Remove spinner from project folder
                const projectEl = document.getElementById('tree-project');
                if (projectEl) {
                    const spinner = projectEl.querySelector('.fa-spinner');
                    if (spinner) {
                        spinner.classList.remove('fa-spinner', 'fa-spin');
                        spinner.classList.add('fa-check');
                    }
                }

                document.getElementById('results-actions').classList.remove('hidden');
                loadGeneratedDocuments();
                showToast('Documentation generated successfully!', 'success');

                setTimeout(() => {
                    addActivity('Sync complete - files available in Google Drive', 'success');
                }, 3000);

            } else if (status.status === 'failed') {
                statusEl.textContent = 'Generation failed';
                addActivity('Document generation failed', 'error');
                showToast('Document generation failed', 'error');
            } else {
                setTimeout(poll, 2000);
            }

        } catch (error) {
            console.error('Poll error:', error);
            addActivity(`Polling error: ${error.message}`, 'warning');
            setTimeout(poll, 3000);
        }
    };

    // Reset tracking for new generation
    lastDocCount = 0;
    seenDocuments = new Set();

    poll();
}

// Load generated documents
async function loadGeneratedDocuments() {
    try {
        const response = await fetch(`${API_BASE}/projects/${currentProject.id}/result`);
        if (!response.ok) return;

        const result = await response.json();
        generatedDocuments = result.documents || [];

        const documentsGrid = document.getElementById('documents-grid');
        documentsGrid.innerHTML = generatedDocuments.map(doc => `
            <div class="bg-slate-900 rounded-lg p-4 cursor-pointer card-hover transition-all"
                 onclick="viewDocument('${escapeHtml(doc.name)}', '${doc.id}')">
                <div class="flex items-center mb-2">
                    <i class="fas fa-file-alt text-green-400 mr-2"></i>
                    <span class="font-medium">${escapeHtml(doc.name)}</span>
                </div>
                <p class="text-xs text-slate-400">${escapeHtml(doc.category || '')}</p>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

// View document in modal
function viewDocument(name, contentOrId) {
    document.getElementById('modal-title').textContent = name;
    const content = document.querySelector('#modal-content pre');

    // If it's an ID, find the document
    const doc = generatedDocuments.find(d => d.id === contentOrId);
    content.textContent = doc?.content || contentOrId || 'Document content not available';

    document.getElementById('modal').classList.remove('hidden');
}

// Close modal
function closeModal() {
    document.getElementById('modal').classList.add('hidden');
}

// Copy document content
function copyDocument() {
    const content = document.querySelector('#modal-content pre').textContent;
    navigator.clipboard.writeText(content);
    showToast('Copied to clipboard', 'success');
}

// Download single document
function downloadDocument() {
    const title = document.getElementById('modal-title').textContent;
    const content = document.querySelector('#modal-content pre').textContent;
    downloadFile(`${title}.md`, content);
}

// Download all documents
function downloadAll() {
    generatedDocuments.forEach(doc => {
        downloadFile(`${doc.name}.md`, doc.content);
    });
    showToast('Downloading all documents', 'success');
}

// Download file helper
function downloadFile(filename, content) {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

// Start new project
function startNew() {
    currentProject = null;
    discoveryData = null;
    generatedDocuments = [];

    document.getElementById('project-form').reset();
    document.getElementById('privacy-consent').checked = false;
    document.getElementById('approve-btn').disabled = true;

    setStep(1);
    document.getElementById('section-input').classList.remove('hidden');
    document.getElementById('section-discovery').classList.add('hidden');
    document.getElementById('section-privacy').classList.add('hidden');
    document.getElementById('section-results').classList.add('hidden');

    loadRecentProjects();
}

// Navigation helpers
function showDiscovery() {
    document.getElementById('section-input').classList.add('hidden');
    document.getElementById('section-discovery').classList.remove('hidden');
    document.getElementById('section-privacy').classList.add('hidden');
    document.getElementById('section-results').classList.add('hidden');
}

function goBack() {
    if (currentStep === 2) {
        setStep(1);
        document.getElementById('section-input').classList.remove('hidden');
        document.getElementById('section-discovery').classList.add('hidden');
    } else if (currentStep === 3) {
        setStep(2);
        document.getElementById('section-discovery').classList.remove('hidden');
        document.getElementById('section-privacy').classList.add('hidden');
    }
}

// Load existing project
async function loadProject(projectId) {
    try {
        const response = await fetch(`${API_BASE}/projects/${projectId}`);
        if (!response.ok) throw new Error('Project not found');

        const projectResponse = await response.json();
        // Normalize - API uses project_id in some places, id in others
        currentProject = {
            ...projectResponse,
            id: projectResponse.project_id || projectResponse.id
        };

        if (currentProject.status === 'completed') {
            setStep(4);
            document.getElementById('section-input').classList.add('hidden');
            document.getElementById('section-results').classList.remove('hidden');
            document.getElementById('progress-section').classList.add('hidden');
            document.getElementById('results-actions').classList.remove('hidden');
            document.getElementById('generation-status').textContent = 'Documents ready';
            loadGeneratedDocuments();
        } else {
            await loadDiscovery(projectId);
            setStep(2);
            showDiscovery();
        }

    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Update step indicator
function setStep(step) {
    currentStep = step;
    for (let i = 1; i <= 4; i++) {
        const el = document.getElementById(`step-${i}`);
        const circle = el.querySelector('div');

        if (i < step) {
            el.classList.remove('opacity-50');
            circle.className = 'w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-sm font-bold';
            circle.innerHTML = '<i class="fas fa-check"></i>';
        } else if (i === step) {
            el.classList.remove('opacity-50');
            circle.className = 'w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-sm font-bold';
            circle.textContent = i;
        } else {
            el.classList.add('opacity-50');
            circle.className = 'w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm font-bold';
            circle.textContent = i;
        }
    }
}

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-yellow-500'
    };
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle',
        warning: 'fa-exclamation-triangle'
    };

    const toast = document.createElement('div');
    toast.className = `${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center space-x-2 fade-in`;
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function getStatusClass(status) {
    const classes = {
        pending: 'bg-slate-600 text-slate-200',
        processing: 'bg-blue-500/20 text-blue-400',
        completed: 'bg-green-500/20 text-green-400',
        failed: 'bg-red-500/20 text-red-400'
    };
    return classes[status] || classes.pending;
}
