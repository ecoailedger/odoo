/**
 * OpenFlow Web Client
 * Main application entry point
 */

import ActionManager from './action_manager.js';
import rpc from './rpc_service.js';
import notification from './notification.js';

class OpenFlowApp {
    constructor() {
        this.actionManager = null;
        this.currentUser = null;
        this.init();
    }

    async init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.start());
        } else {
            this.start();
        }
    }

    async start() {
        console.log('Starting OpenFlow Web Client...');

        // Create main layout
        this.createLayout();

        // Check authentication
        await this.checkAuth();

        // Setup event listeners
        this.setupEventListeners();

        // Initialize action manager
        const contentArea = document.getElementById('content-area');
        this.actionManager = new ActionManager(contentArea);

        // Load initial view (e.g., dashboard or home)
        await this.loadHome();

        console.log('OpenFlow Web Client started successfully');
    }

    createLayout() {
        const app = document.createElement('div');
        app.id = 'app';

        // Header
        const header = document.createElement('header');
        header.className = 'app-header';
        header.innerHTML = `
            <div class="header-left">
                <h1 class="app-title">OpenFlow</h1>
                <div class="breadcrumbs"></div>
            </div>
            <div class="header-right">
                <span id="user-info"></span>
                <button id="logout-btn" class="btn btn-secondary">Logout</button>
            </div>
        `;

        // Sidebar
        const sidebar = document.createElement('aside');
        sidebar.className = 'app-sidebar';
        sidebar.innerHTML = `
            <nav class="sidebar-nav">
                <ul class="nav-menu">
                    <li class="nav-item">
                        <a href="#" data-action="dashboard">
                            <span class="nav-icon">🏠</span>
                            <span class="nav-label">Dashboard</span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="#" data-model="res.partner">
                            <span class="nav-icon">👥</span>
                            <span class="nav-label">Contacts</span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="#" data-model="res.users">
                            <span class="nav-icon">👤</span>
                            <span class="nav-label">Users</span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="#" data-model="res.company">
                            <span class="nav-icon">🏢</span>
                            <span class="nav-label">Companies</span>
                        </a>
                    </li>
                </ul>
            </nav>
        `;

        // Main content
        const main = document.createElement('main');
        main.className = 'app-main';
        main.innerHTML = `
            <div id="content-area" class="content-area"></div>
        `;

        // Assemble layout
        app.appendChild(header);
        app.appendChild(sidebar);
        app.appendChild(main);

        document.body.appendChild(app);
    }

    setupEventListeners() {
        // Logout button
        document.getElementById('logout-btn')?.addEventListener('click', () => {
            this.logout();
        });

        // Navigation menu
        document.querySelectorAll('.nav-item a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();

                const model = link.dataset.model;
                const action = link.dataset.action;

                // Remove active class from all items
                document.querySelectorAll('.nav-item').forEach(item => {
                    item.classList.remove('active');
                });

                // Add active class to clicked item
                link.closest('.nav-item').classList.add('active');

                if (model) {
                    this.openModel(model);
                } else if (action) {
                    this.handleAction(action);
                }
            });
        });

        // Auth required event
        window.addEventListener('auth:required', () => {
            this.showLogin();
        });
    }

    async checkAuth() {
        try {
            // Try to get current user
            const user = await rpc.call('res.users', 'get_current_user');
            this.currentUser = user;
            this.updateUserInfo();
        } catch (error) {
            // Not authenticated
            this.showLogin();
        }
    }

    updateUserInfo() {
        const userInfo = document.getElementById('user-info');
        if (userInfo && this.currentUser) {
            userInfo.textContent = this.currentUser.name || this.currentUser.login;
        }
    }

    showLogin() {
        // Create login modal
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal login-modal">
                <div class="modal-header">
                    <h2 class="modal-title">Login to OpenFlow</h2>
                </div>
                <div class="modal-body">
                    <form id="login-form">
                        <div class="form-field">
                            <label class="field-label">Username</label>
                            <input type="text" name="login" class="form-input" required autofocus>
                        </div>
                        <div class="form-field">
                            <label class="field-label">Password</label>
                            <input type="password" name="password" class="form-input" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-block">Login</button>
                    </form>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const form = overlay.querySelector('#login-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(form);
            const login = formData.get('login');
            const password = formData.get('password');

            try {
                const result = await rpc.request('/auth/login', {
                    method: 'POST',
                    body: JSON.stringify({ login, password }),
                });

                // Store token
                rpc.setToken(result.access_token);

                // Remove login modal
                document.body.removeChild(overlay);

                // Reload app
                await this.checkAuth();
                await this.loadHome();

                notification.success('Logged in successfully');
            } catch (error) {
                notification.error(error.message, 'Login Failed');
            }
        });
    }

    async logout() {
        try {
            await rpc.request('/auth/logout', { method: 'POST' });
        } catch (error) {
            console.error('Logout error:', error);
        }

        // Clear token
        rpc.setToken(null);
        this.currentUser = null;

        // Clear content
        this.actionManager?.clear();

        // Show login
        this.showLogin();

        notification.info('Logged out successfully');
    }

    async loadHome() {
        // Load default dashboard or home view
        const contentArea = document.getElementById('content-area');
        contentArea.innerHTML = `
            <div class="welcome-screen">
                <h1>Welcome to OpenFlow</h1>
                <p>Select a menu item to get started</p>
            </div>
        `;
    }

    async openModel(model) {
        // Open list view for model
        await this.actionManager.doAction({
            type: 'ir.actions.act_window',
            res_model: model,
            view_mode: 'tree,form',
            name: model,
        });
    }

    async handleAction(action) {
        switch (action) {
            case 'dashboard':
                await this.loadHome();
                break;

            default:
                notification.warning(`Action '${action}' not implemented yet`);
        }
    }
}

// Create and start the app
const app = new OpenFlowApp();

// Make app available globally for debugging
window.app = app;

export default OpenFlowApp;
