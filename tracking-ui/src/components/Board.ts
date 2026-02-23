/**
 * Board Component (Kanban View)
 *
 * Renders a Kanban board with columns for each status.
 */

import { config, filters, items } from '../store';
import { getFilteredItems, getItemsByStatus } from '../store';
import { ItemCard } from './ItemCard';
import type { Status } from '../types';

export function Board(): HTMLElement {
  const container = document.createElement('div');
  container.className = 'board';
  container.id = 'board';

  function render() {
    const cfg = config.get();
    const allItems = getFilteredItems();

    if (!cfg) {
      container.innerHTML = '<p class="loading-text">Loading...</p>';
      return;
    }

    container.innerHTML = '';

    // Create columns for each status
    cfg.statuses.forEach(statusConfig => {
      const statusItems = allItems.filter(i => i.status === statusConfig.id);

      const column = document.createElement('div');
      column.className = 'board-column';
      column.style.setProperty('--status-color', statusConfig.color);

      const header = document.createElement('div');
      header.className = 'column-header';
      header.innerHTML = `
        <h3>${statusConfig.name}</h3>
        <span class="count" style="background: ${statusConfig.color}">${statusItems.length}</span>
      `;
      column.appendChild(header);

      const content = document.createElement('div');
      content.className = 'column-content';

      if (statusItems.length === 0) {
        content.innerHTML = '<p class="empty-column">No items</p>';
      } else {
        statusItems.forEach(item => {
          content.appendChild(ItemCard(item));
        });
      }

      column.appendChild(content);
      container.appendChild(column);
    });

    // Add stats footer
    const stats = document.createElement('div');
    stats.className = 'board-stats';
    const total = allItems.length;
    stats.innerHTML = `<span>Total: ${total} items</span>`;
    container.appendChild(stats);
  }

  // Initial render
  render();

  // Subscribe to changes
  items.subscribe(render);
  filters.subscribe(render);

  return container;
}
