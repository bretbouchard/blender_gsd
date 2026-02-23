/**
 * Shot 1-Sheet Template
 *
 * Template for shot/sequence assets.
 */

import { generateBaseHTML } from './base';
import type { OneSheetData } from '../types';

export function generateShotHTML(data: OneSheetData): string {
  // For now, use base template
  // Future: Add shot-specific sections like scene info, duration, camera specs, etc.
  return generateBaseHTML(data);
}
