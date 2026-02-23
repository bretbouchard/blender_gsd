/**
 * Production Tracking Types
 *
 * TypeScript interfaces for the tracking system.
 * Matches YAML schema in .planning/tracking/
 */

export type Status = 'complete' | 'in_progress' | 'planned' | 'vague' | 'blocked';

export type Category =
  | 'character'
  | 'wardrobe'
  | 'prop'
  | 'set'
  | 'shot'
  | 'asset'
  | 'audio';

export interface Source {
  spec?: string;
  task?: string;
  commit?: string;
  created_by: string;
  created_at: string;
  regenerated_from?: string;
}

export interface TrackingItem {
  id: string;
  name: string;
  category: Category;
  status: Status;
  description?: string;
  source: Source;
  blockers: string[];
  depends_on: string[];
  assigned_to?: string;
  notes?: string;
  images: string[];
  onesheet?: string;
}

export interface CategoryConfig {
  id: Category;
  name: string;
  color: string;
}

export interface StatusConfig {
  id: Status;
  name: string;
  color: string;
}

export interface TrackingConfig {
  categories: CategoryConfig[];
  statuses: StatusConfig[];
}

export interface Blocker {
  id: string;
  reason: string;
  blocking_since: string;
  blocking_items: string[];
  resolution?: string;
}

export interface Filters {
  status?: Status;
  category?: Category;
  search?: string;
}

export type ViewMode = 'kanban' | 'table';
