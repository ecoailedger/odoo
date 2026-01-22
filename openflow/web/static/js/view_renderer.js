/**
 * View Renderers
 * Renders different view types (form, list, etc.)
 */

import { createWidget } from './field_widgets.js';
import rpc from './rpc_service.js';
import notification from './notification.js';

/**
 * Form Renderer
 * Renders form views for creating/editing records
 */
export class FormRenderer {
    constructor(model, viewDef, record = null) {
        this.model = model;
        this.viewDef = viewDef;
        this.record = record;
        this.widgets = {};
        this.element = null;
    }

    render() {
        const container = document.createElement('div');
        container.className = 'form-view';

        // Create form header
        const header = this.renderHeader();
        container.appendChild(header);

        // Create form body
        const body = document.createElement('div');
        body.className = 'form-body';

        // Render fields from view definition
        if (this.viewDef.arch) {
            this.renderFields(body, this.viewDef.arch);
        }

        container.appendChild(body);

        // Create form footer
        const footer = this.renderFooter();
        container.appendChild(footer);

        this.element = container;
        return container;
    }

    renderHeader() {
        const header = document.createElement('div');
        header.className = 'form-header';

        const title = document.createElement('h2');
        title.textContent = this.record ? `Edit ${this.model}` : `New ${this.model}`;
        header.appendChild(title);

        return header;
    }

    renderFields(container, arch) {
        // Parse arch structure (simplified version)
        // In a real implementation, this would parse the XML structure
        const fields = this.viewDef.fields || {};

        Object.entries(fields).forEach(([fieldName, fieldDef]) => {
            const fieldContainer = document.createElement('div');
            fieldContainer.className = 'form-field';

            // Field label
            const label = document.createElement('label');
            label.className = 'field-label';
            label.textContent = fieldDef.string || fieldName;
            if (fieldDef.required) {
                label.classList.add('required');
            }
            fieldContainer.appendChild(label);

            // Field widget
            const value = this.record ? this.record[fieldName] : null;
            const widget = createWidget(fieldDef, value, {
                readonly: this.viewDef.mode === 'readonly',
            });

            const widgetElement = widget.render();
            fieldContainer.appendChild(widgetElement);

            // Store widget reference
            this.widgets[fieldName] = widget;

            container.appendChild(fieldContainer);
        });
    }

    renderFooter() {
        const footer = document.createElement('div');
        footer.className = 'form-footer';

        const saveButton = document.createElement('button');
        saveButton.className = 'btn btn-primary';
        saveButton.textContent = 'Save';
        saveButton.addEventListener('click', () => this.save());

        const cancelButton = document.createElement('button');
        cancelButton.className = 'btn btn-secondary';
        cancelButton.textContent = 'Cancel';
        cancelButton.addEventListener('click', () => this.cancel());

        footer.appendChild(cancelButton);
        footer.appendChild(saveButton);

        return footer;
    }

    async save() {
        // Validate all fields
        const errors = [];
        Object.entries(this.widgets).forEach(([fieldName, widget]) => {
            const validation = widget.validate();
            if (!validation.valid) {
                errors.push(validation.message);
            }
        });

        if (errors.length > 0) {
            notification.error(errors.join('\n'), 'Validation Error');
            return;
        }

        // Collect values
        const values = {};
        Object.entries(this.widgets).forEach(([fieldName, widget]) => {
            values[fieldName] = widget.getValue();
        });

        try {
            if (this.record && this.record.id) {
                // Update existing record
                await rpc.write(this.model, [this.record.id], values);
                notification.success('Record updated successfully');
            } else {
                // Create new record
                const newRecord = await rpc.create(this.model, values);
                notification.success('Record created successfully');
                this.record = newRecord;
            }

            // Trigger save event
            this.element.dispatchEvent(new CustomEvent('record:saved', {
                detail: { record: this.record },
            }));
        } catch (error) {
            notification.error(error.message, 'Save Failed');
        }
    }

    cancel() {
        this.element.dispatchEvent(new CustomEvent('record:cancelled'));
    }

