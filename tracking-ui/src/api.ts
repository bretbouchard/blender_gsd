/**
 * API Layer for Production Tracking
 *
 * Loads YAML data files using Vite's glob imports.
 * This is read-only - AI handles writes to YAML files.
 */

import type { TrackingItem, TrackingConfig, Blocker } from './types';

/**
 * Load configuration (categories and statuses)
 */
export async function loadConfig(): Promise<TrackingConfig> {
  try {
    const config = await import('../../.planning/tracking/config.yaml');
    return config.default || config;
  } catch (error) {
    console.error('Failed to load config:', error);
    // Return default config
    return {
      categories: [
        { id: 'character', name: 'Characters', color: '#3498db' },
        { id: 'wardrobe', name: 'Wardrobe', color: '#9b59b6' },
        { id: 'prop', name: 'Props', color: '#e67e22' },
        { id: 'set', name: 'Sets', color: '#27ae60' },
        { id: 'shot', name: 'Shots', color: '#e74c3c' },
        { id: 'asset', name: 'Assets', color: '#1abc9c' },
        { id: 'audio', name: 'Audio', color: '#f39c12' },
      ],
      statuses: [
        { id: 'complete', name: 'Complete', color: '#27ae60' },
        { id: 'in_progress', name: 'In Progress', color: '#f1c40f' },
        { id: 'planned', name: 'Planned', color: '#3498db' },
        { id: 'vague', name: 'Vague', color: '#95a5a6' },
        { id: 'blocked', name: 'Blocked', color: '#e74c3c' },
      ],
    };
  }
}

/**
 * Load all tracking items
 */
export async function loadItems(): Promise<TrackingItem[]> {
  const items: TrackingItem[] = [];

  try {
    // Vite glob import for all item files (must be static string)
    const modules = import.meta.glob('../../.planning/tracking/items/*.yaml');

    for (const path in modules) {
      try {
        const mod = await modules[path]();
        const item = (mod as any).default || mod;
        if (item && item.id) {
          items.push(item as TrackingItem);
        }
      } catch (err) {
        console.warn(`Failed to load item: ${path}`, err);
      }
    }
  } catch (error) {
    console.error('Failed to load items:', error);
  }

  // Sort by ID
  return items.sort((a, b) => a.id.localeCompare(b.id));
}

/**
 * Load blockers
 */
export async function loadBlockers(): Promise<Blocker[]> {
  try {
    const data = await import('../../.planning/tracking/blockers.yaml');
    const blockers = (data.default || data).blockers || [];
    return blockers as Blocker[];
  } catch (error) {
    console.error('Failed to load blockers:', error);
    return [];
  }
}

/**
 * Get item by ID
 */
export async function getItem(id: string): Promise<TrackingItem | null> {
  try {
    // Dynamic import for single item
    const modules = import.meta.glob('../../.planning/tracking/items/*.yaml');
    const path = `../../.planning/tracking/items/${id}.yaml`;
    if (path in modules) {
      const mod = await modules[path]();
      return (mod as any).default || mod;
    }
    return null;
  } catch {
    return null;
  }
}
