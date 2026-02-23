/**
 * Production Tracking - Main Bootstrap
 *
 * Initializes the app, loads data, and renders the UI.
 */

import './styles/main.css';
import { loadConfig, loadItems, loadBlockers } from './api';
import { config, items, blockers, isLoading, error, getStats } from './store';
import { FilterBar } from './components/FilterBar';
import { Board } from './components/Board';
import { BlockerPanel } from './components/BlockerPanel';
import { ItemDetail } from './components/ItemDetail';

/**
 * Initialize the application
 */
async function init() {
  const app = document.getElementById('app');

  if (!app) {
    console.error('App container not found');
    return;
  }

  try {
    isLoading.set(true);

    // Load all data in parallel
    const [cfg, allItems, allBlockers] = await Promise.all([
      loadConfig(),
      loadItems(),
      loadBlockers(),
    ]);

    // Update store
    config.set(cfg);
    items.set(allItems);
    blockers.set(allBlockers);

    // Build UI
    app.innerHTML = '';

    // Header
    const header = document.createElement('header');
    const stats = getStats();
    header.innerHTML = `
      <h1>📋 Production Tracking</h1>
      <div class="header-stats">
        <span class="header-stat">${stats.complete} complete</span>
        <span class="header-stat">${stats.in_progress} in progress</span>
        <span class="header-stat">${stats.blocked} blocked</span>
      </div>
    `;
    app.appendChild(header);

    // Filter bar
    app.appendChild(FilterBar());

    // Main content area
    const main = document.createElement('main');
    main.className = 'main-content';
    main.appendChild(Board());
    main.appendChild(BlockerPanel());
    app.appendChild(main);

    // Item detail modal (hidden by default)
    app.appendChild(ItemDetail());

    isLoading.set(false);

    console.log(`Loaded ${allItems.length} items, ${allBlockers.length} blockers`);
  } catch (err) {
    isLoading.set(false);
    error.set(err instanceof Error ? err.message : 'Failed to load data');

    app.innerHTML = `
      <div class="error-container">
        <h2>⚠️ Failed to Load</h2>
        <p>${error.get()}</p>
        <button onclick="location.reload()">Retry</button>
      </div>
    `;
  }
}

// Start app
init().catch(console.error);