    getValues() {
        const values = {};
        Object.entries(this.widgets).forEach(([fieldName, widget]) => {
            values[fieldName] = widget.getValue();
        });
        return values;
    }

    setValues(values) {
        Object.entries(values).forEach(([fieldName, value]) => {
            if (this.widgets[fieldName]) {
                this.widgets[fieldName].setValue(value);
            }
        });
    }

    destroy() {
        Object.values(this.widgets).forEach(widget => widget.destroy());
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

/**
 * List Renderer
 * Renders list/tree views for browsing records
 */
export class ListRenderer {
    constructor(model, viewDef, options = {}) {
        this.model = model;
        this.viewDef = viewDef;
        this.options = options;
        this.records = [];
        this.selectedRecords = new Set();
        this.element = null;
    }

    render() {
        const container = document.createElement('div');
        container.className = 'list-view';

        // Create toolbar
        const toolbar = this.renderToolbar();
        container.appendChild(toolbar);

        // Create table
        const table = this.renderTable();
        container.appendChild(table);

        // Create pagination
        const pagination = this.renderPagination();
        container.appendChild(pagination);

        this.element = container;
        return container;
    }

    renderToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'list-toolbar';

        const createButton = document.createElement('button');
        createButton.className = 'btn btn-primary';
        createButton.textContent = 'Create';
        createButton.addEventListener('click', () => this.onCreate());

        const deleteButton = document.createElement('button');
        deleteButton.className = 'btn btn-danger';
        deleteButton.textContent = 'Delete';
        deleteButton.disabled = this.selectedRecords.size === 0;
        deleteButton.addEventListener('click', () => this.onDelete());

        this.deleteButton = deleteButton;

        toolbar.appendChild(createButton);
        toolbar.appendChild(deleteButton);

        return toolbar;
    }

    renderTable() {
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-container';

        const table = document.createElement('table');
        table.className = 'data-table';

        // Table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');

        // Checkbox column
        const checkboxTh = document.createElement('th');
        checkboxTh.className = 'checkbox-column';
        const selectAllCheckbox = document.createElement('input');
        selectAllCheckbox.type = 'checkbox';
        selectAllCheckbox.addEventListener('change', (e) => this.selectAll(e.target.checked));
        checkboxTh.appendChild(selectAllCheckbox);
        headerRow.appendChild(checkboxTh);

        // Field columns
        const fields = this.viewDef.fields || {};
        this.columns = [];

        Object.entries(fields).forEach(([fieldName, fieldDef]) => {
            if (fieldDef.invisible) return;

            this.columns.push(fieldName);

            const th = document.createElement('th');
            th.textContent = fieldDef.string || fieldName;
            th.dataset.field = fieldName;
            th.classList.add('sortable');
            th.addEventListener('click', () => this.sort(fieldName));
            headerRow.appendChild(th);
        });

        // Actions column
        const actionsTh = document.createElement('th');
        actionsTh.textContent = 'Actions';
        actionsTh.className = 'actions-column';
        headerRow.appendChild(actionsTh);

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Table body
        const tbody = document.createElement('tbody');
        this.tbody = tbody;
        table.appendChild(tbody);

        tableContainer.appendChild(table);
        return tableContainer;
    }

    renderTableBody(records) {
        this.tbody.innerHTML = '';
        this.records = records;

        if (records.length === 0) {
            const emptyRow = document.createElement('tr');
            const emptyCell = document.createElement('td');
            emptyCell.colSpan = this.columns.length + 2;
            emptyCell.className = 'empty-message';
            emptyCell.textContent = 'No records found';
            emptyRow.appendChild(emptyCell);
            this.tbody.appendChild(emptyRow);
            return;
        }

        records.forEach(record => {
            const row = this.renderRow(record);
            this.tbody.appendChild(row);
        });
    }

    renderRow(record) {
        const row = document.createElement('tr');
        row.dataset.recordId = record.id;

        // Checkbox cell
        const checkboxCell = document.createElement('td');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = this.selectedRecords.has(record.id);
        checkbox.addEventListener('change', (e) => this.selectRecord(record.id, e.target.checked));
        checkboxCell.appendChild(checkbox);
        row.appendChild(checkboxCell);

        // Field cells
        this.columns.forEach(fieldName => {
            const cell = document.createElement('td');
            const value = record[fieldName];

            // Format value based on type
            if (Array.isArray(value)) {
                // Many2one: [id, name]
                cell.textContent = value[1] || '';
            } else if (typeof value === 'boolean') {
                cell.textContent = value ? '✓' : '';
            } else {
                cell.textContent = value !== false && value !== null ? value : '';
            }

            row.appendChild(cell);
        });

        // Actions cell
        const actionsCell = document.createElement('td');
        actionsCell.className = 'actions-cell';

        const editButton = document.createElement('button');
        editButton.className = 'btn-icon';
        editButton.textContent = '✎';
        editButton.title = 'Edit';
        editButton.addEventListener('click', () => this.onEdit(record));

        const deleteButton = document.createElement('button');
        deleteButton.className = 'btn-icon btn-danger';
        deleteButton.textContent = '🗑';
        deleteButton.title = 'Delete';
        deleteButton.addEventListener('click', () => this.onDeleteSingle(record));

        actionsCell.appendChild(editButton);
        actionsCell.appendChild(deleteButton);
        row.appendChild(actionsCell);

        // Double click to edit
        row.addEventListener('dblclick', () => this.onEdit(record));

        return row;
    }

    renderPagination() {
        const pagination = document.createElement('div');
        pagination.className = 'pagination';

        const info = document.createElement('span');
        info.textContent = `${this.records.length} records`;
        pagination.appendChild(info);

        // TODO: Add actual pagination controls

        return pagination;
    }

    selectRecord(recordId, selected) {
        if (selected) {
            this.selectedRecords.add(recordId);
        } else {
            this.selectedRecords.delete(recordId);
        }

        if (this.deleteButton) {
            this.deleteButton.disabled = this.selectedRecords.size === 0;
        }
    }

    selectAll(selected) {
        this.records.forEach(record => {
            this.selectRecord(record.id, selected);
        });

        // Update checkboxes
        this.tbody.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = selected;
        });
    }

    onCreate() {
        this.element.dispatchEvent(new CustomEvent('record:create'));
    }

    onEdit(record) {
        this.element.dispatchEvent(new CustomEvent('record:edit', {
            detail: { record },
        }));
    }

    async onDeleteSingle(record) {
        const confirmed = await notification.confirm(
            `Are you sure you want to delete this record?`,
            { title: 'Confirm Delete', type: 'danger', confirmText: 'Delete' }
        );

        if (confirmed) {
            try {
                await rpc.unlink(this.model, [record.id]);
                notification.success('Record deleted successfully');
                this.element.dispatchEvent(new CustomEvent('records:deleted'));
            } catch (error) {
                notification.error(error.message, 'Delete Failed');
            }
        }
    }

    async onDelete() {
        if (this.selectedRecords.size === 0) return;

        const confirmed = await notification.confirm(
            `Are you sure you want to delete ${this.selectedRecords.size} record(s)?`,
            { title: 'Confirm Delete', type: 'danger', confirmText: 'Delete' }
        );

        if (confirmed) {
            try {
                await rpc.unlink(this.model, Array.from(this.selectedRecords));
                notification.success(`${this.selectedRecords.size} record(s) deleted successfully`);
                this.selectedRecords.clear();
                this.element.dispatchEvent(new CustomEvent('records:deleted'));
            } catch (error) {
                notification.error(error.message, 'Delete Failed');
            }
        }
    }

    async sort(fieldName) {
        // Toggle sort order
        this.sortOrder = this.sortField === fieldName && this.sortOrder === 'asc' ? 'desc' : 'asc';
        this.sortField = fieldName;

        // Trigger reload with sort
        this.element.dispatchEvent(new CustomEvent('list:sort', {
            detail: { field: fieldName, order: this.sortOrder },
        }));
    }

    async loadRecords(domain = [], options = {}) {
        try {
            const records = await rpc.search(this.model, domain, {
                ...options,
                fields: this.columns,
            });
            this.renderTableBody(records);
        } catch (error) {
            notification.error(error.message, 'Load Failed');
        }
    }

    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}
