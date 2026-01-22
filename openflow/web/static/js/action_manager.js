/**
 * Action Manager
 * Manages navigation and action execution
 */

import { ViewManager } from './view_manager.js';
import notification from './notification.js';

export class ActionManager {
    constructor(container) {
        this.container = container;
        this.viewManager = null;
        this.actionStack = [];
        this.breadcrumbs = [];
    }

    /**
     * Execute an action
     */
    async doAction(action, options = {}) {
        try {
            if (typeof action === 'string') {
                // Action by XML ID or name
                action = await this.loadAction(action);
            }

            const actionType = action.type || 'ir.actions.act_window';

            switch (actionType) {
                case 'ir.actions.act_window':
                    await this.doWindowAction(action, options);
                    break;

                case 'ir.actions.act_url':
                    this.doUrlAction(action);
                    break;

                case 'ir.actions.server':
                    await this.doServerAction(action);
                    break;

                case 'ir.actions.client':
                    await this.doClientAction(action);
                    break;

                default:
                    throw new Error(`Unknown action type: ${actionType}`);
            }

            // Add to action stack
            if (!options.skipBreadcrumb) {
                this.actionStack.push(action);
                this.updateBreadcrumbs();
            }

        } catch (error) {
            notification.error(error.message, 'Action Failed');
            console.error('Action error:', error);
        }
    }

    /**
     * Execute window action (open view)
     */
    async doWindowAction(action, options = {}) {
        const {
            res_model,
            res_id,
            view_mode = 'tree,form',
            views = [],
            domain = [],
            context = {},
            target = 'current',
        } = action;

        if (!res_model) {
            throw new Error('res_model is required for window actions');
        }

        // Parse view modes
        const viewModes = view_mode.split(',').map(v => v.trim());
        const startMode = options.viewMode || viewModes[0];

        // Create or update view manager
        if (!this.viewManager || target === 'new') {
            this.viewManager = new ViewManager(this.container, {
                model: res_model,
                viewModes,
                domain,
                context,
            });
        } else {
            this.viewManager.setModel(res_model);
            this.viewManager.setDomain(domain);
        }

        // Switch to the view
        if (res_id) {
            await this.viewManager.switchView('form', { recordId: res_id });
        } else {
            await this.viewManager.switchView(startMode);
        }
    }

    /**
     * Execute URL action
     */
    doUrlAction(action) {
        const { url, target = '_blank' } = action;
        window.open(url, target);
    }

    /**
     * Execute server action
     */
    async doServerAction(action) {
        // Server actions are executed on the backend
        // This would call a specific endpoint
        throw new Error('Server actions not yet implemented');
    }

    /**
     * Execute client action
     */
    async doClientAction(action) {
        // Client actions are custom JavaScript actions
        const { tag, params = {} } = action;

        // Dispatch custom event for client actions
        window.dispatchEvent(new CustomEvent('client:action', {
            detail: { tag, params },
        }));
    }

    /**
     * Load action definition from server
     */
    async loadAction(actionId) {
        // This would load the action definition from the backend
        // For now, return a simple structure
        throw new Error('Action loading not yet implemented');
    }

    /**
     * Go back to previous action
     */
    goBack() {
        if (this.actionStack.length > 1) {
            this.actionStack.pop(); // Remove current
            const previousAction = this.actionStack.pop(); // Get previous
            this.doAction(previousAction, { skipBreadcrumb: true });
        }
    }

    /**
     * Update breadcrumb navigation
     */
    updateBreadcrumbs() {
        const breadcrumbContainer = document.querySelector('.breadcrumbs');
        if (!breadcrumbContainer) return;

        breadcrumbContainer.innerHTML = '';

        this.actionStack.forEach((action, index) => {
            const crumb = document.createElement('span');
            crumb.className = 'breadcrumb-item';
            crumb.textContent = action.name || action.res_model || 'View';

            if (index < this.actionStack.length - 1) {
                crumb.classList.add('clickable');
                crumb.addEventListener('click', () => {
                    // Go back to this action
                    while (this.actionStack.length > index + 1) {
                        this.actionStack.pop();
                    }
                    this.doAction(action, { skipBreadcrumb: true });
                });
            }

            breadcrumbContainer.appendChild(crumb);

            if (index < this.actionStack.length - 1) {
                const separator = document.createElement('span');
                separator.className = 'breadcrumb-separator';
                separator.textContent = ' / ';
                breadcrumbContainer.appendChild(separator);
            }
        });
    }

    /**
     * Clear action stack
     */
    clear() {
        this.actionStack = [];
        this.breadcrumbs = [];
        if (this.viewManager) {
            this.viewManager.destroy();
            this.viewManager = null;
        }
    }
}

export default ActionManager;
