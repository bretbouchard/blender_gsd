/**
 * Base 1-Sheet Template
 *
 * Generates HTML for a standard 1-sheet with hero image,
 * metadata, description, thumbnails, and dependencies.
 */

import type { OneSheetData, OneSheetConfig } from '../types';

interface CategoryInfo {
  id: string;
  name: string;
  color: string;
}

interface StatusInfo {
  id: string;
  name: string;
  color: string;
}

// Default category/status info for fallback
const defaultCategories: Record<string, CategoryInfo> = {
  character: { id: 'character', name: 'Character', color: '#3498db' },
  prop: { id: 'prop', name: 'Prop', color: '#9b59b6' },
  wardrobe: { id: 'wardrobe', name: 'Wardrobe', color: '#e91e63' },
  set: { id: 'set', name: 'Set', color: '#795548' },
  shot: { id: 'shot', name: 'Shot', color: '#ff9800' },
  asset: { id: 'asset', name: 'Asset', color: '#607d8b' },
  audio: { id: 'audio', name: 'Audio', color: '#4caf50' },
};

const defaultStatuses: Record<string, StatusInfo> = {
  todo: { id: 'todo', name: 'Todo', color: '#9e9e9e' },
  in_progress: { id: 'in_progress', name: 'In Progress', color: '#2196f3' },
  review: { id: 'review', name: 'Review', color: '#ff9800' },
  done: { id: 'done', name: 'Done', color: '#4caf50' },
  blocked: { id: 'blocked', name: 'Blocked', color: '#f44336' },
};

export function generateBaseHTML(data: OneSheetData): string {
  const { item, heroImage, thumbnails, dependencies, config: cfg } = data;

  const category = defaultCategories[item.category] || { id: item.category, name: item.category, color: '#666' };
  const status = defaultStatuses[item.status] || { id: item.status, name: item.status, color: '#666' };

  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(item.name)} - 1-Sheet</title>
  <style>
    ${generateStyles(cfg)}
  </style>
</head>
<body>
  <div class="onesheet" style="width: ${cfg.width}px;">
    ${heroImage ? `
      <div class="hero-image">
        <img src="${escapeHtml(heroImage)}" alt="${escapeHtml(item.name)}" />
      </div>
    ` : `
      <div class="hero-placeholder">
        <span>No Image</span>
      </div>
    `}

    <div class="content">
      <header class="header">
        <div class="title-block">
          <h1 class="name">${escapeHtml(item.name)}</h1>
          <span class="id">${escapeHtml(item.id)}</span>
        </div>
        <div class="badges">
          <span class="category" style="background: ${category.color}">${escapeHtml(category.name)}</span>
          <span class="status" style="background: ${status.color}">${escapeHtml(status.name)}</span>
        </div>
      </header>

      ${item.description ? `
        <section class="description">
          <h2>Description</h2>
          <p>${escapeHtml(item.description)}</p>
        </section>
      ` : ''}

      ${thumbnails.length > 0 ? `
        <section class="thumbnails">
          ${thumbnails.map(t => `
            <img src="${escapeHtml(t)}" class="thumb" alt="thumbnail" />
          `).join('')}
        </section>
      ` : ''}

      ${cfg.showDependencies && dependencies.length > 0 ? `
        <section class="dependencies">
          <h2>Dependencies</h2>
          <ul>
            ${dependencies.map(dep => `
              <li>
                <span class="dep-id">${escapeHtml(dep.id)}</span>
                <span class="dep-name">${escapeHtml(dep.name)}</span>
              </li>
            `).join('')}
          </ul>
        </section>
      ` : ''}

      <footer class="footer">
        <div class="source">
          <span>Source:</span>
          ${item.source?.spec ? `<span class="source-path">${escapeHtml(item.source.spec)}</span>` : '<span>N/A</span>'}
        </div>
        <div class="meta">
          ${item.source?.created_at ? `Created: ${escapeHtml(item.source.created_at)}` : ''}
          ${item.source?.created_by ? ` by ${escapeHtml(item.source.created_by)}` : ''}
        </div>
        ${cfg.showQRCode ? `
          <div class="qr-placeholder">
            [QR: ${escapeHtml(item.id)}]
          </div>
        ` : ''}
        <div class="project">blender_gsd</div>
      </footer>
    </div>
  </div>
