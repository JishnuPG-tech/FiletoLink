export interface FeatureItem {
  id: string;
  badge: string;
  title: string;
  description: string;
  metric?: string;
  metricLabel?: string;
}

export const VERIFIED_CAPABILITIES: FeatureItem[] = [
  {
    id: 'streaming',
    badge: 'HTTP 206 Partial Content',
    title: 'Lossless Byte-Range Streaming',
    description: 'Direct seekable streaming pipeline directly from Telegram data centers to modern browser players with sub-150ms buffer onset.',
    metric: '1000',
    metricLabel: 'Max Transmissions',
  },
  {
    id: 'multiclient',
    badge: 'Multi-Worker Pool',
    title: '6x Parallel Telegram MTProto Workers',
    description: 'Dynamic workload distribution across six independent userbot sessions to prevent FloodWait rate limits and maximize bandwidth.',
    metric: '6 Nodes',
    metricLabel: 'Worker Clients',
  },
  {
    id: 'cinema',
    badge: 'Obsidian Ember',
    title: 'Clean Web Cinema & External App Sync',
    description: 'Hardware accelerated in-browser playback paired with 1-tap deep links for VLC, MX Player, PotPlayer, Infuse, and M3U playlists.',
    metric: '1-Tap',
    metricLabel: 'App Integration',
  },
  {
    id: 'batch',
    badge: 'Batch Queue',
    title: 'Multi-File & Batch Generation',
    description: 'Easily bundle ranges of stored documents into single streaming playlists or bulk aria2 command exports for automated downstream fetching.',
    metric: '50 Files',
    metricLabel: 'Max Batch Size',
  },
  {
    id: 'security',
    badge: 'Canonical File Hash',
    title: 'Secure Hash File Identification',
    description: 'Files are indexed and addressed using cryptographically verifiable secure hash IDs, preventing unauthorized enumeration and link scraping.',
    metric: 'SHA-256',
    metricLabel: 'Integrity Check',
  },
  {
    id: 'autopilot',
    badge: 'Automated Operations',
    title: 'Weekly Milestones & Channel Health',
    description: 'Autonomous Sunday night server milestone performance reporting and scheduled TMDB OTT media syndication into connected Telegram channels.',
    metric: '24/7',
    metricLabel: 'Health Monitoring',
  },
];
