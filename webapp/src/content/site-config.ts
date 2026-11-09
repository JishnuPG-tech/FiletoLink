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
    tagline: 'Telegram File to Direct Link & Fast Downloader',
    description: 'Convert any Telegram file into a direct high-speed download link for Chrome, IDM, or any browser, plus instant 4K media streaming in VLC and MX Player.',
    botUsername: serverConfig?.bot_username || envBot?.replace('https://t.me/', '') || 'flashfilezbot',
    channelUrl: serverConfig?.channel_url || 'https://t.me/flashfilez',
    githubUrl: 'https://github.com/JishnuPG-tech',
    statusEndpoint: '/status',
  };
};

export const getTelegramBotLink = (attribution: string = 'website_hero'): string => {
  const config = getSiteConfig();
  return `https://t.me/${config.botUsername}?start=${attribution}`;
};
