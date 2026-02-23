/**
 * PNG Export for 1-Sheets
 *
 * Export 1-sheet as PNG image using html2canvas.
 * Note: Requires html2canvas library to be installed (optional dependency).
 */

import type { OneSheetData } from '../types';

// Type for html2canvas
type Html2CanvasFunction = (element: HTMLElement, options?: Record<string, unknown>) => Promise<HTMLCanvasElement>;

let html2canvasModule: Html2CanvasFunction | null = null;

/**
 * Load html2canvas dynamically (if available)
 */
async function loadHtml2Canvas(): Promise<Html2CanvasFunction | null> {
  if (html2canvasModule) return html2canvasModule;

  try {
    // @ts-expect-error - Dynamic import of optional dependency
    const module = await import('html2canvas');
    html2canvasModule = module.default || module;
    return html2canvasModule;
  } catch {
    console.warn('html2canvas not available. PNG export will not work.');
    return null;
  }
}

/**
 * Export an HTML element as PNG.
 * Uses html2canvas (lazy loaded).
 */
export async function exportPNG(element: HTMLElement, filename: string): Promise<void> {
  const html2canvas = await loadHtml2Canvas();

  if (!html2canvas) {
    throw new Error('PNG export requires html2canvas. Install with: npm install html2canvas');
  }

  const canvas = await html2canvas(element, {
    backgroundColor: '#1a1a2e',
    scale: 2, // High DPI
    useCORS: true,
    logging: false,
  });

  const url = canvas.toDataURL('image/png');

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

/**
 * Export 1-sheet data as PNG by rendering to a hidden element.
 */
export async function exportOneSheetPNG(data: OneSheetData): Promise<void> {
  // Create a hidden container
  const container = document.createElement('div');
  container.style.cssText = 'position: absolute; left: -9999px; top: 0;';
  document.body.appendChild(container);

  try {
    // Render 1-sheet HTML
    const { generateOneSheet } = await import('../templates');
    const html = generateOneSheet(data);

    const iframe = document.createElement('iframe');
    iframe.style.cssText = 'border: none; width: 800px; height: 1000px;';
    container.appendChild(iframe);

    iframe.contentDocument?.open();
    iframe.contentDocument?.write(html);
    iframe.contentDocument?.close();

    // Wait for images to load
    await new Promise(resolve => setTimeout(resolve, 500));

    // Capture
    if (iframe.contentDocument?.body) {
      await exportPNG(iframe.contentDocument.body, `${data.item.id}.png`);
    }
  } finally {
    document.body.removeChild(container);
  }
}
