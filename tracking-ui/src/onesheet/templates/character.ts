/**
 * Character 1-Sheet Template
 *
 * Extended template for character assets with potential
 * additional fields like actor, costume, etc.
 */

import { generateBaseHTML } from './base';
import type { OneSheetData } from '../types';

export function generateCharacterHTML(data: OneSheetData): string {
  // For now, use base template
  // Future: Add character-specific sections like actor info, costume notes, etc.
  return generateBaseHTML(data);
}
