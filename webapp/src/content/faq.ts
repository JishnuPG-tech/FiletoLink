export interface FaqItem {
  question: string;
  answer: string;
}

export const FAQS: FaqItem[] = [
  {
    question: 'How does FlashFile generate direct streaming links?',
    answer: 'When you forward or upload a document to the Telegram bot, FlashFile records its Telegram message location and file metadata in a persistent store. When someone requests the stream or download URL, the Python server pulls the specific requested byte ranges directly from Telegram servers in real-time over MTProto, forwarding HTTP 206 Partial Content streams without saving the file to server disk first.'
  },
  {
    question: 'Do I need to download files to watch them?',
    answer: 'No. You can stream videos directly inside your browser using the built-in web cinema player, or tap the 1-click external player launcher to stream directly inside VLC Mobile, MX Player, PotPlayer, or Infuse without downloading the full video first.'
  },
  {
    question: 'Why do some MKV files show a black screen or lack audio in web browsers?',
    answer: 'Standard desktop browsers (Chrome, Edge, Brave) do not include proprietary Dolby Digital (AC-3 / E-AC-3) audio decoders or 10-bit HEVC video licenses. In the FlashFile web player, you can tap "Play in VLC" or "Open M3U" to immediately launch VLC or PotPlayer with full 5.1 Dolby audio and 10-bit hardware video decoding.'
  },
  {
    question: 'What is the multi-worker client pool?',
    answer: 'Telegram enforces strict per-account download limits (FloodWait). FlashFile uses a worker pool of up to 6 Pyrogram clients running in parallel, automatically balancing streaming requests across the least-loaded worker to guarantee uninterrupted high-speed downloads.'
  },
  {
    question: 'Is there a limit on file size?',
    answer: 'FlashFile supports files up to 2 GB (standard Telegram limit) or up to 4 GB for Telegram Premium userbot accounts.'
  },
  {
    question: 'Can I generate batch links for multiple files at once?',
    answer: 'Yes. Use the /batch or /b command inside the Telegram bot. You can pass the first and last message links, and FlashFile will automatically compile a single batch link or aria2 command line for all files in the range.'
  }
];
