/**
 * Notification System
 * Toast notifications, confirmation dialogs, and alerts
 */

class NotificationService {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create notification container
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);

        // Inject styles
        this.injectStyles();
    }

    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
            }

            .toast {
                background: white;
                border-radius: 8px;
                padding: 16px 20px;
                margin-bottom: 10px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                display: flex;
                align-items: center;
                gap: 12px;
                animation: slideIn 0.3s ease-out;
                border-left: 4px solid;
            }

            .toast.success {
                border-left-color: #10b981;
            }

            .toast.error {
                border-left-color: #ef4444;
            }

            .toast.warning {
                border-left-color: #f59e0b;
            }

            .toast.info {
                border-left-color: #3b82f6;
            }

            .toast-icon {
                font-size: 20px;
                flex-shrink: 0;
            }

            .toast.success .toast-icon {
                color: #10b981;
            }

            .toast.error .toast-icon {
                color: #ef4444;
            }

            .toast.warning .toast-icon {
                color: #f59e0b;
            }

            .toast.info .toast-icon {
                color: #3b82f6;
            }

            .toast-content {
                flex: 1;
            }

            .toast-title {
                font-weight: 600;
                margin-bottom: 4px;
                color: #1f2937;
            }

            .toast-message {
                color: #6b7280;
                font-size: 14px;
            }

            .toast-close {
                background: none;
                border: none;
                color: #9ca3af;
                cursor: pointer;
                font-size: 20px;
                padding: 0;
                line-height: 1;
                flex-shrink: 0;
            }

            .toast-close:hover {
                color: #4b5563;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }

            .toast.closing {
                animation: slideOut 0.3s ease-in;
            }

            /* Modal Dialog */
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10001;
                animation: fadeIn 0.2s ease-out;
            }

            .modal {
                background: white;
                border-radius: 12px;
                padding: 24px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                animation: modalSlideIn 0.3s ease-out;
            }

            .modal-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 16px;
            }

            .modal-icon {
                font-size: 24px;
                flex-shrink: 0;
            }

            .modal.confirm .modal-icon {
                color: #3b82f6;
            }

            .modal.warning .modal-icon {
                color: #f59e0b;
            }

            .modal.danger .modal-icon {
                color: #ef4444;
            }

            .modal-title {
                font-size: 18px;
                font-weight: 600;
                color: #1f2937;
                flex: 1;
            }

            .modal-body {
                color: #6b7280;
                margin-bottom: 24px;
            }

            .modal-footer {
                display: flex;
                gap: 12px;
                justify-content: flex-end;
            }

            .modal-button {
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }

            .modal-button.primary {
                background: #3b82f6;
                color: white;
            }

            .modal-button.primary:hover {
                background: #2563eb;
            }

            .modal-button.danger {
                background: #ef4444;
                color: white;
            }

            .modal-button.danger:hover {
                background: #dc2626;
            }

            .modal-button.secondary {
                background: #e5e7eb;
                color: #4b5563;
            }

            .modal-button.secondary:hover {
                background: #d1d5db;
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            @keyframes modalSlideIn {
                from {
                    transform: translateY(-20px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Show toast notification
     */
    toast(message, options = {}) {
        const {
            type = 'info',
            title = null,
            duration = 5000,
        } = options;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ',
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">×</button>
        `;

        const closeButton = toast.querySelector('.toast-close');
        closeButton.addEventListener('click', () => this.removeToast(toast));

        this.container.appendChild(toast);

        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => this.removeToast(toast), duration);
        }

        return toast;
    }

    /**
     * Remove toast with animation
     */
    removeToast(toast) {
        toast.classList.add('closing');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    /**
     * Success notification
     */
    success(message, title = 'Success') {
        return this.toast(message, { type: 'success', title });
    }

    /**
     * Error notification
     */
    error(message, title = 'Error') {
        return this.toast(message, { type: 'error', title, duration: 0 });
    }

    /**
     * Warning notification
     */
    warning(message, title = 'Warning') {
        return this.toast(message, { type: 'warning', title });
    }

    /**
     * Info notification
     */
    info(message, title = null) {
        return this.toast(message, { type: 'info', title });
    }

    /**
     * Confirmation dialog
     */
    confirm(message, options = {}) {
        return new Promise((resolve) => {
            const {
                title = 'Confirm',
                confirmText = 'Confirm',
                cancelText = 'Cancel',
                type = 'confirm', // confirm, warning, danger
            } = options;

            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';

            const icons = {
                confirm: '?',
                warning: '⚠',
                danger: '⚠',
            };

            overlay.innerHTML = `
                <div class="modal ${type}">
                    <div class="modal-header">
                        <div class="modal-icon">${icons[type] || icons.confirm}</div>
                        <div class="modal-title">${title}</div>
                    </div>
                    <div class="modal-body">${message}</div>
                    <div class="modal-footer">
                        <button class="modal-button secondary cancel-btn">${cancelText}</button>
                        <button class="modal-button ${type === 'danger' ? 'danger' : 'primary'} confirm-btn">${confirmText}</button>
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const confirmBtn = overlay.querySelector('.confirm-btn');
            const cancelBtn = overlay.querySelector('.cancel-btn');

            const cleanup = () => {
                document.body.removeChild(overlay);
            };

            confirmBtn.addEventListener('click', () => {
                cleanup();
                resolve(true);
            });

            cancelBtn.addEventListener('click', () => {
                cleanup();
                resolve(false);
            });

            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    cleanup();
                    resolve(false);
                }
            });
        });
    }

    /**
     * Alert dialog
     */
    alert(message, title = 'Alert') {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';

            overlay.innerHTML = `
                <div class="modal info">
                    <div class="modal-header">
                        <div class="modal-icon">ℹ</div>
                        <div class="modal-title">${title}</div>
                    </div>
                    <div class="modal-body">${message}</div>
                    <div class="modal-footer">
                        <button class="modal-button primary ok-btn">OK</button>
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const okBtn = overlay.querySelector('.ok-btn');

            const cleanup = () => {
                document.body.removeChild(overlay);
                resolve();
            };

            okBtn.addEventListener('click', cleanup);

            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    cleanup();
                }
            });
        });
    }
}

// Export singleton instance
const notification = new NotificationService();

// Make available globally
window.notification = notification;

export default notification;
