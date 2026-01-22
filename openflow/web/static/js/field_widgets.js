/**
 * Field Widgets
 * UI components for different field types
 */

import rpc from './rpc_service.js';

/**
 * Base Widget Class
 */
class BaseWidget {
    constructor(field, value, options = {}) {
        this.field = field;
        this.value = value;
        this.options = options;
        this.readonly = options.readonly || field.readonly || false;
        this.required = options.required || field.required || false;
        this.element = null;
    }

    render() {
        throw new Error('render() must be implemented');
    }

    getValue() {
        throw new Error('getValue() must be implemented');
    }

    setValue(value) {
        this.value = value;
    }

    validate() {
        if (this.required && !this.getValue()) {
            return { valid: false, message: `${this.field.string || this.field.name} is required` };
        }
        return { valid: true };
    }

    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

/**
 * Char Widget - Text input
 */
class CharField extends BaseWidget {
    render() {
        const container = document.createElement('div');
        container.className = 'field-widget field-char';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-input';
        input.value = this.value || '';
        input.disabled = this.readonly;
        input.required = this.required;
        input.placeholder = this.field.placeholder || '';

        if (this.field.size) {
            input.maxLength = this.field.size;
        }

        container.appendChild(input);
        this.input = input;
        this.element = container;

        return container;
    }

    getValue() {
        return this.input.value || false;
    }

    setValue(value) {
        this.value = value;
        if (this.input) {
            this.input.value = value || '';
        }
    }
}

/**
 * Text Widget - Textarea
 */
class TextField extends BaseWidget {
    render() {
        const container = document.createElement('div');
        container.className = 'field-widget field-text';

        const textarea = document.createElement('textarea');
        textarea.className = 'form-textarea';
        textarea.value = this.value || '';
        textarea.disabled = this.readonly;
        textarea.required = this.required;
        textarea.rows = this.options.rows || 3;

        container.appendChild(textarea);
        this.textarea = textarea;
        this.element = container;

        return container;
    }

    getValue() {
        return this.textarea.value || false;
    }

    setValue(value) {
        this.value = value;
        if (this.textarea) {
            this.textarea.value = value || '';
        }
    }
}

/**
 * Integer Widget - Number input
 */
class IntegerField extends BaseWidget {
    render() {
        const container = document.createElement('div');
        container.className = 'field-widget field-integer';

        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-input';
        input.value = this.value !== null && this.value !== undefined ? this.value : '';
        input.disabled = this.readonly;
        input.required = this.required;
        input.step = '1';

        container.appendChild(input);
        this.input = input;
        this.element = container;

        return container;
    }

    getValue() {
        const value = this.input.value;
        return value ? parseInt(value, 10) : false;
    }

    setValue(value) {
        this.value = value;
        if (this.input) {
            this.input.value = value !== null && value !== undefined ? value : '';
        }
    }
}

/**
 * Float Widget - Decimal number input
 */
class FloatField extends BaseWidget {
    render() {
        const container = document.createElement('div');
        container.className = 'field-widget field-float';

        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-input';
        input.value = this.value !== null && this.value !== undefined ? this.value : '';
        input.disabled = this.readonly;
        input.required = this.required;
        input.step = this.field.digits ? Math.pow(10, -this.field.digits[1]) : '0.01';

        container.appendChild(input);
        this.input = input;
        this.element = container;

        return container;
    }

    getValue() {
        const value = this.input.value;
        return value ? parseFloat(value) : false;
    }

    setValue(value) {
        this.value = value;
        if (this.input) {
            this.input.value = value !== null && value !== undefined ? value : '';
        }
    }
}

/**
 * Boolean Widget - Checkbox
 */
class BooleanField extends BaseWidget {
    render() {
        const container = document.createElement('div');
        container.className = 'field-widget field-boolean';

        const label = document.createElement('label');
        label.className = 'checkbox-label';

        const input = document.createElement('input');
        input.type = 'checkbox';
        input.className = 'form-checkbox';
        input.checked = !!this.value;
        input.disabled = this.readonly;

        const span = document.createElement('span');
        span.textContent = this.field.string || this.field.name;

        label.appendChild(input);
        label.appendChild(span);
        container.appendChild(label);

        this.input = input;
        this.element = container;

        return container;
    }

    getValue() {
        return this.input.checked;
    }

    setValue(value) {
        this.value = value;
        if (this.input) {
            this.input.checked = !!value;
        }
    }
}

/**
 * Selection Widget - Dropdown
 */
class SelectionField extends BaseWidget {
    render() {
        const container = document.createElement('div');
        container.className = 'field-widget field-selection';

        const select = document.createElement('select');
        select.className = 'form-select';
        select.disabled = this.readonly;
        select.required = this.required;

        // Add empty option if not required
        if (!this.required) {
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = '';
            select.appendChild(emptyOption);
        }

        // Add options from selection
        const selection = this.field.selection || [];
        selection.forEach(([value, label]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            option.selected = value === this.value;
            select.appendChild(option);
        });

        container.appendChild(select);
        this.select = select;
        this.element = container;

        return container;
    }

