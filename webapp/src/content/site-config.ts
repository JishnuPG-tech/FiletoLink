export interface SiteConfig {
  name: string;
  tagline: string;
  description: string;
  botUsername: string;
  channelUrl: string;
  githubUrl: string;
  statusEndpoint: string;
}

// Read injected config from window if served by server, else fallback to env / defaults
declare global {
  interface Window {
    __FLASHFILE_CONFIG__?: {
      bot_username?: string;
      server_name?: string;
      channel_url?: string;
    };
  }
}

export const getSiteConfig = (): SiteConfig => {
  const serverConfig = typeof window !== 'undefined' ? window.__FLASHFILE_CONFIG__ : undefined;
  const envBot = (import.meta as unknown as { env: Record<string, string> }).env?.VITE_TELEGRAM_BOT_URL;

  return {
    name: 'FlashFile',
    tagline: 'Lossless Telegram Media & File Streaming Engine',
    description: 'Direct HTTP byte-range video streaming, high-speed pipelines, and 1-tap external player integration powered by Telegram MTProto.',
    botUsername: serverConfig?.bot_username || envBot?.replace('https://t.me/', '') || 'flashfilezbot',
    channelUrl: serverConfig?.channel_url || 'https://t.me/Thunder_Updates',
    githubUrl: 'https://github.com/JishnuPG-tech/FiletoLink',
    statusEndpoint: '/status',
  };
};

export const getTelegramBotLink = (attribution: string = 'website_hero'): string => {
  const config = getSiteConfig();
  return `https://t.me/${config.botUsername}?start=${attribution}`;
};
