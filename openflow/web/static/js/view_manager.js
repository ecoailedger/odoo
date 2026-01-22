/**
 * View Manager
 * Manages different view types and switching between them
 */

import { FormRenderer, ListRenderer } from './view_renderer.js';
import rpc from './rpc_service.js';
import notification from './notification.js';

export class ViewManager {
    constructor(container, options = {}) {
        this.container = container;
        this.model = options.model;
        this.viewModes = options.viewModes || ['tree', 'form'];
        this.domain = options.domain || [];
        this.context = options.context || {};

        this.currentView = null;
        this.currentRenderer = null;
        this.viewDefs = {};

        this.element = null;
        this.init();
    }

    init() {
        // Create main container
        const container = document.createElement('div');
        container.className = 'view-manager';

        // Create view switcher
        const switcher = this.createViewSwitcher();
        container.appendChild(switcher);

        // Create content area
        const content = document.createElement('div');
        content.className = 'view-content';
        this.contentArea = content;
        container.appendChild(content);

        this.element = container;
        this.container.appendChild(container);
    }

    createViewSwitcher() {
        const switcher = document.createElement('div');
        switcher.className = 'view-switcher';

        this.viewModes.forEach(mode => {
            const button = document.createElement('button');
            button.className = 'view-switch-btn';
            button.dataset.viewMode = mode;
            button.textContent = this.getViewIcon(mode) + ' ' + this.capitalize(mode);

            button.addEventListener('click', () => this.switchView(mode));

            switcher.appendChild(button);
        });

        this.switcherElement = switcher;
        return switcher;
    }

    getViewIcon(mode) {
        const icons = {
            'tree': '☰',
            'form': '📝',
            'kanban': '⊞',
            'calendar': '📅',
            'graph': '📊',
            'pivot': '⊡',
        };
        return icons[mode] || '◉';
    }

    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    async switchView(viewMode, options = {}) {
        try {
            // Update active button
            this.switcherElement.querySelectorAll('.view-switch-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.viewMode === viewMode);
            });

            // Destroy current renderer
            if (this.currentRenderer) {
                this.currentRenderer.destroy();
            }

            // Load view definition if not cached
            if (!this.viewDefs[viewMode]) {
                this.viewDefs[viewMode] = await this.loadViewDef(viewMode);
            }

            const viewDef = this.viewDefs[viewMode];

            // Create renderer based on view type
            let renderer;

            switch (viewMode) {
                case 'tree':
                case 'list':
                    renderer = new ListRenderer(this.model, viewDef);
                    this.contentArea.innerHTML = '';
                    this.contentArea.appendChild(renderer.render());

                    // Load records
                    await renderer.loadRecords(this.domain);

                    // Setup event listeners
                    renderer.element.addEventListener('record:create', () => {
                        this.switchView('form', { mode: 'create' });
                    });

                    renderer.element.addEventListener('record:edit', async (e) => {
                        const record = e.detail.record;
                        this.switchView('form', { recordId: record.id });
                    });

                    renderer.element.addEventListener('records:deleted', () => {
                        renderer.loadRecords(this.domain);
                    });

                    break;

                case 'form':
                    let record = null;

                    if (options.recordId) {
                        // Load existing record
                        const records = await rpc.read(this.model, [options.recordId]);
                        record = records[0];
                    }

                    renderer = new FormRenderer(this.model, viewDef, record);
                    this.contentArea.innerHTML = '';
                    this.contentArea.appendChild(renderer.render());

                    // Setup event listeners
                    renderer.element.addEventListener('record:saved', () => {
                        notification.success('Record saved');
                        this.switchView('tree');
                    });

                    renderer.element.addEventListener('record:cancelled', () => {
                        this.switchView('tree');
                    });

                    break;

                default:
                    throw new Error(`View type ${viewMode} not supported yet`);
            }

            this.currentView = viewMode;
            this.currentRenderer = renderer;

        } catch (error) {
            notification.error(error.message, 'View Error');
            console.error('View switch error:', error);
        }
    }

    async loadViewDef(viewMode) {
        try {
            // This would normally load the view definition from the backend
            // For now, we'll generate a simple view definition based on model fields

            // Get model fields
            const fields = await this.getModelFields();

            return {
                type: viewMode,
                arch: `<${viewMode}/>`, // Simplified
                fields: fields,
                mode: 'edit',
            };

        } catch (error) {
            console.error('Error loading view definition:', error);

            // Return a minimal view definition
            return {
                type: viewMode,
                arch: `<${viewMode}/>`,
                fields: {},
                mode: 'edit',
            };
        }
    }

    async getModelFields() {
        try {
            // Call backend to get model fields
            // For now, return common fields
            const result = await rpc.call('ir.model', 'get_fields', [this.model]);
            return result;
        } catch (error) {
            console.error('Error getting model fields:', error);

            // Return basic fields as fallback
            return {
                'id': { type: 'integer', string: 'ID', readonly: true },
                'name': { type: 'char', string: 'Name', required: true },
                'active': { type: 'boolean', string: 'Active' },
                'create_date': { type: 'datetime', string: 'Created', readonly: true },
                'write_date': { type: 'datetime', string: 'Modified', readonly: true },
            };
        }
    }

    setModel(model) {
        this.model = model;
        this.viewDefs = {}; // Clear cached view definitions
    }

    setDomain(domain) {
        this.domain = domain;
    }

    setContext(context) {
        this.context = context;
    }

    destroy() {
        if (this.currentRenderer) {
            this.currentRenderer.destroy();
        }

        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

export default ViewManager;
