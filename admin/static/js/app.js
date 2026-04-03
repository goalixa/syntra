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
        case 'users':
          pageTitle.textContent = 'Users';
          await this.loadUsers(contentArea);
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

  // ============================================================
  // USER MANAGEMENT
  // ============================================================

  async loadUsers(container) {
    try {
      const users = await this.apiCall('/api/admin/users');
      this.renderUsers(container, users);
    } catch (error) {
      this.showToast('Failed to load users', 'error');
      console.error(error);
    }
  }

  renderUsers(container, users) {
    this.currentUsers = users;

    container.innerHTML = `
      <div class="users-filters">
        <div class="filter-group">
          <input type="text" id="user-search" class="filter-input" placeholder="Search users...">
        </div>
        <select id="role-filter" class="filter-select">
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="developer">Developer</option>
          <option value="operator">Operator</option>
          <option value="viewer">Viewer</option>
        </select>
        <select id="status-filter" class="filter-select">
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="suspended">Suspended</option>
          <option value="pending">Pending</option>
        </select>
        <button id="add-user-btn" class="btn-add-user">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 4v12M4 10h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Add User
        </button>
      </div>

      <div class="users-table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Status</th>
              <th>Department</th>
              <th>Last Login</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="users-table-body">
            ${this.renderUserRows(users)}
          </tbody>
        </table>
      </div>
    `;

    // Bind filter events
    document.getElementById('user-search').addEventListener('input', (e) => this.filterUsers(e.target.value));
    document.getElementById('role-filter').addEventListener('change', () => this.applyFilters());
    document.getElementById('status-filter').addEventListener('change', () => this.applyFilters());
    document.getElementById('add-user-btn').addEventListener('click', () => this.showUserModal());
  }

  renderUserRows(users) {
    if (users.length === 0) {
      return `
        <tr>
          <td colspan="6" style="text-align: center; padding: 2rem; color: var(--color-text-muted);">
            No users found
          </td>
        </tr>
      `;
    }

    return users.map(user => `
      <tr data-user-id="${user.id}">
        <td>
          <div class="user-table-cell">
            <div class="user-table-avatar">${user.name[0].toUpperCase()}</div>
            <div class="user-table-info">
              <div class="user-table-name">${user.name}</div>
              <div class="user-table-email">${user.email}</div>
            </div>
          </div>
        </td>
        <td><span class="badge badge-${user.role}">${user.role}</span></td>
        <td><span class="badge badge-${user.status}">${user.status}</span></td>
        <td>${user.department || '-'}</td>
        <td>${user.last_login ? this.formatDate(user.last_login) : 'Never'}</td>
        <td>
          <div class="user-actions">
            <button class="btn-icon btn-icon-edit" onclick="syntraAdmin.viewUserDetail('${user.id}')" title="View Details">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 3L3 8l5 5M13 8H3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
            <button class="btn-icon btn-icon-edit" onclick="syntraAdmin.editUser('${user.id}')" title="Edit">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M2 11.5l8-8M11 2l3 3M2 14h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
            ${user.status === 'active' ? `
              <button class="btn-icon btn-icon-suspend" onclick="syntraAdmin.suspendUser('${user.id}')" title="Suspend">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M5 8h6" stroke="currentColor" stroke-width="1.5"/>
                </svg>
              </button>
            ` : `
              <button class="btn-icon" onclick="syntraAdmin.activateUser('${user.id}')" title="Activate" style="color: var(--color-success)">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </button>
            `}
            <button class="btn-icon btn-icon-delete" onclick="syntraAdmin.deleteUser('${user.id}')" title="Delete">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 5l6 6M11 5l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  filterUsers(searchTerm) {
    this.currentSearchTerm = searchTerm.toLowerCase();
    this.applyFilters();
  }

  applyFilters() {
    const roleFilter = document.getElementById('role-filter')?.value;
    const statusFilter = document.getElementById('status-filter')?.value;

    let filtered = this.currentUsers;

    if (this.currentSearchTerm) {
      filtered = filtered.filter(user =>
        user.name.toLowerCase().includes(this.currentSearchTerm) ||
        user.email.toLowerCase().includes(this.currentSearchTerm)
      );
    }

    if (roleFilter) {
      filtered = filtered.filter(user => user.role === roleFilter);
    }

    if (statusFilter) {
      filtered = filtered.filter(user => user.status === statusFilter);
    }

    const tbody = document.getElementById('users-table-body');
    if (tbody) {
      tbody.innerHTML = this.renderUserRows(filtered);
    }
  }

  async viewUserDetail(userId) {
    try {
      const [user, usage, apiKeys, accessLogs] = await Promise.all([
        this.apiCall(`/api/admin/users/${userId}`),
        this.apiCall(`/api/admin/users/${userId}/usage?period=daily`),
        this.apiCall(`/api/admin/users/${userId}/api-keys`),
        this.apiCall(`/api/admin/users/${userId}/access-logs?limit=20`)
      ]);

      this.renderUserDetail(user, usage, apiKeys, accessLogs);
    } catch (error) {
      this.showToast('Failed to load user details', 'error');
      console.error(error);
    }
  }

  renderUserDetail(user, usage, apiKeys, accessLogs) {
    const contentArea = document.getElementById('content-area');
    const pageTitle = document.getElementById('page-title');

    pageTitle.innerHTML = `
      <button onclick="syntraAdmin.loadUsers(document.getElementById('content-area'))" style="background: none; border: none; color: var(--color-text-muted); cursor: pointer; margin-right: 0.5rem;">
        ← Users
      </button>
      ${user.name}
    `;

    contentArea.innerHTML = `
      <div class="user-detail-header">
        <div class="user-detail-avatar-large">${user.name[0].toUpperCase()}</div>
        <div class="user-detail-info">
          <h2>${user.name}</h2>
          <div class="user-detail-email">${user.email}</div>
          <div class="user-detail-badges">
            <span class="badge badge-${user.role}">${user.role}</span>
            <span class="badge badge-${user.status}">${user.status}</span>
            ${user.department ? `<span class="badge badge-viewer">${user.department}</span>` : ''}
          </div>
        </div>
        <div style="margin-left: auto;">
          <button class="btn-primary" onclick="syntraAdmin.editUser('${user.id}')">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M2 11.5l8-8M11 2l3 3M2 14h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            Edit User
          </button>
        </div>
      </div>

      <div class="user-detail-tabs">
        <button class="user-detail-tab active" data-tab="overview">Overview</button>
        <button class="user-detail-tab" data-tab="usage">Usage</button>
        <button class="user-detail-tab" data-tab="api-keys">API Keys</button>
        <button class="user-detail-tab" data-tab="activity">Activity</button>
        <button class="user-detail-tab" data-tab="permissions">Permissions</button>
      </div>

      <div id="user-tab-content">
        ${this.renderUserOverviewTab(user, usage)}
      </div>
    `;

    this.currentUserDetail = { user, usage, apiKeys, accessLogs };

    // Bind tab events
    document.querySelectorAll('.user-detail-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        document.querySelectorAll('.user-detail-tab').forEach(t => t.classList.remove('active'));
        e.target.classList.add('active');
        this.loadUserTab(e.target.dataset.tab);
      });
    });
  }

  renderUserOverviewTab(user, usage) {
    return `
      <div class="usage-stats-grid">
        <div class="usage-stat">
          <div class="usage-stat-label">Total Requests (Today)</div>
          <div class="usage-stat-value">${usage.total_requests}</div>
          <div class="usage-stat-change ${usage.failed_requests > 0 ? 'negative' : 'positive'}">
            ${usage.failed_requests} failed
          </div>
        </div>
        <div class="usage-stat">
          <div class="usage-stat-label">Success Rate</div>
          <div class="usage-stat-value">${usage.successful_requests > 0 ? ((usage.successful_requests / usage.total_requests) * 100).toFixed(1) : 0}%</div>
          <div class="usage-stat-change positive">
            Target: 95%
          </div>
        </div>
        <div class="usage-stat">
          <div class="usage-stat-label">Tokens Used</div>
          <div class="usage-stat-value">${usage.tokens_used.toLocaleString()}</div>
          <div class="usage-stat-change">
            ~$${usage.cost_estimate.toFixed(2)} cost
          </div>
        </div>
        <div class="usage-stat">
          <div class="usage-stat-label">Avg Response Time</div>
          <div class="usage-stat-value">${usage.avg_response_time}s</div>
          <div class="usage-stat-change ${usage.avg_response_time < 3 ? 'positive' : 'negative'}">
            ${usage.avg_response_time < 3 ? 'Good' : 'Slow'}
          </div>
        </div>
      </div>

      <div class="section-card">
        <div class="section-card-header">
          <h2 class="section-card-title">User Information</h2>
        </div>
        <div class="section-card-content">
          <div class="form-group">
            <label class="form-label">User ID</label>
            <input type="text" class="form-input" value="${user.id}" disabled>
          </div>
          <div class="form-group">
            <label class="form-label">Email</label>
            <input type="text" class="form-input" value="${user.email}" disabled>
          </div>
          <div class="form-group">
            <label class="form-label">Created At</label>
            <input type="text" class="form-input" value="${this.formatDate(user.created_at)}" disabled>
          </div>
          <div class="form-group">
            <label class="form-label">Last Login</label>
            <input type="text" class="form-input" value="${user.last_login ? this.formatDate(user.last_login) : 'Never'}" disabled>
          </div>
          <div class="form-group">
            <label class="form-label">Auth Provider</label>
            <input type="text" class="form-input" value="${user.auth_provider}" disabled>
          </div>
        </div>
      </div>
    `;
  }

  loadUserTab(tabName) {
    const content = document.getElementById('user-tab-content');

    switch (tabName) {
      case 'overview':
        content.innerHTML = this.renderUserOverviewTab(this.currentUserDetail.user, this.currentUserDetail.usage);
        break;
      case 'usage':
        content.innerHTML = this.renderUsageTab(this.currentUserDetail.usage);
        break;
      case 'api-keys':
        content.innerHTML = this.renderApiKeysTab(this.currentUserDetail.apiKeys);
        break;
      case 'activity':
        content.innerHTML = this.renderActivityTab(this.currentUserDetail.accessLogs);
        break;
      case 'permissions':
        content.innerHTML = this.renderPermissionsTab(this.currentUserDetail.user);
        break;
    }
  }

  renderUsageTab(usage) {
    return `
      <div class="usage-chart">
        <div class="usage-chart-header">
          <h3 class="usage-chart-title">Usage Breakdown</h3>
          <div class="usage-chart-period">
            <button class="period-button active">Daily</button>
            <button class="period-button">Weekly</button>
            <button class="period-button">Monthly</button>
          </div>
        </div>
        <div style="margin-top: 1rem;">
          ${Object.entries(usage.breakdown || {}).map(([endpoint, count]) => `
            <div style="display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid var(--color-border);">
              <span style="color: var(--color-text-muted); font-family: monospace;">${endpoint}</span>
              <span style="font-weight: 600;">${count} requests</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  renderApiKeysTab(apiKeys) {
    return `
      <button class="btn-create-key" onclick="syntraAdmin.createApiKey()">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Create API Key
      </button>
      <div class="api-keys-list">
        ${apiKeys.length > 0 ? apiKeys.map(key => `
          <div class="api-key-item">
            <div class="api-key-info">
              <div class="api-key-name">${key.name}</div>
              <div class="api-key-value">${key.key_prefix}••••••••••••</div>
              <div class="api-key-meta">
                <span>Created: ${this.formatDate(key.created_at)}</span>
                ${key.last_used ? `<span>Last used: ${this.formatDate(key.last_used)}</span>` : '<span>Never used</span>'}
                ${key.expires_at ? `<span>Expires: ${this.formatDate(key.expires_at)}</span>` : ''}
              </div>
            </div>
            <div>
              <span class="badge ${key.is_active ? 'badge-active' : 'badge-inactive'}">${key.is_active ? 'Active' : 'Inactive'}</span>
              ${key.is_active ? `
                <button class="btn-icon btn-icon-delete" onclick="syntraAdmin.revokeApiKey('${key.id}')" style="margin-left: 1rem;">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M5 5l6 6M11 5l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                </button>
              ` : ''}
            </div>
          </div>
        `).join('') : '<p style="color: var(--color-text-muted); text-align: center; padding: 2rem;">No API keys found</p>'}
      </div>
    `;
  }

  renderActivityTab(accessLogs) {
    return `
      <div class="section-card">
        <div class="section-card-header">
          <h2 class="section-card-title">Recent Access Logs</h2>
        </div>
        <div class="section-card-content">
          <table class="access-log-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Action</th>
                <th>Resource</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${accessLogs.map(log => `
                <tr>
                  <td style="white-space: nowrap; color: var(--color-text-muted);">${this.formatDateTime(log.timestamp)}</td>
                  <td>${log.action}</td>
                  <td style="font-family: monospace;">${log.resource}</td>
                  <td>
                    <span class="badge ${log.granted ? 'badge-active' : 'badge-suspended'}">
                      ${log.granted ? 'Granted' : 'Denied'}
                    </span>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  renderPermissionsTab(user) {
    return `
      <div class="section-card">
        <div class="section-card-header">
          <h2 class="section-card-title">User Permissions</h2>
        </div>
        <div class="section-card-content">
          <div class="form-group">
            <label class="form-label">Role</label>
            <input type="text" class="form-input" value="${user.role}" disabled>
          </div>
          <div class="form-group">
            <label class="form-label">Permissions</label>
            <div class="permissions-list">
              ${user.permissions && user.permissions.length > 0
                ? user.permissions.map(p => `<span class="permission-tag">${p}</span>`).join('')
                : '<span style="color: var(--color-text-muted);">No specific permissions assigned</span>'
              }
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // User Actions
  showUserModal(user = null) {
    const isEdit = user !== null;

    const modalHtml = `
      <div class="modal-overlay" id="user-modal">
        <div class="modal">
          <div class="modal-header">
            <h3 class="modal-title">${isEdit ? 'Edit User' : 'Add New User'}</h3>
            <button class="btn-close-modal" onclick="syntraAdmin.closeUserModal()">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4l12 12M4 16L16 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <form id="user-form">
              <div class="form-group">
                <label class="form-label">Name *</label>
                <input type="text" name="name" class="form-input" value="${user?.name || ''}" required>
              </div>
              <div class="form-group">
                <label class="form-label">Email *</label>
                <input type="email" name="email" class="form-input" value="${user?.email || ''}" required ${isEdit ? 'disabled' : ''}>
              </div>
              <div class="form-group">
                <label class="form-label">Role *</label>
                <select name="role" class="form-select" required>
                  <option value="viewer" ${user?.role === 'viewer' ? 'selected' : ''}>Viewer</option>
                  <option value="operator" ${user?.role === 'operator' ? 'selected' : ''}>Operator</option>
                  <option value="developer" ${user?.role === 'developer' ? 'selected' : ''}>Developer</option>
                  <option value="admin" ${user?.role === 'admin' ? 'selected' : ''}>Admin</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Department</label>
                <input type="text" name="department" class="form-input" value="${user?.department || ''}">
              </div>
              ${!isEdit ? `
                <div class="form-group">
                  <label class="form-label">Password</label>
                  <input type="password" name="password" class="form-input">
                  <p class="form-hint">Leave empty to generate automatic password</p>
                </div>
              ` : ''}
            </form>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" onclick="syntraAdmin.closeUserModal()">Cancel</button>
            <button class="btn-primary" onclick="syntraAdmin.saveUser('${user?.id || ''}')">${isEdit ? 'Update' : 'Create'} User</button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    setTimeout(() => document.getElementById('user-modal').classList.add('active'), 10);
  }

  closeUserModal() {
    const modal = document.getElementById('user-modal');
    if (modal) {
      modal.classList.remove('active');
      setTimeout(() => modal.remove(), 300);
    }
  }

  async saveUser(userId) {
    const form = document.getElementById('user-form');
    const formData = new FormData(form);
    const userData = Object.fromEntries(formData.entries());

    try {
      if (userId) {
        await this.apiCall(`/api/admin/users/${userId}`, {
          method: 'PUT',
          body: JSON.stringify(userData)
        });
        this.showToast('User updated successfully', 'success');
      } else {
        await this.apiCall('/api/admin/users', {
          method: 'POST',
          body: JSON.stringify(userData)
        });
        this.showToast('User created successfully', 'success');
      }

      this.closeUserModal();
      this.loadUsers(document.getElementById('content-area'));
    } catch (error) {
      this.showToast(error.message || 'Failed to save user', 'error');
    }
  }

  editUser(userId) {
    const user = this.currentUsers.find(u => u.id === userId);
    if (user) {
      this.showUserModal(user);
    }
  }

  async suspendUser(userId) {
    if (!confirm('Are you sure you want to suspend this user?')) return;

    try {
      await this.apiCall(`/api/admin/users/${userId}/suspend`, { method: 'POST' });
      this.showToast('User suspended successfully', 'success');
      this.loadUsers(document.getElementById('content-area'));
    } catch (error) {
      this.showToast('Failed to suspend user', 'error');
    }
  }

  async activateUser(userId) {
    try {
      await this.apiCall(`/api/admin/users/${userId}/activate`, { method: 'POST' });
      this.showToast('User activated successfully', 'success');
      this.loadUsers(document.getElementById('content-area'));
    } catch (error) {
      this.showToast('Failed to activate user', 'error');
    }
  }

  async deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;

    try {
      await this.apiCall(`/api/admin/users/${userId}`, { method: 'DELETE' });
      this.showToast('User deleted successfully', 'success');
      this.loadUsers(document.getElementById('content-area'));
    } catch (error) {
      this.showToast('Failed to delete user', 'error');
    }
  }

  async createApiKey() {
    const name = prompt('Enter a name for this API key:');
    if (!name) return;

    try {
      const result = await this.apiCall(`/api/admin/users/${this.currentUserDetail.user.id}/api-keys`, {
        method: 'POST',
        body: JSON.stringify({ name })
      });

      alert(`API Key created!\n\nKey: ${result.raw_key}\n\nSave this key now - you won't be able to see it again!`);
      this.viewUserDetail(this.currentUserDetail.user.id);
    } catch (error) {
      this.showToast('Failed to create API key', 'error');
    }
  }

  async revokeApiKey(keyId) {
    if (!confirm('Are you sure you want to revoke this API key?')) return;

    try {
      await this.apiCall(`/api/admin/api-keys/${keyId}`, { method: 'DELETE' });
      this.showToast('API key revoked', 'success');
      this.viewUserDetail(this.currentUserDetail.user.id);
    } catch (error) {
      this.showToast('Failed to revoke API key', 'error');
    }
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

  formatDate(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  }

  formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const icons = {
      success: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="8" fill="currentColor"/><path d="M6 10l3 3 5-5" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>',
      error: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="8" fill="currentColor"/><path d="M7 7l6 6M7 13l6-6" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>',
      warning: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="8" fill="currentColor"/><path d="M10 6v4M10 13h.01" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>',
      info: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="10" cy="10" r="8" fill="currentColor"/><path d="M10 6v8M10 15h.01" stroke="white" stroke-width="2" stroke-linecap="round"/></svg>'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-icon">${icons[type]}</div>
      <div>${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'slideIn 0.3s ease reverse';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
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
