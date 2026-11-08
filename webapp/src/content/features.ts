export interface VerifiedFeature {
  id: string;
  badge: string;
  title: string;
  description: string;
  metric?: string;
  metricLabel?: string;
}

export const VERIFIED_CAPABILITIES: VerifiedFeature[] = [
  {
    id: 'tg-to-link',
    badge: 'Core Engine',
    title: 'Instant Telegram-to-Link Conversion',
    description: 'Transform any Telegram file, document, or movie up to 4 GB into a direct, high-speed HTTP link. No waiting for Telegram client queueing.',
    metric: '< 1s',
    metricLabel: 'Link Generation',
  },
  {
    id: 'stream-no-download',
    badge: 'Zero Storage Needed',
    title: 'Stream Movies Without Downloading',
    description: 'Play videos instantly in your browser or mobile player. Save gigabytes of internal device storage by streaming directly on demand.',
    metric: '100%',
    metricLabel: 'Cloud Streaming',
  },
  {
    id: 'audio-print-verify',
    badge: 'Quality Check',
    title: 'Verify Audio Dubbing & Video Print',
    description: 'Never waste hours downloading the wrong print. Instantly preview the file to check audio clarity, Malayalam/Tamil/Hindi dubbing, and video quality.',
    metric: 'Instant',
    metricLabel: 'Voice & Print Check',
  },
  {
    id: 'resumable-downloads',
    badge: 'HTTP 206 Byte-Range',
    title: '100% Resumable in IDM, 1DM & ADM',
    description: 'Bypass Telegram app crashes and 50% download freezes. Pause, resume, and multi-thread your downloads using your favorite download manager.',
    metric: 'Zero Loss',
    metricLabel: 'Broken Link Immunity',
  },
  {
    id: 'background-freedom',
    badge: 'Uninterrupted',
    title: 'No App Close Aborts',
    description: 'Closing Telegram or switching chats won\'t stop your downloads. Once generated, your direct download link lives in your browser or download app.',
    metric: '24/7',
    metricLabel: 'Independent Download',
  },
  {
    id: 'player-launchers',
    badge: 'Hardware Acceleration',
    title: '1-Tap VLC & MX Player Integration',
    description: 'One tap launches VLC Mobile or MX Player with full hardware acceleration, multi-audio language track selection, and Dolby AC-3 support.',
    metric: '1-Tap',
    metricLabel: 'Native App Launch',
  },
];
