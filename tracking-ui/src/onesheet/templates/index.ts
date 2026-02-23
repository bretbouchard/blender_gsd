/**
 * 1-Sheet Template Router
 *
 * Routes to the appropriate template based on item category.
 */

import type { OneSheetData } from '../types';
import { generateBaseHTML } from './base';
import { generateCharacterHTML } from './character';
import { generatePropHTML } from './prop';
import { generateShotHTML } from './shot';

// Template map - routes categories to their specific templates
const templates: Record<string, (data: OneSheetData) => string> = {
  character: generateCharacterHTML,
  prop: generatePropHTML,
  wardrobe: generateBaseHTML,
  set: generateBaseHTML,
  shot: generateShotHTML,
  asset: generateBaseHTML,
  audio: generateBaseHTML,
};

/**
 * Generate a 1-sheet HTML for the given data.
 * Routes to category-specific template if available.
 */
export function generateOneSheet(data: OneSheetData): string {
  const template = templates[data.item.category] || generateBaseHTML;
  return template(data);
}

export { generateBaseHTML, generateCharacterHTML, generatePropHTML, generateShotHTML };
