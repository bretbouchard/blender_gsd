/**
 * 1-Sheet Generator Service
 *
 * Main service for generating and exporting 1-sheets.
 */

import type { TrackingItem } from '../types';
import type { OneSheetData, OneSheetConfig, BatchResult } from './types';
import { defaultConfig } from './types';
import { exportHTML, downloadHTML, exportPDF } from './export';

/**
 * 1-Sheet Generator class.
 * Generates 1-sheet data and exports in various formats.
 */
export class OneSheetGenerator {
  private config: OneSheetConfig;
  private allItems: () => TrackingItem[];

  constructor(getItems: () => TrackingItem[], config: Partial<OneSheetConfig> = {}) {
    this.config = { ...defaultConfig, ...config };
    this.allItems = getItems;
  }

  /**
   * Generate 1-sheet data from a tracking item.
   */
  generate(item: TrackingItem): OneSheetData {
    const allItems = this.allItems();

    // Resolve dependencies
    const dependencies = (item.depends_on || [])
      .map(id => allItems.find(i => i.id === id))
      .filter(Boolean) as TrackingItem[];

    // Determine hero image (first image or undefined)
    const heroImage = item.images?.[0];

    // Thumbnails (remaining images, up to 4)
    const thumbnails = (item.images || []).slice(1, 5);

    return {
      item,
      heroImage,
      thumbnails,
      dependencies,
      config: this.config
    };
  }

  /**
   * Generate HTML string for a 1-sheet.
   */
  generateHTML(item: TrackingItem): string {
    const data = this.generate(item);
    return exportHTML(data);
  }

  /**
   * Download 1-sheet as HTML file.
   */
  downloadHTML(item: TrackingItem): void {
    const data = this.generate(item);
    downloadHTML(data);
  }

  /**
   * Print 1-sheet to PDF via browser print dialog.
   */
  printPDF(item: TrackingItem): void {
    const data = this.generate(item);
    exportPDF(data);
  }

  /**
   * Generate 1-sheets for all items.
   */
  generateAll(): BatchResult[] {
    const allItems = this.allItems();
    const results: BatchResult[] = [];

    for (const item of allItems) {
      try {
        this.generate(item);
        results.push({
          id: item.id,
          status: 'success',
          path: `.gsd-state/onesheets/${item.id}.html`
        });
      } catch (error) {
        results.push({
          id: item.id,
          status: 'error',
          error: String(error)
        });
      }
    }

    return results;
  }
}

// Singleton will be created in main.ts after store is available
let _instance: OneSheetGenerator | null = null;

/**
 * Get the singleton 1-sheet generator instance.
 */
export function getOneSheetGenerator(getItems: () => TrackingItem[]): OneSheetGenerator {
  if (!_instance) {
    _instance = new OneSheetGenerator(getItems);
  }
  return _instance;
}

/**
 * Reset the singleton (for testing).
 */
export function resetGenerator(): void {
  _instance = null;
}
