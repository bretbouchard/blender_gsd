/**
 * Prop 1-Sheet Template
 *
 * Template for prop assets.
 */

import { generateBaseHTML } from './base';
import type { OneSheetData } from '../types';

export function generatePropHTML(data: OneSheetData): string {
  // For now, use base template
  // Future: Add prop-specific sections like materials, dimensions, etc.
  return generateBaseHTML(data);
}
