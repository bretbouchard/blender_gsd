/**
 * Blocker Panel Component
 *
 * Shows all blocked items and active blockers.
 */

import { items, blockers } from '../store';
import { getBlockedItems, getStats } from '../store';

export function BlockerPanel(): HTMLElement {
  const container = document.createElement('div');
  container.className = 'blocker-panel';

  function render() {
    const stats = getStats();
    const blockedItems = getBlockedItems();
    const allBlockers = blockers.get();

    container.innerHTML = `
      <h3>⚠️ Blockers</h3>

      <div class="stats-summary">
        <span class="stat blocked">${stats.blocked} blocked</span>
        <span class="stat total">${stats.total} total</span>
      </div>

      ${blockedItems.length === 0
        ? '<p class="empty">No blockers! 🎉</p>'
        : `
          <ul class="blocker-list">
            ${blockedItems.map(item => `
              <li class="blocker-item" data-id="${item.id}">
                <div class="blocker-header">
                  <strong>${item.id}</strong>
                  <span class="blocker-name">${escapeHtml(item.name)}</span>
                </div>
                ${item.blockers.length > 0
                  ? `<ul class="blocker-reasons">
                      ${item.blockers.map(b => `<li>${escapeHtml(b)}</li>`).join('')}
                    </ul>`
                  : '<p class="blocker-reason">Status: blocked</p>'
                }
              </li>
            `).join('')}
          </ul>
        `
      }

      ${allBlockers.length > 0 ? `
        <div class="blocker-details">
          <h4>Active Blockers</h4>
          <ul class="blocker-detail-list">
            ${allBlockers.map(b => `
              <li class="blocker-detail">
                <span class="blocker-id">${b.id}</span>
                <p class="blocker-reason">${escapeHtml(b.reason)}</p>
                <span class="blocker-since">Since: ${b.blocking_since}</span>
              </li>
            `).join('')}
          </ul>
        </div>
      ` : ''}
    `;

    // Add click handlers to blocker items
    container.querySelectorAll('.blocker-item').forEach(el => {
      el.addEventListener('click', () => {
        const id = (el as HTMLElement).dataset.id;
        // Could open item detail here
        console.log('Blocked item:', id);
      });
    });
  }

  // Initial render
  render();

  // Subscribe to changes
  items.subscribe(render);
  blockers.subscribe(render);

  return container;
}

function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
