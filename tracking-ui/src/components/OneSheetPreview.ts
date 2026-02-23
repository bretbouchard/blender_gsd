/**
 * 1-Sheet Preview Component
 *
 * Modal preview of 1-sheet with export options.
 */

import type { TrackingItem } from '../types';
import { getOneSheetGenerator } from '../onesheet/generator';
import { items } from '../store';

// Add styles for the preview modal
const styles = `
.onesheet-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.onesheet-modal.hidden {
  display: none;
}

.onesheet-preview {
  background: #1a1a2e;
  border-radius: 12px;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #2a2a4a;
}

.preview-header h2 {
  font-size: 1.25rem;
  color: #eaeaea;
}

.preview-close {
  background: none;
  border: none;
  color: #888;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem;
}

.preview-close:hover {
  color: #fff;
}

.preview-frame {
  border: none;
  flex: 1;
  min-height: 500px;
  background: #1a1a2e;
}

.preview-actions {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #2a2a4a;
}

.preview-actions button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-html {
  background: #3498db;
  color: white;
}

.btn-html:hover {
  background: #2980b9;
}

.btn-pdf {
  background: #e74c3c;
  color: white;
}

.btn-pdf:hover {
  background: #c0392b;
}

.btn-close {
  background: #333;
  color: #888;
  margin-left: auto;
}

.btn-close:hover {
  background: #444;
  color: #fff;
}
`;

// Inject styles
if (typeof document !== 'undefined' && !document.getElementById('onesheet-styles')) {
  const styleEl = document.createElement('style');
  styleEl.id = 'onesheet-styles';
  styleEl.textContent = styles;
  document.head.appendChild(styleEl);
}

/**
 * Create the 1-sheet preview component.
 */
export function OneSheetPreview(item: TrackingItem): HTMLElement {
  const generator = getOneSheetGenerator(() => items.get());
  const html = generator.generateHTML(item);

  const container = document.createElement('div');
  container.className = 'onesheet-preview';

  // Header
  const header = document.createElement('div');
  header.className = 'preview-header';
  header.innerHTML = `
    <h2>1-Sheet: ${item.name}</h2>
    <button class="preview-close" aria-label="Close">&times;</button>
  `;

  // Preview iframe
  const iframe = document.createElement('iframe');
  iframe.className = 'preview-frame';
  iframe.srcdoc = html;

  // Actions
  const actions = document.createElement('div');
  actions.className = 'preview-actions';
  actions.innerHTML = `
    <button class="btn-html">Download HTML</button>
    <button class="btn-pdf">Print PDF</button>
    <button class="btn-close">Close</button>
  `;

  // Event handlers
  header.querySelector('.preview-close')?.addEventListener('click', () => {
    closeModal();
  });

  actions.querySelector('.btn-html')?.addEventListener('click', () => {
    generator.downloadHTML(item);
  });

  actions.querySelector('.btn-pdf')?.addEventListener('click', () => {
    generator.printPDF(item);
  });

  actions.querySelector('.btn-close')?.addEventListener('click', () => {
    closeModal();
  });

  container.appendChild(header);
  container.appendChild(iframe);
  container.appendChild(actions);

  return container;
}

let currentModal: HTMLElement | null = null;

/**
 * Show 1-sheet preview modal.
 */
export function showOneSheetPreview(item: TrackingItem): void {
  // Close existing modal if any
  closeModal();

  // Create modal
  const modal = document.createElement('div');
  modal.className = 'onesheet-modal';
  modal.appendChild(OneSheetPreview(item));

  // Close on backdrop click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  // Close on Escape key
  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      closeModal();
      document.removeEventListener('keydown', handleEscape);
    }
  };
  document.addEventListener('keydown', handleEscape);

  document.body.appendChild(modal);
  currentModal = modal;
}

/**
 * Close the 1-sheet preview modal.
 */
export function closeModal(): void {
  if (currentModal) {
    currentModal.remove();
    currentModal = null;
  }
}
