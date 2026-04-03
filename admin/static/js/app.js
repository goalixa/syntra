/**
 * Syntra Admin Panel Application
 * Handles authentication, navigation, and API communication
 */

class SyntraAdmin {
  constructor() {
    this.apiBase = window.location.origin;
    this.isAuthenticated = false;
    this.currentUser = null;
    this.token = null;
    this.currentView = 'overview';

    this.init();
  }

  init() {
    // Skip auth - go directly to dashboard
    this.isAuthenticated = true;
    this.currentUser = { name: 'Admin User', role: 'Administrator' };
    this.showDashboard();
    this.bindEvents();
    this.setupRefreshInterval();
  }

  // Authentication
  async checkAuth() {
    const token = localStorage.getItem('syntra_token');
    const user = localStorage.getItem('syntra_user');

    if (token && user) {
      try {
        this.token = token;
        this.currentUser = JSON.parse(user);
        this.isAuthenticated = true;
        this.showDashboard();
      } catch (e) {
        this.logout();
      }
    } else {
      this.showAuthScreen();
    }
  }

  async authenticate() {
    const authButton = document.getElementById('auth-button');
    const statusText = document.querySelector('#auth-status .status-text');
    const statusIndicator = document.querySelector('.status-indicator');

    try {
      authButton.disabled = true;
      authButton.innerHTML = '<span class="spinner"></span> Authenticating...';
      statusText.textContent = 'Connecting to Syntra...';

      // Call authentication endpoint
      const response = await fetch(`${this.apiBase}/api/admin/auth`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const data = await response.json();

      this.token = data.token;
      this.currentUser = data.user;
      this.isAuthenticated = true;

      localStorage.setItem('syntra_token', this.token);
      localStorage.setItem('syntra_user', JSON.stringify(this.currentUser));

      statusText.textContent = 'Authenticated';
      statusIndicator.classList.add('connected');

      setTimeout(() => this.showDashboard(), 500);

    } catch (error) {
      console.error('Auth error:', error);
      statusText.textContent = 'Authentication failed';
      authButton.disabled = false;
      authButton.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10 2L2 10L10 18M18 10H2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Retry Authentication
      `;
    }
  }

  logout() {
    localStorage.removeItem('syntra_token');
    localStorage.removeItem('syntra_user');
    this.token = null;
    this.currentUser = null;
    this.isAuthenticated = false;
    this.showAuthScreen();
  }

  // Screen Management
  showAuthScreen() {
    document.getElementById('auth-screen').classList.add('active');
    document.getElementById('dashboard-screen').classList.remove('active');
  }

  showDashboard() {
    document.getElementById('auth-screen').classList.remove('active');
    document.getElementById('dashboard-screen').classList.add('active');
    this.updateUserInfo();
    this.loadView(this.currentView);
  }

  updateUserInfo() {
    if (this.currentUser) {
      document.getElementById('user-name').textContent = this.currentUser.name || 'Admin User';
      document.getElementById('user-initials').textContent = (this.currentUser.name || 'A')[0].toUpperCase();
    }
  }

  // Navigation
  bindEvents() {
    // Auth button
    document.getElementById('auth-button').addEventListener('click', () => this.authenticate());

    // Logout button
    document.getElementById('logout-button').addEventListener('click', () => this.logout());

    // Navigation items
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        const view = e.currentTarget.dataset.view;
        this.navigateTo(view);
      });
    });

    // Refresh button
    document.getElementById('refresh-button').addEventListener('click', () => this.refreshCurrentView());
  }

  navigateTo(view) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.view === view);
    });

    this.currentView = view;
    this.loadView(view);
  }

  async loadView(view) {
    const contentArea = document.getElementById('content-area');
    const pageTitle = document.getElementById('page-title');

    contentArea.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
      switch (view) {
        case 'overview':
          pageTitle.textContent = 'Overview';
          await this.loadOverview(contentArea);
          break;
        case 'agents':
          pageTitle.textContent = 'Agents';
          await this.loadAgents(contentArea);
          break;
        case 'config':
          pageTitle.textContent = 'Configuration';
          await this.loadConfig(contentArea);
          break;
        case 'logs':
          pageTitle.textContent = 'Activity Logs';
          await this.loadLogs(contentArea);
          break;
      }
    } catch (error) {
      contentArea.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⚠️</div>
          <div class="empty-state-title">Failed to load content</div>
          <p>${error.message}</p>
        </div>
      `;
    }
  }

  refreshCurrentView() {
    this.loadView(this.currentView);
  }

  // API Calls
  async apiCall(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.apiBase}${endpoint}`, {
      ...options,
      headers
    });

    if (response.status === 401) {
      this.logout();
      throw new Error('Session expired');
    }

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  // View Loaders
  async loadOverview(container) {
    try {
      const data = await this.apiCall('/api/admin/overview');
      this.renderOverview(container, data);
    } catch (error) {
      this.renderOverview(container, this.getMockOverview());
    }
  }

  renderOverview(container, data) {
    container.innerHTML = `
      <div class="dashboard-grid">
        <div class="stat-card">
          <div class="stat-card-header">
            <span class="stat-card-title">Total Tasks</span>
            <svg class="stat-card-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="stat-card-value">${data.totalTasks || 0}</div>
          <div class="stat-card-change positive">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 4v8M4 8h8" stroke="currentColor" stroke-width="2"/>
            </svg>
            +${data.taskGrowth || 12}% from last week
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-card-header">
            <span class="stat-card-title">Active Agents</span>
            <svg class="stat-card-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
              <path d="M4 20c0-4.42 3.58-8 8-8s8 3.58 8 8" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="stat-card-value">${data.activeAgents || 4}</div>
          <div class="stat-card-change">
            All systems operational
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-card-header">
            <span class="stat-card-title">Success Rate</span>
            <svg class="stat-card-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="stat-card-value">${data.successRate || 98.5}%</div>
          <div class="stat-card-change positive">
            ${data.successRateChange || '+0.3%'} from last week
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-card-header">
            <span class="stat-card-title">Avg Response Time</span>
            <svg class="stat-card-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="stat-card-value">${data.avgResponseTime || '2.3s'}</div>
          <div class="stat-card-change positive">
            ${data.responseTimeChange || '-0.2s'} from last week
          </div>
        </div>
      </div>

      <div class="section-card">
        <div class="section-card-header">
          <h2 class="section-card-title">Recent Activity</h2>
        </div>
        <div class="section-card-content">
          ${this.renderRecentActivity(data.recentActivity || [])}
        </div>
      </div>
    `;
  }

  renderRecentActivity(activities) {
    if (activities.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-state-icon">📋</div>
          <div class="empty-state-title">No recent activity</div>
          <p>Activity will appear here as you use Syntra</p>
        </div>
      `;
    }