</body>
</html>
  `.trim();
}

function generateStyles(cfg: OneSheetConfig): string {
  const colors = cfg.theme === 'dark'
    ? { bg: '#1a1a2e', fg: '#eaeaea', muted: '#888', card: '#16213e', border: '#2a2a4a', accent: '#3498db' }
    : { bg: '#f5f5f5', fg: '#1a1a2e', muted: '#666', card: '#ffffff', border: '#ddd', accent: '#3498db' };

  return `
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: ${colors.bg};
      color: ${colors.fg};
      display: flex;
      justify-content: center;
      padding: 2rem;
      line-height: 1.5;
    }

    .onesheet {
      background: ${colors.card};
      border: 1px solid ${colors.border};
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    .hero-image {
      width: 100%;
      height: ${cfg.heroImageSize.height}px;
      overflow: hidden;
      background: ${colors.bg};
    }

    .hero-image img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .hero-placeholder {
      width: 100%;
      height: ${cfg.heroImageSize.height}px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: ${colors.bg};
      color: ${colors.muted};
      font-size: 1.5rem;
    }

    .content {
      padding: 1.5rem;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid ${colors.border};
    }

    .title-block {
      flex: 1;
    }

    .name {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 0.25rem;
      color: ${colors.fg};
    }

    .id {
      font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
      font-size: 0.875rem;
      color: ${colors.muted};
    }

    .badges {
      display: flex;
      gap: 0.5rem;
      flex-shrink: 0;
    }

    .category, .status {
      padding: 0.25rem 0.75rem;
      border-radius: 4px;
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 500;
      color: white;
    }

    .description {
      margin-bottom: 1.5rem;
    }

    .description h2 {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: ${colors.muted};
      margin-bottom: 0.5rem;
    }

    .description p {
      font-size: 0.9375rem;
      line-height: 1.6;
      color: ${colors.fg};
    }

    .thumbnails {
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
      overflow-x: auto;
      padding-bottom: 0.5rem;
    }

    .thumb {
      width: ${cfg.thumbSize.width}px;
      height: ${cfg.thumbSize.height}px;
      object-fit: cover;
      border-radius: 4px;
      border: 1px solid ${colors.border};
      flex-shrink: 0;
    }

    .dependencies {
      margin-bottom: 1.5rem;
    }

    .dependencies h2 {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: ${colors.muted};
      margin-bottom: 0.5rem;
    }

    .dependencies ul {
      list-style: none;
    }

    .dependencies li {
      padding: 0.5rem 0.75rem;
      background: ${colors.bg};
      border-radius: 4px;
      margin-bottom: 0.25rem;
      font-size: 0.875rem;
    }

    .dep-id {
      font-family: 'SF Mono', 'Monaco', monospace;
      color: ${colors.accent};
      margin-right: 0.75rem;
    }

    .dep-name {
      color: ${colors.fg};
    }

    .footer {
      border-top: 1px solid ${colors.border};
      padding-top: 1rem;
      font-size: 0.75rem;
      color: ${colors.muted};
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      align-items: center;
    }

    .source {
      display: flex;
      gap: 0.25rem;
    }

    .source-path {
      font-family: monospace;
      color: ${colors.accent};
    }

    .qr-placeholder {
      margin-left: auto;
      background: ${colors.bg};
      padding: 0.5rem;
      border-radius: 4px;
      font-family: monospace;
      font-size: 0.625rem;
    }

    .project {
      width: 100%;
      text-align: center;
      margin-top: 0.5rem;
      font-weight: 500;
      padding-top: 0.5rem;
      border-top: 1px dashed ${colors.border};
    }

    @media print {
      body {
        padding: 0;
        background: white;
      }
      .onesheet {
        box-shadow: none;
        border: none;
      }
    }
  `;
}

function escapeHtml(text: string): string {
  const escapeMap: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, char => escapeMap[char]);
}
