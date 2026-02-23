/**
 * Item Card Component
 *
 * Renders a single tracking item as a card.
 */

import type { TrackingItem } from '../types';
import { config, selectedItem } from '../store';
import { showOneSheetPreview } from './OneSheetPreview';

export function ItemCard(item: TrackingItem): HTMLElement {
  const cfg = config.get();
  const category = cfg?.categories.find(c => c.id === item.category);
  const hasBlockers = item.blockers.length > 0 || item.status === 'blocked';

  const card = document.createElement('div');
  card.className = 'item-card';
  card.dataset.id = item.id;
  card.dataset.status = item.status;

  if (hasBlockers) {
    card.classList.add('has-blockers');
  }

  card.innerHTML = `
    <div class="item-header">
      <span class="item-category" style="background: ${category?.color || '#666'}">
        ${category?.name || item.category}
      </span>
      <span class="item-id">${item.id}</span>
    </div>
    <h4 class="item-name">${escapeHtml(item.name)}</h4>
    ${item.description ? `<p class="item-description">${escapeHtml(item.description)}</p>` : ''}
    ${item.images.length > 0 ? `<img src="${item.images[0]}" class="item-thumb" alt="${item.name}" onerror="this.style.display='none'" />` : ''}
    ${hasBlockers ? `<div class="item-blocked">⚠️ ${item.blockers.length || 1} blocker(s)</div>` : ''}
    ${item.depends_on.length > 0 ? `<div class="item-deps">↳ ${item.depends_on.length} dependencies</div>` : ''}
    <div class="item-footer">
      ${item.assigned_to ? `<span class="assigned">👤 ${item.assigned_to}</span>` : ''}
      <button class="btn-onesheet" title="Generate 1-Sheet">📄</button>
    </div>
  `;

  // Main card click - select item
  card.addEventListener('click', () => {
    selectedItem.set(item);
  });

  // 1-Sheet button - stop propagation to prevent selection
  const onesheetBtn = card.querySelector('.btn-onesheet');
  onesheetBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    showOneSheetPreview(item);
  });

  return card;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
