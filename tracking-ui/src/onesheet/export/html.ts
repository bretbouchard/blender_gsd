/**
 * HTML Export for 1-Sheets
 *
 * Export 1-sheet as downloadable HTML file.
 */

import type { OneSheetData } from '../types';
import { generateOneSheet } from '../templates';

/**
 * Generate HTML string for a 1-sheet.
 */
export function exportHTML(data: OneSheetData): string {
  return generateOneSheet(data);
}

/**
 * Download 1-sheet as HTML file.
 */
export function downloadHTML(data: OneSheetData): void {
  const html = exportHTML(data);
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `${data.item.id}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  URL.revokeObjectURL(url);
}

/**
 * Get the path where this 1-sheet would be saved in .gsd-state.
 * (Note: actual file writing requires server-side implementation)
 */
export function getStatePath(data: OneSheetData): string {
  return `.gsd-state/onesheets/${data.item.id}.html`;
}
