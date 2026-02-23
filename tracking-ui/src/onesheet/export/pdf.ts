/**
 * PDF Export for 1-Sheets
 *
 * Export 1-sheet as PDF via browser print dialog.
 */

import type { OneSheetData } from '../types';
import { generateOneSheet } from '../templates';

/**
 * Open 1-sheet in new window for printing to PDF.
 */
export function exportPDF(data: OneSheetData): void {
  const html = generateOneSheet(data);

  // Open in new window for printing
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups to print 1-sheets');
    return;
  }

  printWindow.document.write(html);
  printWindow.document.close();

  // Trigger print after content loads
  printWindow.onload = () => {
    setTimeout(() => {
      printWindow.print();
    }, 250);
  };
}

/**
 * Print current window (for use when 1-sheet is already displayed).
 */
export function printCurrent(): void {
  window.print();
}
