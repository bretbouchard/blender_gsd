/**
 * 1-Sheet Generator Type Definitions
 *
 * Types for generating asset 1-sheets from tracking data.
 */

import type { TrackingItem } from '../types';

export interface OneSheetConfig {
  width: number;
  height: number;
  heroImageSize: { width: number; height: number };
  thumbSize: { width: number; height: number };
  showQRCode: boolean;
  showDependencies: boolean;
  theme: 'dark' | 'light';
}

export interface OneSheetData {
  item: TrackingItem;
  heroImage?: string;
  thumbnails: string[];
  dependencies: TrackingItem[];
  config: OneSheetConfig;
}

export const defaultConfig: OneSheetConfig = {
  width: 800,
  height: 1000,
  heroImageSize: { width: 800, height: 450 },
  thumbSize: { width: 180, height: 100 },
  showQRCode: true,
  showDependencies: true,
  theme: 'dark'
};

export interface BatchResult {
  id: string;
  status: 'success' | 'error';
  path?: string;
  error?: string;
}
