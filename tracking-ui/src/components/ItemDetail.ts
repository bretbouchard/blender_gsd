/**
 * Item Detail Modal Component
 *
 * Shows full details for a selected item.
 */

import { selectedItem, config } from '../store';
import type { TrackingItem } from '../types';

export function ItemDetail(): HTMLElement {
  const container = document.createElement('div');
  container.className = 'item-detail-overlay';
  container.style.display = 'none';

  function render() {
    const item = selectedItem.get();
    const cfg = config.get();

    if (!item) {
      container.style.display = 'none';
      return;
    }

    container.style.display = 'flex';

    const category = cfg?.categories.find(c => c.id === item.category);
    const status = cfg?.statuses.find(s => s.id === item.status);

    container.innerHTML = `
      <div class="item-detail-modal">
        <button class="close-btn" title="Close">✕</button>

        <div class="detail-header">
          <span class="detail-category" style="background: ${category?.color}">
            ${category?.name}
          </span>
          <span class="detail-status" style="background: ${status?.color}">
            ${status?.name}
          </span>
        </div>

        <h2 class="detail-id">${item.id}</h2>
        <h3 class="detail-name">${escapeHtml(item.name)}</h3>

        ${item.description ? `
          <p class="detail-description">${escapeHtml(item.description)}</p>
        ` : ''}

        ${item.images.length > 0 ? `
          <div class="detail-images">
            ${item.images.map((img, i) => `
              <img src="${img}" alt="${item.name} image ${i + 1}"
                   class="detail-image"
                   onerror="this.style.display='none'" />
            `).join('')}
          </div>
        ` : ''}

        <div class="detail-meta">
          <div class="meta-row">
            <span class="meta-label">Created by:</span>
            <span class="meta-value">${item.source.created_by}</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">Created at:</span>
            <span class="meta-value">${item.source.created_at}</span>
          </div>
          ${item.assigned_to ? `
            <div class="meta-row">
              <span class="meta-label">Assigned to:</span>
              <span class="meta-value">${item.assigned_to}</span>
            </div>
          ` : ''}
          ${item.source.spec ? `
            <div class="meta-row">
              <span class="meta-label">Source:</span>
              <a href="${item.source.spec}" class="meta-link" target="_blank">
                ${item.source.spec} →
              </a>
            </div>
          ` : ''}
        </div>

        ${item.blockers.length > 0 ? `
          <div class="detail-section">
            <h4>⚠️ Blockers</h4>
            <ul class="detail-blockers">
              ${item.blockers.map(b => `<li>${escapeHtml(b)}</li>`).join('')}
            </ul>
          </div>
        ` : ''}

        ${item.depends_on.length > 0 ? `
          <div class="detail-section">
            <h4>↳ Dependencies</h4>
            <ul class="detail-deps">
              ${item.depends_on.map(d => `<li>${d}</li>`).join('')}
            </ul>
          </div>
        ` : ''}

        ${item.notes ? `
          <div class="detail-section">
            <h4>📝 Notes</h4>
            <p class="detail-notes">${escapeHtml(item.notes)}</p>
          </div>
        ` : ''}

        ${item.onesheet ? `
          <div class="detail-actions">
            <a href="${item.onesheet}" class="btn-onesheet" target="_blank">
              View 1-Sheet →
            </a>
          </div>
        ` : ''}
      </div>
    `;

    // Close button handler
    container.querySelector('.close-btn')?.addEventListener('click', () => {
      selectedItem.set(null);
    });

    // Click outside to close
    container.addEventListener('click', (e) => {
      if (e.target === container) {
        selectedItem.set(null);
      }
    });

    // Escape key to close
    const handleKeydown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        selectedItem.set(null);
        document.removeEventListener('keydown', handleKeydown);
      }
    };
    document.addEventListener('keydown', handleKeydown);
  }

  // Initial render
  render();

  // Subscribe to selected item changes
  selectedItem.subscribe(render);

  return container;
}

function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
