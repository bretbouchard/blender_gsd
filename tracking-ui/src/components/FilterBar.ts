/**
 * Filter Bar Component
 *
 * Provides filtering and view switching controls.
 */

import { config, filters, view } from '../store';
import type { Status, Category, ViewMode } from '../types';

export function FilterBar(): HTMLElement {
  const container = document.createElement('div');
  container.className = 'filter-bar';

  function render() {
    const cfg = config.get();
    const currentFilters = filters.get();
    const currentView = view.get();

    container.innerHTML = `
      <div class="filters">
        <select id="status-filter" title="Filter by status">
          <option value="">All Statuses</option>
          ${cfg?.statuses.map(s => `
            <option value="${s.id}" ${currentFilters.status === s.id ? 'selected' : ''}>
              ${s.name}
            </option>
          `).join('') || ''}
        </select>

        <select id="category-filter" title="Filter by category">
          <option value="">All Categories</option>
          ${cfg?.categories.map(c => `
            <option value="${c.id}" ${currentFilters.category === c.id ? 'selected' : ''}>
              ${c.name}
            </option>
          `).join('') || ''}
        </select>

        <input
          type="text"
          id="search"
          placeholder="Search items..."
          value="${currentFilters.search || ''}"
          title="Search by name, ID, or description"
        />

        <button id="clear-filters" class="btn-clear" title="Clear all filters">
          ✕ Clear
        </button>
      </div>

      <div class="view-toggle">
        <button class="${currentView === 'kanban' ? 'active' : ''}" data-view="kanban" title="Board view">
          ▦ Board
        </button>
        <button class="${currentView === 'table' ? 'active' : ''}" data-view="table" title="Table view">
          ☰ Table
        </button>
      </div>
    `;

    // Status filter handler
    container.querySelector('#status-filter')?.addEventListener('change', (e) => {
      const value = (e.target as HTMLSelectElement).value as Status;
      filters.set({ ...currentFilters, status: value || undefined });
    });

    // Category filter handler
    container.querySelector('#category-filter')?.addEventListener('change', (e) => {
      const value = (e.target as HTMLSelectElement).value as Category;
      filters.set({ ...currentFilters, category: value || undefined });
    });

    // Search handler with debounce
    let searchTimeout: number;
    container.querySelector('#search')?.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = window.setTimeout(() => {
        const value = (e.target as HTMLInputElement).value;
        filters.set({ ...currentFilters, search: value || undefined });
      }, 200);
    });

    // Clear filters button
    container.querySelector('#clear-filters')?.addEventListener('click', () => {
      filters.set({});
      // Reset form elements
      (container.querySelector('#status-filter') as HTMLSelectElement).value = '';
      (container.querySelector('#category-filter') as HTMLSelectElement).value = '';
      (container.querySelector('#search') as HTMLInputElement).value = '';
    });

    // View toggle buttons
    container.querySelectorAll('[data-view]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const newView = (e.target as HTMLElement).dataset.view as ViewMode;
        view.set(newView);
      });
    });
  }

  // Initial render
  render();

  // Subscribe to config changes
  config.subscribe(render);

  return container;
}
