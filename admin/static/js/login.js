/**
 * Syntra Admin Login Page
 * Handles authentication via Goalixa Auth Service
 */

class SyntraLogin {
  constructor() {
    this.apiBase = window.location.origin;
    this.init();
  }

  init() {
    this.bindEvents();
    this.checkExistingSession();
    this.setupPasswordToggle();
  }

  bindEvents() {
    // Form submission
    document.getElementById('login-form').addEventListener('submit', (e) => this.handleLogin(e));
  }

  setupPasswordToggle() {
    const toggle = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('password');

    toggle.addEventListener('click', () => {
      const isVisible = toggle.classList.contains('visible');
      passwordInput.type = isVisible ? 'password' : 'text';
      toggle.classList.toggle('visible', !isVisible);
    });
  }

  async checkExistingSession() {
    // Check if user is already authenticated
    const accessToken = this.getCookie('goalixa_access');

    if (accessToken) {
      try {
        const response = await this.apiCall('/api/auth/verify', {
          method: 'POST',
          body: JSON.stringify({ token: accessToken })
        });

        if (response.valid) {
          // Valid session, redirect to admin
          this.redirectToAdmin();
          return;
        }
      } catch (error) {
        // Token invalid, continue to login
        console.log('No valid session found');
      }
    }
  }

  async handleLogin(event) {
    event.preventDefault();

    const form = event.target;
    const email = form.email.value;
    const password = form.password.value;
    const remember = form.remember.checked;

    const button = document.getElementById('login-button');
    const errorDiv = document.getElementById('login-error');

    // Show loading state
    button.classList.add('loading');
    button.disabled = true;
    errorDiv.style.display = 'none';

    try {
      // Call login API
      const response = await this.apiCall('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password, remember })
      });

      if (response.success) {
        // Login successful, store tokens and redirect
        if (response.access_token) {
          localStorage.setItem('syntra_token', response.access_token);
        }

        if (response.user) {
          localStorage.setItem('syntra_user', JSON.stringify(response.user));
        }

        this.showLoadingOverlay('Logging you in...');

        setTimeout(() => {
          this.redirectToAdmin();
        }, 500);
      } else {
        // Login failed
        errorDiv.textContent = response.message || 'Login failed. Please check your credentials.';
        errorDiv.style.display = 'flex';
      }
    } catch (error) {
      errorDiv.textContent = error.message || 'An error occurred. Please try again.';
      errorDiv.style.display = 'flex';
    } finally {
      button.classList.remove('loading');
      button.disabled = false;
    }
  }


  showLoadingOverlay(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    overlay.querySelector('p').textContent = message;
    overlay.style.display = 'flex';
  }

  hideLoadingOverlay() {
    document.getElementById('loading-overlay').style.display = 'none';
  }

  redirectToAdmin() {
    window.location.href = '/admin';
  }

  async apiCall(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    // Use current origin (works on both syntra.goalixa.com and localhost)
    const response = await fetch(`${window.location.origin}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include'  // Include cookies for auth
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(';').shift();
    }
    return null;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new SyntraLogin();
});
