/**
 * Reactive Store for Production Tracking
 *
 * Simple signal-based reactive state management.
 * No framework dependencies - vanilla TypeScript.
 */

import type { TrackingItem, TrackingConfig, Filters, ViewMode, Blocker, Status } from './types';

type Subscriber<T> = (value: T) => void;

/**
 * Signal - Simple reactive container
 */
class Signal<T> {
  private _value: T;
  private subscribers: Subscriber<T>[] = [];

  constructor(initial: T) {
    this._value = initial;
  }

  get(): T {
    return this._value;
  }

  set(newValue: T): void {
    if (this._value === newValue) return;
    this._value = newValue;
    this.subscribers.forEach(s => s(newValue));
  }

  subscribe(fn: Subscriber<T>): () => void {
    this.subscribers.push(fn);
    // Call immediately with current value
    fn(this._value);
    // Return unsubscribe function
    return () => {
      this.subscribers = this.subscribers.filter(s => s !== fn);
    };
  }
}

// Global state signals
export const items = new Signal<TrackingItem[]>([]);
export const config = new Signal<TrackingConfig | null>(null);
export const blockers = new Signal<Blocker[]>([]);
export const filters = new Signal<Filters>({});
export const view = new Signal<ViewMode>('kanban');
export const selectedItem = new Signal<TrackingItem | null>(null);
export const isLoading = new Signal<boolean>(true);
export const error = new Signal<string | null>(null);

/**
 * Get filtered items based on current filters
 */
export function getFilteredItems(): TrackingItem[] {
  const allItems = items.get();
  const currentFilters = filters.get();

  return allItems.filter(item => {
    // Status filter
    if (currentFilters.status && item.status !== currentFilters.status) {
      return false;
    }

    // Category filter
    if (currentFilters.category && item.category !== currentFilters.category) {
      return false;
    }

    // Search filter
    if (currentFilters.search) {
      const search = currentFilters.search.toLowerCase();
      const matchId = item.id.toLowerCase().includes(search);
      const matchName = item.name.toLowerCase().includes(search);
      const matchDesc = item.description?.toLowerCase().includes(search) ?? false;
      if (!matchId && !matchName && !matchDesc) {
        return false;
      }
    }

    return true;
  });
}

/**
 * Get items by status
 */
export function getItemsByStatus(status: Status): TrackingItem[] {
  return getFilteredItems().filter(item => item.status === status);
}

/**
 * Get blocked items
 */
export function getBlockedItems(): TrackingItem[] {
  return items.get().filter(item => item.blockers.length > 0 || item.status === 'blocked');
}

/**
 * Get items that depend on a given item
 */
export function getDependentItems(itemId: string): TrackingItem[] {
  return items.get().filter(item => item.depends_on.includes(itemId));
}

/**
 * Statistics
 */
export function getStats() {
  const allItems = items.get();

  return {
    total: allItems.length,
    complete: allItems.filter(i => i.status === 'complete').length,
    in_progress: allItems.filter(i => i.status === 'in_progress').length,
    planned: allItems.filter(i => i.status === 'planned').length,
    vague: allItems.filter(i => i.status === 'vague').length,
    blocked: allItems.filter(i => i.status === 'blocked' || i.blockers.length > 0).length,
    blockers: blockers.get().length,
  };
}