    getValue() {
        return this.select.value || false;
    }

    setValue(value) {
        this.value = value;
        if (this.select) {
            this.select.value = value || '';
        }
    }
}

/**
 * Date Widget - Date input
 */
class DateField extends BaseWidget {
    render() {
        const container = document.createElement('div');
        container.className = 'field-widget field-date';

        const input = document.createElement('input');
        input.type = 'date';
        input.className = 'form-input';
        input.value = this.value || '';
        input.disabled = this.readonly;
        input.required = this.required;

        container.appendChild(input);
        this.input = input;
        this.element = container;

        return container;
    }

    getValue() {
        return this.input.value || false;
    }

    setValue(value) {
        this.value = value;
        if (this.input) {
            this.input.value = value || '';
        }
    }
}

/**
 * DateTime Widget - Datetime input
 */
class DateTimeField extends BaseWidget {
    render() {
        const container = document.createElement('div');
        container.className = 'field-widget field-datetime';

        const input = document.createElement('input');
        input.type = 'datetime-local';
        input.className = 'form-input';
        input.value = this.value ? this.value.substring(0, 16) : '';
        input.disabled = this.readonly;
        input.required = this.required;

        container.appendChild(input);
        this.input = input;
        this.element = container;

        return container;
    }

    getValue() {
        return this.input.value ? this.input.value + ':00' : false;
    }

    setValue(value) {
        this.value = value;
        if (this.input) {
            this.input.value = value ? value.substring(0, 16) : '';
        }
    }
}

/**
 * Many2one Widget - Autocomplete
 */
class Many2oneField extends BaseWidget {
    render() {
        const container = document.createElement('div');
        container.className = 'field-widget field-many2one';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-input';
        input.disabled = this.readonly;
        input.required = this.required;
        input.placeholder = 'Search...';

        // Display current value
        if (this.value && Array.isArray(this.value)) {
            input.value = this.value[1]; // Display name
            input.dataset.recordId = this.value[0]; // Store ID
        }

        // Autocomplete dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown hidden';

        container.appendChild(input);
        container.appendChild(dropdown);

        this.input = input;
        this.dropdown = dropdown;
        this.element = container;

        // Setup autocomplete
        if (!this.readonly) {
            this.setupAutocomplete();
        }

        return container;
    }

    setupAutocomplete() {
        let timeout;

        this.input.addEventListener('input', () => {
            clearTimeout(timeout);
            const query = this.input.value;

            if (query.length < 2) {
                this.dropdown.classList.add('hidden');
                return;
            }

            timeout = setTimeout(async () => {
                try {
                    const domain = [[this.field.relation_name || 'name', 'ilike', query]];
                    const records = await rpc.search(this.field.relation, domain, { limit: 10 });

                    this.showResults(records);
                } catch (error) {
                    console.error('Autocomplete error:', error);
                }
            }, 300);
        });

        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.element.contains(e.target)) {
                this.dropdown.classList.add('hidden');
            }
        });
    }

    showResults(records) {
        this.dropdown.innerHTML = '';

        if (records.length === 0) {
            this.dropdown.innerHTML = '<div class="autocomplete-item">No results</div>';
            this.dropdown.classList.remove('hidden');
            return;
        }

        records.forEach(record => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.textContent = record.name || record.display_name || `Record ${record.id}`;
            item.dataset.recordId = record.id;

            item.addEventListener('click', () => {
                this.selectRecord(record);
            });

            this.dropdown.appendChild(item);
        });

        this.dropdown.classList.remove('hidden');
    }

    selectRecord(record) {
        this.value = [record.id, record.name || record.display_name];
        this.input.value = this.value[1];
        this.input.dataset.recordId = this.value[0];
        this.dropdown.classList.add('hidden');
    }

    getValue() {
        return this.input.dataset.recordId ? parseInt(this.input.dataset.recordId) : false;
    }

    setValue(value) {
        this.value = value;
        if (this.input) {
            if (value && Array.isArray(value)) {
                this.input.value = value[1];
                this.input.dataset.recordId = value[0];
            } else {
                this.input.value = '';
                delete this.input.dataset.recordId;
            }
        }
    }
}

/**
 * Widget Factory
 */
export function createWidget(field, value, options = {}) {
    const type = field.type || 'char';
    const widgetClass = field.widget || type;

    const widgets = {
        'char': CharField,
        'text': TextField,
        'integer': IntegerField,
        'float': FloatField,
        'boolean': BooleanField,
        'selection': SelectionField,
        'date': DateField,
        'datetime': DateTimeField,
        'many2one': Many2oneField,
    };

    const WidgetClass = widgets[widgetClass] || CharField;
    return new WidgetClass(field, value, options);
}

export {
    BaseWidget,
    CharField,
    TextField,
    IntegerField,
    FloatField,
    BooleanField,
    SelectionField,
    DateField,
    DateTimeField,
    Many2oneField,
};