    return activities.map(activity => `
      <div class="log-entry">
        <div class="log-time">${this.formatTime(activity.timestamp)}</div>
        <div class="log-content">
          <div class="log-message">${activity.message}</div>
          <div class="log-meta">${activity.agent} • ${activity.duration}</div>
        </div>
      </div>
    `).join('');
  }

  async loadAgents(container) {
    try {
      const data = await this.apiCall('/api/admin/agents');
      this.renderAgents(container, data);
    } catch (error) {
      this.renderAgents(container, this.getMockAgents());
    }
  }

  renderAgents(container, data) {
    container.innerHTML = `
      <div class="section-card">
        <div class="section-card-header">
          <h2 class="section-card-title">Agent Status</h2>
        </div>
        <div class="section-card-content">
          <div class="agent-grid">
            ${data.agents.map(agent => `
              <div class="agent-card" data-agent="${agent.name}">
                <div class="agent-card-header">
                  <div class="agent-card-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                      <path d="M4 20c0-4.42 3.58-8 8-8s8 3.58 8 8" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <span class="agent-card-name">${agent.name}</span>
                  <span class="agent-card-status">${agent.status}</span>
                </div>
                <p class="agent-card-description">${agent.description}</p>
                <div class="agent-card-stats">
                  <span>Tasks: ${agent.tasksCompleted}</span>
                  <span>Success: ${agent.successRate}%</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  async loadConfig(container) {
    try {
      const data = await this.apiCall('/api/admin/config');
      this.renderConfig(container, data);
    } catch (error) {
      this.renderConfig(container, this.getMockConfig());
    }
  }

  renderConfig(container, data) {
    container.innerHTML = `
      <div class="section-card">
        <div class="section-card-header">
          <h2 class="section-card-title">Syntra Configuration</h2>
        </div>
        <div class="section-card-content">
          <form id="config-form">
            <div class="form-group">
              <label class="form-label">LLM Model</label>
              <select class="form-select" name="model">
                <option value="claude" ${data.model === 'claude' ? 'selected' : ''}>Claude (Anthropic)</option>
                <option value="gpt-4" ${data.model === 'gpt-4' ? 'selected' : ''}>GPT-4 (OpenAI)</option>
                <option value="gpt-3.5-turbo" ${data.model === 'gpt-3.5-turbo' ? 'selected' : ''}>GPT-3.5 Turbo</option>
              </select>
              <p class="form-hint">Select the primary language model for AI operations</p>
            </div>

            <div class="form-group">
              <label class="form-label">Default Kubernetes Namespace</label>
              <input type="text" class="form-input" name="namespace" value="${data.namespace || 'default'}">
              <p class="form-hint">Default namespace for Kubernetes operations</p>
            </div>

            <div class="form-group">
              <label class="form-label">Agent Timeout (seconds)</label>
              <input type="number" class="form-input" name="timeout" value="${data.timeout || 300}" min="30" max="3600">
              <p class="form-hint">Maximum time to wait for agent completion</p>
            </div>

            <div class="form-group">
              <label class="form-label">Enable Debug Logging</label>
              <select class="form-select" name="debug">
                <option value="true" ${data.debug === true ? 'selected' : ''}>Enabled</option>
                <option value="false" ${data.debug === false ? 'selected' : ''}>Disabled</option>
              </select>
              <p class="form-hint">Enable detailed logging for troubleshooting</p>
            </div>

            <div class="form-group">
              <label class="form-label">Custom System Prompt</label>
              <textarea class="form-textarea" name="systemPrompt" placeholder="Enter custom system instructions...">${data.systemPrompt || ''}</textarea>
              <p class="form-hint">Additional instructions for the AI agents</p>
            </div>

            <button type="submit" class="btn-primary">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M16 10l-6-6v4H4v4h6v4l6-6z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Save Configuration
            </button>
          </form>
        </div>
      </div>
    `;

    // Bind form submission
    document.getElementById('config-form').addEventListener('submit', (e) => this.saveConfig(e));
  }

  async saveConfig(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const config = Object.fromEntries(formData.entries());

    try {
      await this.apiCall('/api/admin/config', {
        method: 'POST',
        body: JSON.stringify(config)
      });

      // Show success message
      const button = event.target.querySelector('button[type="submit"]');
      const originalText = button.innerHTML;
      button.innerHTML = '✓ Configuration Saved';
      button.style.background = 'var(--color-success)';

      setTimeout(() => {
        button.innerHTML = originalText;
        button.style.background = '';
      }, 2000);

    } catch (error) {
      alert('Failed to save configuration: ' + error.message);
    }
  }

  async loadLogs(container) {
    try {
      const data = await this.apiCall('/api/admin/logs?limit=50');
      this.renderLogs(container, data);
    } catch (error) {
      this.renderLogs(container, this.getMockLogs());
    }
  }

  renderLogs(container, data) {
    container.innerHTML = `
      <div class="section-card">
        <div class="section-card-header">
          <h2 class="section-card-title">Activity Logs</h2>
        </div>
        <div class="section-card-content">
          ${data.logs.map(log => `
            <div class="log-entry">
              <div class="log-time">${this.formatTime(log.timestamp)}</div>
              <div class="log-content">
                <div class="log-message">${log.message}</div>
                <div class="log-meta">
                  <span class="log-level log-level-${log.level.toLowerCase()}">${log.level}</span>
                  ${log.agent ? ` • ${log.agent}` : ''}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  // Mock Data (fallback when API is unavailable)
  getMockOverview() {
    return {
      totalTasks: 156,
      taskGrowth: 12,
      activeAgents: 4,
      successRate: 98.5,
      successRateChange: '+0.3%',
      avgResponseTime: '2.3s',
      responseTimeChange: '-0.2s',
      recentActivity: [
        { timestamp: Date.now() - 300000, message: 'Deployed Core-API v1.2.3 to production', agent: 'DevOps Agent', duration: '45s' },
        { timestamp: Date.now() - 900000, message: 'Investigated pod crash in auth-service', agent: 'Planner Agent', duration: '2m 15s' },
        { timestamp: Date.now() - 1800000, message: 'Code review completed for PR #234', agent: 'Reviewer Agent', duration: '1m 30s' }
      ]
    };
  }

  getMockAgents() {
    return {
      agents: [
        { name: 'Planner Agent', description: 'Breaks down complex tasks into executable steps', status: 'Active', tasksCompleted: 45, successRate: 98 },
        { name: 'DevOps Agent', description: 'Executes Kubernetes and infrastructure operations', status: 'Active', tasksCompleted: 78, successRate: 99 },
        { name: 'Reviewer Agent', description: 'Validates changes and provides feedback', status: 'Active', tasksCompleted: 33, successRate: 95 },
        { name: 'Evidence Collector', description: 'Gathers logs and diagnostic information', status: 'Active', tasksCompleted: 56, successRate: 100 }
      ]
    };
  }

  getMockConfig() {
    return {
      model: 'claude',
      namespace: 'production',
      timeout: 300,
      debug: false,
      systemPrompt: ''
    };
  }

  getMockLogs() {
    const levels = ['INFO', 'SUCCESS', 'WARNING', 'ERROR'];
    const messages = [
      'Task completed successfully',
      'Kubernetes pod restarted',
      'Configuration updated',
      'Agent task timed out',
      'Authentication verified',
      'Deployment initiated'
    ];
    const agents = ['Planner Agent', 'DevOps Agent', 'Reviewer Agent', 'System'];

    return {
      logs: Array.from({ length: 20 }, (_, i) => ({
        timestamp: Date.now() - (i * 300000),
        level: levels[Math.floor(Math.random() * levels.length)],
        message: messages[Math.floor(Math.random() * messages.length)],
        agent: agents[Math.floor(Math.random() * agents.length)]
      }))
    };
  }

  // Utilities
  formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  setupRefreshInterval() {
    // Refresh connection status every 30 seconds
    setInterval(() => this.checkConnection(), 30000);
  }

  async checkConnection() {
    const statusElement = document.getElementById('connection-status');
    try {
      await this.apiCall('/health');
      statusElement.innerHTML = '<span class="status-dot status-dot-connected"></span> Connected';
    } catch (error) {
      statusElement.innerHTML = '<span class="status-dot status-dot-disconnected"></span> Disconnected';
    }
  }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.syntraAdmin = new SyntraAdmin();
});
