export interface FaqItem {
  question: string;
  answer: string;
}

export const FAQS: FaqItem[] = [
  {
    question: 'Why is downloading directly inside the Telegram app so slow?',
    answer: 'The official Telegram mobile app throttles background downloads, limits concurrent TCP streams per file, and often freezes or cancels when you switch apps or close the chat. FlashFile generates a direct HTTP link that connects to our 6-worker MTProto pool, allowing your browser or download manager (like IDM or 1DM) to download with multi-threaded parallel connections at your full ISP bandwidth.',
  },
  {
    question: 'How does streaming help me check the movie before downloading?',
    answer: 'Large movie files often have multiple releases: theatre prints, cam rips, original language, or regional dubs (Malayalam, Tamil, Telugu, Hindi). Rather than waiting hours to download a 3GB file only to discover poor audio or wrong dubbing, FlashFile lets you click Play instantly to verify audio sync, multi-audio tracks, subtitle availability, and visual print quality within seconds.',
  },
  {
    question: 'Can I stream movies without downloading them to my phone storage?',
    answer: 'Yes! The generated stream link allows full real-time seeking and playback directly in your web browser, or via 1-tap in external media players like VLC Mobile and MX Player. You can watch full-length 1080p and 4K movies with zero storage space occupied on your device.',
  },
  {
    question: 'What happens if my internet disconnects or my download pauses?',
    answer: 'FlashFile implements standard HTTP 206 Partial Content byte-range headers. This means your download is 100% resumable in all modern browsers and download managers (IDM, 1DM, ADM, aria2). When your connection restores, the download resumes exactly where it stopped without restarting from 0%.',
  },
  {
    question: 'How do I use FlashFile?',
    answer: 'Simply open @flashfilezbot on Telegram and forward or upload any video, audio, or document file up to 4 GB. Within seconds, the bot replies with your high-speed direct download link, in-browser streaming player link, and 1-tap mobile player launcher shortcuts.',
  },
];
