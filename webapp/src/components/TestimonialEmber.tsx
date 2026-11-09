
import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { motion } from "framer-motion";

export interface TestimonialItem {
  quote: string;
  name: string;
  role: string;
  company?: string;
  rating?: number;
  date?: string;
  photoUrl?: string;
  quality?: string;
  rawFilename?: string;
}

export interface TestimonialEmberProps {
  items?: TestimonialItem[];
  background?: string;
  padding?: number;
  printer?: {
    body?: string;
    edge?: string;
    slot?: string;
    screen?: string;
    screenText?: string;
    led?: string;
    key?: string;
    keyIcon?: string;
  };
  paper?: {
    width?: number;
    color?: string;
    ink?: string;
    soft?: string;
    padding?: number;
    lines?: number;
    header?: string;
    footer?: string;
    stars?: boolean;
    avatar?: boolean;
    mono?: boolean;
    barcode?: boolean;
  };
  run?: {
    autoplay?: boolean;
    delay?: number;
    pauseOnHover?: boolean;
    feed?: number;
    stepped?: boolean;
    tapToTear?: boolean;
    printOnView?: boolean;
  };
  style?: React.CSSProperties;
  labelFont?: React.CSSProperties;
  quoteFont?: React.CSSProperties;
  nameFont?: React.CSSProperties;
}

const DEFAULT_PRINTER = {
  body: "#1D1D21",
  edge: "rgba(255, 255, 255, 0.08)",
  slot: "#070708",
  screen: "#1F2A22",
  screenText: "#9BF0B4",
  led: "#43E07A",
  key: "#2C2C32",
  keyIcon: "#E9E9EE",
};

const DEFAULT_PAPER = {
  width: 360,
  color: "#FBFAF6",
  ink: "#1A1917",
  soft: "rgba(26, 25, 23, 0.52)",
  padding: 26,
  lines: 7,
  header: "FILE CONVERSION",
  footer: "DIRECT DOWNLOAD & STREAM · @FLASHFILEZBOT",
  stars: true,
  avatar: true,
  mono: true,
  barcode: true,
};

const DEFAULT_RUN = {
  autoplay: true,
  delay: 5,
  pauseOnHover: true,
  feed: 1.6,
  stepped: true,
  tapToTear: true,
  printOnView: true,
};

const DEFAULT_AVATARS = [
  "https://framerusercontent.com/images/GfGkADagM4KEibNcIiRUWlfrR0.jpg",
  "https://framerusercontent.com/images/aNsAT3jCvt4zglbWCUoFe33Q.jpg",
  "https://framerusercontent.com/images/BYnxEV1zjYb9bhWh1IwBZ1ZoS60.jpg",
  "https://framerusercontent.com/images/2uTNEj5aTl2K3NJaEFWMbnrA.jpg",
  "https://framerusercontent.com/images/f9RiWoNpmlCMqVRIHz8l8wYfeI.jpg",
];

const BODY_HEIGHT = 96;
const OFFSET_Y = 28;
const OFFSET_X = 44;

const clamp = (val: number, min: number, max: number) => Math.min(max, Math.max(min, val));
const mod = (n: number, m: number) => (m > 0 ? ((n % m) + m) % m : 0);
const pad = (n: number | string, len: number) => String(n).padStart(len, "0");

const isReducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;

function buildConfig(props: TestimonialEmberProps) {
  return {
    pr: { ...DEFAULT_PRINTER, ...props.printer },
    pa: { ...DEFAULT_PAPER, ...props.paper },
    ru: { ...DEFAULT_RUN, ...props.run },
  };
}

// Comprehensive Unicode emoji & pictograph pattern
const EMOJI_REGEX = /[\u{1F000}-\u{1FFFF}\u{2600}-\u{27BF}\u{2300}-\u{23FF}\u{2B50}-\u{2B55}\u{200D}\u{FE0F}\u{20E3}\u{D800}-\u{DFFF}]/gu;

export function purgeEmoji(text: string): string {
  if (!text) return "";
  return text
    .replace(EMOJI_REGEX, "")
    .replace(/^[\s\-_~•·|/\\#@!?,:;+=]+/, "")
    .replace(/[\s\-_~•·|/\\#@!?,:;+=]+$/, "")
    .trim();
}

/** Smart Telegram movie/series filename cleaner & extractor */
export function parseTelegramFilename(raw: string) {
  let clean = purgeEmoji(raw);

  const sizeMatch = clean.match(/[\(\[]?(\d+(?:\.\d+)?\s*(?:GB|MB|gb|mb))[\)\]]?/i);
  const size = sizeMatch ? sizeMatch[1].toUpperCase() : "";

  const resMatch = clean.match(/\b(2160p|4k|1080p|720p|480p|uhd|fhd|remux|imax)\b/i);
  let resolution = resMatch ? resMatch[1].toUpperCase() : "1080p";
  if (resolution === "2160P") resolution = "4K UHD";

  // Remove file extension
  clean = clean.replace(/\.(mkv|mp4|avi|webm|mov|ts|m4v|flac)$/i, "");
  // Remove channel tags like @channel, t.me/..., www...
  clean = clean.replace(/[@#][\w_]+|t\.me\/[\w_]+|https?:\/\/\S+|www\.\S+/gi, " ");
  // Remove brackets
  clean = clean.replace(/\[.*?\]|\{.*?\}/g, " ");
  clean = clean.replace(/\((?!\d{4}\)).*?\)/g, " ");
  clean = clean.replace(/[\._\-]+/g, " ").trim();

  const tvMatch = clean.match(/\b(S\d{1,2}\s*E\d{1,2}|Season\s*\d+|Episode\s*\d+|E\d{1,2})\b/i);
  const yearMatch = clean.match(/\b(19\d{2}|20\d{2})\b/);

  let title = clean;
  let yearOrEpisode = "";

  if (tvMatch && tvMatch.index !== undefined) {
    title = clean.slice(0, tvMatch.index).trim();
    yearOrEpisode = tvMatch[1].toUpperCase().replace(/\s+/g, "");
  } else if (yearMatch && yearMatch.index !== undefined) {
    title = clean.slice(0, yearMatch.index).trim();
    yearOrEpisode = `(${yearMatch[1]})`;
  } else {
    const cutMatch = clean.match(/\b(2160p|4k|1080p|720p|480p|bluray|brrip|web[\s\-]?dl|webrip|hdr|hdrip|dvd|x264|x265|hevc|aac|atmos|remux|truehd)\b/i);
    if (cutMatch && cutMatch.index !== undefined) {
      title = clean.slice(0, cutMatch.index).trim();
    }
  }

  // Strip trailing punctuation e.g. 'Jailer 2 (' -> 'Jailer 2'
  title = title.replace(/[\s\(\[\-_~:;,.|/\\]+$/g, "").replace(/^[\s\(\[\-_~:;,.|/\\]+/g, "").trim();

  // Noise words filter
  const NOISE_WORDS = new Set([
    "hindi", "tamil", "telugu", "malayalam", "kannada", "dual", "multi",
    "audio", "sub", "esub", "hc", "rip", "true", "hq", "web", "dl", "bluray",
    "brrip", "hdrip", "dvd", "x264", "x265", "hevc", "aac", "ds4k", "snxt", "mmax",
    "jhs", "extraflix", "worldfree4u", "yify", "nf", "amzn", "hotstar"
  ]);

  const words = title
    .split(/\s+/)
    .filter(w => !NOISE_WORDS.has(w.toLowerCase()))
    .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase());

  title = words.join(" ").trim();

  const cleanTitle = yearOrEpisode ? `${title} ${yearOrEpisode}`.trim() : title;
  const quality = size ? `${resolution} · ${size}` : resolution;
  const canonKey = title.toLowerCase().replace(/[^a-z0-9]/g, "") || clean.toLowerCase();

  return {
    cleanTitle: purgeEmoji(cleanTitle) || purgeEmoji(raw),
    quality,
    rawFilename: purgeEmoji(raw),
    canonKey,
  };
}

const DEFAULT_ITEMS: TestimonialItem[] = [
  {
    quote: "A user used @flashfilezbot to convert the movie Dune: Part Two (2024) to a high-speed download & stream link.",
    name: "Dune: Part Two (2024)",
    role: "Fast Download & Stream · Chrome & VLC",
    rating: 5,
    quality: "4K UHD · 4.2 GB",
    date: "08 NOV 2026",
    photoUrl: "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=120&auto=format&fit=crop&q=80",
    rawFilename: "Dune.Part.Two.2024.2160p.UHD.BluRay.x265.10bit.HDR.DDP5.1.Atmos.mkv",
  },
  {
    quote: "A user used @flashfilezbot to convert the series Breaking Bad S05E14 to a high-speed download & stream link.",
    name: "Breaking Bad S05E14",
    role: "Direct Download & Play · IDM & 1DM",
    rating: 5,
    quality: "1080p · 1.4 GB",
    date: "08 NOV 2026",
    photoUrl: "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=120&auto=format&fit=crop&q=80",
    rawFilename: "Breaking.Bad.S05E14.Ozymandias.1080p.10bit.BluRay.x265.mkv",
  },
  {
    quote: "A user used @flashfilezbot to convert the movie Interstellar (2014) to a high-speed download & stream link.",
    name: "Interstellar (2014)",
    role: "Lossless Download & Stream · Chrome",
    rating: 5,
    quality: "4K Remux · 8.6 GB",
    date: "08 NOV 2026",
    photoUrl: "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=120&auto=format&fit=crop&q=80",
    rawFilename: "Interstellar.2014.IMAX.2160p.HDR.TrueHD.7.1.x265.mkv",
  },
  {
    quote: "A user used @flashfilezbot to convert the series Severance S02E01 to a high-speed download & stream link.",
    name: "Severance S02E01",
    role: "Fast Download & Stream · Apple iOS & Safari",
    rating: 5,
    quality: "4K HDR · 2.1 GB",
    date: "08 NOV 2026",
    photoUrl: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=120&auto=format&fit=crop&q=80",
    rawFilename: "Severance.S02E01.Hello.Ms.Cobel.2160p.WEB-DL.DDP5.1.mkv",
  },
  {
    quote: "A user used @flashfilezbot to convert the movie Gladiator II (2024) to a high-speed download & stream link.",
    name: "Gladiator II (2024)",
    role: "Multi-Audio Download & Stream · MX Player",
    rating: 5,
    quality: "1080p · 2.4 GB",
    date: "08 NOV 2026",
    photoUrl: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=120&auto=format&fit=crop&q=80",
    rawFilename: "Gladiator.II.2024.1080p.WEBRip.DDP5.1.Atmos.mkv",
  },
];

function parseItems(items?: TestimonialItem[]) {
  const source = Array.isArray(items) && items.length > 0 ? items.filter(Boolean) : DEFAULT_ITEMS;
  const seenKeys = new Set<string>();
  const results: any[] = [];

  for (let i = 0; i < source.length; i++) {
    const item = source[i];
    const photo = (item.photoUrl || "").trim();
    let name = purgeEmoji(item.name || "");
    let quote = purgeEmoji(item.quote || "");
    let quality = item.quality || "";

    if (item.rawFilename && (!name || !quote)) {
      const parsed = parseTelegramFilename(item.rawFilename);
      if (!name) name = parsed.cleanTitle;
      if (!quote) quote = `A user used @flashfilezbot to convert ${parsed.cleanTitle} to a direct download and streaming link.`;
      if (!quality) quality = parsed.quality;
    }

    const key = name.toLowerCase().replace(/[^a-z0-9]/g, "");
    if (key && seenKeys.has(key)) continue;
    if (key) seenKeys.add(key);

    results.push({
      quote,
      name,
      role: item.role || "Fast Download & Stream · Chrome & VLC",
      company: item.company || "",
      quality,
      rawFilename: purgeEmoji(item.rawFilename || ""),
      rating: clamp(Math.round(item.rating ?? 5), 0, 5),
      date: item.date || "08 NOV 2026",
      face: photo || DEFAULT_AVATARS[results.length % DEFAULT_AVATARS.length],
    });
  }

  return results.length > 0 ? results : source.map((item, i) => ({
    quote: purgeEmoji(item.quote || ""),
    name: purgeEmoji(item.name || ""),
    role: item.role || "Stream Ready · VLC & MX Player",
    company: item.company || "",
    quality: item.quality || "",
    rawFilename: purgeEmoji(item.rawFilename || ""),
    rating: clamp(Math.round(item.rating ?? 5), 0, 5),
    date: item.date || "08 NOV 2026",
    face: (item.photoUrl || "").trim() || DEFAULT_AVATARS[i % DEFAULT_AVATARS.length],
  }));
}

/** Algorithmic FNV-1a barcode generator */
function generateBarcode(seed: string) {
  let hash = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    hash ^= seed.charCodeAt(i);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  const widths: number[] = [];
  for (let i = 0; i < 52; i++) {
    hash ^= hash << 13;
    hash >>>= 0;
    hash ^= hash >>> 17;
    hash ^= hash << 5;
    hash >>>= 0;
    widths.push(1 + (hash % 3));
  }
  return {
    widths,
    code: (hash >>> 0).toString(16).toUpperCase().padStart(8, "0").slice(0, 8),
  };
}

/** Stepper motor timing curve for authentic physical feed */
function getSteppedFeed(isStepped?: boolean) {
  if (!isStepped) return { y: ["-101%", "0%"], times: [0, 1] };
  const y: string[] = ["-101%"];
  const times: number[] = [0];
  const steps = 6;
  for (let i = 1; i <= steps; i++) {
    const target = -101 + (101 * i) / steps;
    const startT = (i - 1) / steps;
    const endT = i / steps;
    y.push(`${target.toFixed(2)}%`);
    times.push(startT + (endT - startT) * 0.62);
    y.push(`${target.toFixed(2)}%`);
    times.push(endT);
  }
  return { y, times };
}

function DashedPerforation({ color }: { color: string }) {
  return (
    <div
      aria-hidden="true"
      style={{
        height: 0,
        borderTop: `1.5px dashed ${color}`,
        margin: "14px 0",
        opacity: 0.7,
      }}
    />
  );
}

function SawtoothTear({ color, width }: { color: string; width: number }) {
  const count = Math.max(4, Math.round(width / 12));
  const step = width / count;
  let d = `M0 0 H${width} `;
  for (let i = count; i > 0; i--) {
    d += `L${(i - 0.5) * step} 9 L${(i - 1) * step} 0 `;
  }
  return (
    <svg width={width} height={10} viewBox={`0 0 ${width} 10`} aria-hidden="true" style={{ display: "block" }}>
      <path d={d + "Z"} fill={color} />
    </svg>
  );
}

function ArrowIcon({ back, color }: { back?: boolean; color: string }) {
  return (
    <svg width={12} height={12} viewBox="0 0 12 12" aria-hidden="true">
      <path d={back ? "M8 2 L3.5 6 L8 10 Z" : "M4 2 L8.5 6 L4 10 Z"} fill={color} />
    </svg>
  );
}

function SpeakerIcon({ muted, color }: { muted?: boolean; color: string }) {
  if (muted) {
    return (
      <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill={color} />
        <line x1="23" y1="9" x2="17" y2="15" />
        <line x1="17" y1="9" x2="23" y2="15" />
      </svg>
    );
  }
  return (
    <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill={color} />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  );
}

/** Authentic Web Audio API thermal printer sound synthesizer (motor buzz, paper friction, rip & key ticks) */
class ThermalPrinterAudio {
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private isPlaying = false;
  private muted = false;
  private activeNodes: { stop?: () => void }[] = [];

  public init() {
    if (typeof window === "undefined") return;
    try {
      if (!this.ctx) {
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        if (AudioCtx) {
          this.ctx = new AudioCtx();
        }
      }
      if (this.ctx && this.ctx.state === "suspended") {
        this.ctx.resume().catch(() => {});
      }
    } catch (e) {}
  }

  public startPrintSound(duration = 1.6) {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    this.stopPrintSound();

    try {
      const now = this.ctx.currentTime;
      const ctx = this.ctx;

      const master = ctx.createGain();
      master.gain.setValueAtTime(0.001, now);
      master.gain.linearRampToValueAtTime(0.24, now + 0.05);
      master.gain.setValueAtTime(0.24, now + Math.max(0.1, duration - 0.12));
      master.gain.exponentialRampToValueAtTime(0.0001, now + duration);
      master.connect(ctx.destination);
      this.masterGain = master;

      // 1. Stepper Motor Churn (Dual harmonic oscillators modulated by 26Hz stepping LFO)
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const lfo = ctx.createOscillator();
      const lfoGain = ctx.createGain();
      const motorFilter = ctx.createBiquadFilter();
      const motorGain = ctx.createGain();

      osc1.type = "sawtooth";
      osc1.frequency.setValueAtTime(142, now);

      lfo.type = "square";
      lfo.frequency.setValueAtTime(26, now); // Stepper line pulses
      lfoGain.gain.setValueAtTime(38, now);
      lfo.connect(lfoGain);
      lfoGain.connect(osc1.frequency);

      osc2.type = "square";
      osc2.frequency.setValueAtTime(284, now);

      motorFilter.type = "bandpass";
      motorFilter.frequency.setValueAtTime(460, now);
      motorFilter.Q.setValueAtTime(2.8, now);

      motorGain.gain.setValueAtTime(0.18, now);

      osc1.connect(motorFilter);
      osc2.connect(motorFilter);
      motorFilter.connect(motorGain);
      motorGain.connect(master);

      // 2. Paper Feed Friction / Thermal Head Sizzle (Pink noise burst)
      const sampleRate = ctx.sampleRate;
      const bufferSize = Math.floor(sampleRate * Math.min(3, duration));
      const noiseBuffer = ctx.createBuffer(1, bufferSize, sampleRate);
      const output = noiseBuffer.getChannelData(0);
      let b0 = 0, b1 = 0, b2 = 0;
      for (let i = 0; i < bufferSize; i++) {
        const white = Math.random() * 2 - 1;
        b0 = 0.99 * b0 + white * 0.05;
        b1 = 0.95 * b1 + white * 0.1;
        b2 = 0.85 * b2 + white * 0.25;
        output[i] = (b0 + b1 + b2 + white * 0.3) * 0.8;
      }

      const noiseSrc = ctx.createBufferSource();
      noiseSrc.buffer = noiseBuffer;

      const noiseFilter = ctx.createBiquadFilter();
      noiseFilter.type = "bandpass";
      noiseFilter.frequency.setValueAtTime(1600, now);
      noiseFilter.Q.setValueAtTime(1.6, now);

      const noiseGain = ctx.createGain();
      noiseGain.gain.setValueAtTime(0.14, now);

      noiseSrc.connect(noiseFilter);
      noiseFilter.connect(noiseGain);
      noiseGain.connect(master);

      osc1.start(now);
      osc2.start(now);
      lfo.start(now);
      noiseSrc.start(now);

      osc1.stop(now + duration);
      osc2.stop(now + duration);
      lfo.stop(now + duration);
      noiseSrc.stop(now + duration);

      this.activeNodes = [
        { stop: () => { try { osc1.stop(); } catch(e){} } },
        { stop: () => { try { osc2.stop(); } catch(e){} } },
        { stop: () => { try { lfo.stop(); } catch(e){} } },
        { stop: () => { try { noiseSrc.stop(); } catch(e){} } },
      ];

      this.isPlaying = true;
    } catch (e) {}
  }

  public stopPrintSound() {
    if (!this.isPlaying) return;
    this.isPlaying = false;
    if (this.masterGain && this.ctx) {
      try {
        const now = this.ctx.currentTime;
        this.masterGain.gain.cancelScheduledValues(now);
        this.masterGain.gain.setValueAtTime(this.masterGain.gain.value, now);
        this.masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.05);
      } catch (e) {}
    }
    this.activeNodes.forEach((n) => {
      try { n.stop?.(); } catch (e) {}
    });
    this.activeNodes = [];
  }

  public playTearSound() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const ctx = this.ctx;
      const duration = 0.22;
      const sampleRate = ctx.sampleRate;
      const bufferSize = Math.floor(sampleRate * duration);
      const buffer = ctx.createBuffer(1, bufferSize, sampleRate);
      const data = buffer.getChannelData(0);

      for (let i = 0; i < bufferSize; i++) {
        const decay = Math.exp(-i / (sampleRate * 0.045));
        data[i] = (Math.random() * 2 - 1) * decay;
      }

      const src = ctx.createBufferSource();
      src.buffer = buffer;

      const filter = ctx.createBiquadFilter();
      filter.type = "highpass";
      filter.frequency.setValueAtTime(1100, now);

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.32, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

      src.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      src.start(now);
    } catch (e) {}
  }

  public playClickSound() {
    if (this.muted) return;
    this.init();
    if (!this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      const ctx = this.ctx;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "triangle";
      osc.frequency.setValueAtTime(340, now);
      osc.frequency.exponentialRampToValueAtTime(110, now + 0.035);

      gain.gain.setValueAtTime(0.14, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.035);
    } catch (e) {}
  }

  public toggleMute() {
    this.muted = !this.muted;
    if (this.muted) this.stopPrintSound();
    return this.muted;
  }

  public isMuted() {
    return this.muted;
  }
}

export const printerAudio = new ThermalPrinterAudio();

if (typeof window !== "undefined") {
  const unlockAudio = () => {
    printerAudio.init();
    window.removeEventListener("pointerdown", unlockAudio);
    window.removeEventListener("touchstart", unlockAudio);
    window.removeEventListener("keydown", unlockAudio);
  };
  window.addEventListener("pointerdown", unlockAudio, { once: true, passive: true });
  window.addEventListener("touchstart", unlockAudio, { once: true, passive: true });
  window.addEventListener("keydown", unlockAudio, { once: true, passive: true });
}

function PrinterSoundButton({
  cfg,
  isMuted,
  onToggle,
}: {
  cfg: ReturnType<typeof buildConfig>;
  isMuted: boolean;
  onToggle: () => void;
}) {
  const [pressed, setPressed] = useState(false);
  return (
    <button
      type="button"
      aria-label={isMuted ? "Unmute printer sound" : "Mute printer sound"}
      title={isMuted ? "Sound: Off (click to unmute)" : "Sound: On (click to mute)"}
      onClick={() => {
        printerAudio.playClickSound();
        onToggle();
      }}
      onPointerDown={() => setPressed(true)}
      onPointerUp={() => setPressed(false)}
      onPointerLeave={() => setPressed(false)}
      style={{
        width: 34,
        height: 34,
        borderRadius: 10,
        border: "none",
        padding: 0,
        background: cfg.pr.key,
        boxShadow: pressed
          ? `inset 0 1px 0 ${cfg.pr.edge}, 0 1px 0 rgba(0,0,0,0.45)`
          : `inset 0 1px 0 ${cfg.pr.edge}, 0 3px 0 rgba(0,0,0,0.45)`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxSizing: "border-box",
        cursor: "pointer",
        transform: pressed ? "translateY(2px)" : "none",
        transition: "transform 0.08s ease, box-shadow 0.08s ease",
      }}
    >
      <SpeakerIcon muted={isMuted} color={isMuted ? "#71717A" : cfg.pr.keyIcon} />
    </button>
  );
}

function PrinterKeyButton({
  back,
  cfg,
  onPress,
}: {
  back?: boolean;
  cfg: ReturnType<typeof buildConfig>;
  onPress: () => void;
}) {
  const [pressed, setPressed] = useState(false);
  return (
    <button
      type="button"
      aria-label={back ? "Print previous testimonial" : "Print next testimonial"}
      onClick={() => {
        printerAudio.playClickSound();
        onPress();
      }}
      onPointerDown={() => setPressed(true)}
      onPointerUp={() => setPressed(false)}
      onPointerLeave={() => setPressed(false)}
      style={{
        width: 34,
        height: 34,
        borderRadius: 10,
        border: "none",
        padding: 0,
        background: cfg.pr.key,
        boxShadow: pressed
          ? `inset 0 1px 0 ${cfg.pr.edge}, 0 1px 0 rgba(0,0,0,0.45)`
          : `inset 0 1px 0 ${cfg.pr.edge}, 0 3px 0 rgba(0,0,0,0.45)`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxSizing: "border-box",
        cursor: "pointer",
        transform: pressed ? "translateY(2px)" : "none",
        transition: "transform 0.08s ease, box-shadow 0.08s ease",
      }}
    >
      <ArrowIcon back={back} color={cfg.pr.keyIcon} />
    </button>
  );
}

function ReceiptCard({
  item,
  index,
  count,
  cfg,
  labelFont,
  quoteFont,
  nameFont,
}: {
  item: ReturnType<typeof parseItems>[0];
  index: number;
  count: number;
  cfg: ReturnType<typeof buildConfig>;
  labelFont?: React.CSSProperties;
  quoteFont?: React.CSSProperties;
  nameFont?: React.CSSProperties;
}) {
  const { pa } = cfg;
  const barcode = useMemo(
    () => generateBarcode(`${item.name}|${item.quote.length}|${index}`),
    [item.name, item.quote, index]
  );
  const subtitle = [item.role, item.company].filter(Boolean).join(" · ");
  const baseLabelStyle: React.CSSProperties = {
    fontFamily: `"JetBrains Mono", ui-monospace, Menlo, Consolas, monospace`,
    fontSize: 11,
    letterSpacing: "0.08em",
    ...labelFont,
    color: pa.soft,
  };

  return (
    <div style={{ width: pa.width }}>
      <div
        style={{
          background: pa.color,
          padding: `${pa.padding + 6}px ${pa.padding}px ${pa.padding}px`,
          boxSizing: "border-box",
          boxShadow: "0 18px 30px -18px rgba(0,0,0,0.35)",
        }}
      >
        {pa.header && (
          <div
            style={{
              ...baseLabelStyle,
              color: pa.ink,
              textAlign: "center",
              letterSpacing: "0.18em",
              fontWeight: 600,
            }}
          >
            {pa.header}
          </div>
        )}
        <div style={{ ...baseLabelStyle, display: "flex", justifyContent: "space-between", marginTop: pa.header ? 10 : 0 }}>
          <span>NO. {pad(index + 1, 4)}</span>
          <span>{item.date || `${pad(index + 1, 2)} / ${pad(count, 2)}`}</span>
        </div>
        <DashedPerforation color={pa.soft} />
        {pa.stars && item.rating > 0 && (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <span
              style={{
                ...baseLabelStyle,
                color: pa.ink,
                fontSize: 15,
                letterSpacing: "0.12em",
              }}
            >
              {"★".repeat(item.rating)}
              <span style={{ color: pa.soft, opacity: 0.45 }}>{"★".repeat(5 - item.rating)}</span>
            </span>
            <span style={baseLabelStyle}>{item.quality || `${item.rating.toFixed(1)} / 5.0`}</span>
          </div>
        )}
        <p
          style={{
            fontFamily: `"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`,
            fontSize: item.quote.length > 90 ? 14 : 15,
            lineHeight: 1.5,
            ...quoteFont,
            color: pa.ink,
            margin: 0,
            overflow: "hidden",
            display: "-webkit-box",
            WebkitBoxOrient: "vertical",
            WebkitLineClamp: pa.lines,
          }}
        >
          “{item.quote}”
        </p>
        <DashedPerforation color={pa.soft} />
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {pa.avatar && (
            <img
              src={item.face}
              alt={item.name || "Portrait"}
              draggable={false}
              style={{
                width: 40,
                height: 40,
                borderRadius: 8,
                objectFit: "cover",
                display: "block",
                flex: "0 0 auto",
                filter: pa.mono ? "grayscale(1) contrast(1.15)" : undefined,
              }}
            />
          )}
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                fontFamily: `"Inter", sans-serif`,
                fontWeight: 600,
                fontSize: 14,
                ...nameFont,
                color: pa.ink,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {item.name}
            </div>
            {subtitle && (
              <div
                style={{
                  ...baseLabelStyle,
                  marginTop: 2,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {subtitle}
              </div>
            )}
          </div>
        </div>
        {pa.barcode && (
          <>
            <DashedPerforation color={pa.soft} />
            <div
              aria-hidden="true"
              style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "stretch",
                height: 38,
                overflow: "hidden",
              }}
            >
              {barcode.widths.map((w, idx) => (
                <span
                  key={idx}
                  style={{
                    width: w,
                    marginRight: barcode.widths[(idx + 7) % barcode.widths.length] > 2 ? 2 : 1,
                    background: idx % 2 === 0 ? pa.ink : "transparent",
                    display: "block",
                  }}
                />
              ))}
            </div>
            <div style={{ ...baseLabelStyle, textAlign: "center", marginTop: 6, letterSpacing: "0.3em" }}>
              {barcode.code}
            </div>
          </>
        )}
        {pa.footer && (
          <div
            style={{
              ...baseLabelStyle,
              textAlign: "center",
              marginTop: pa.barcode ? 14 : 18,
              letterSpacing: "0.16em",
              fontSize: 10,
              opacity: 0.8,
            }}
          >
            {pa.footer}
          </div>
        )}
      </div>
      <SawtoothTear color={pa.color} width={pa.width} />
    </div>
  );
}

function PrinterChassis({
  cfg,
  geo,
  screen,
  led,
  keys,
}: {
  cfg: ReturnType<typeof buildConfig>;
  geo: { bodyW: number; stageW: number; slotY: number };
  screen: React.ReactNode;
  led: React.ReactNode;
  keys: React.ReactNode;
}) {
  const { pr, pa } = cfg;
  return (
    <div
      style={{
        position: "absolute",
        left: OFFSET_X,
        top: OFFSET_Y,
        width: geo.bodyW,
        height: BODY_HEIGHT,
        borderRadius: 22,
        background: `linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 40%), ${pr.body}`,
        boxShadow: `inset 0 1px 0 ${pr.edge}, inset 0 0 0 1px ${pr.edge}, 0 22px 40px -22px rgba(0,0,0,0.55)`,
        zIndex: 3,
      }}
    >
      <div style={{ position: "absolute", left: 22, top: 20, display: "flex", alignItems: "center", gap: 12 }}>
        {led}
        <div
          style={{
            height: 30,
            minWidth: 118,
            padding: "0 12px",
            borderRadius: 8,
            background: pr.screen,
            boxShadow: "inset 0 2px 6px rgba(0,0,0,0.45)",
            display: "flex",
            alignItems: "center",
            boxSizing: "border-box",
            fontFamily: `ui-monospace, SFMono-Regular, Menlo, monospace`,
            fontSize: 12,
            letterSpacing: "0.12em",
            color: pr.screenText,
            textShadow: `0 0 6px ${pr.screenText}55`,
            whiteSpace: "nowrap",
          }}
        >
          {screen}
        </div>
      </div>
      <div style={{ position: "absolute", right: 22, top: 18, display: "flex", gap: 10 }}>{keys}</div>
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          left: (geo.bodyW - (pa.width + 20)) / 2,
          bottom: -1,
          width: pa.width + 20,
          height: 12,
          borderRadius: 6,
          background: pr.slot,
          boxShadow: "inset 0 3px 5px rgba(0,0,0,0.8)",
        }}
      />
    </div>
  );
}

export const TestimonialEmber: React.FC<TestimonialEmberProps> = (props) => {
  const cfg = buildConfig(props);
  const [liveItems, setLiveItems] = useState<TestimonialItem[] | null>(null);

  useEffect(() => {
    let active = true;
    const fetchDispatches = async () => {
      try {
        let res = await fetch("/api/live-dispatches", { cache: "no-store" });
        if (!res.ok) {
          res = await fetch("/dispatches", { cache: "no-store" });
        }
        if (!res.ok) return;
        const data = await res.json();
        if (data.ok && Array.isArray(data.dispatches) && data.dispatches.length > 0 && active) {
          const seenKeys = new Set<string>();
          const uniqueItems: TestimonialItem[] = [];

          for (let idx = 0; idx < data.dispatches.length; idx++) {
            const d = data.dispatches[idx];
            if (!d || !d.raw_filename) continue;
            const parsed = parseTelegramFilename(d.raw_filename);
            const title = parsed.cleanTitle || d.raw_filename;
            const key = parsed.canonKey || title.toLowerCase().replace(/[^a-z0-9]/g, "");
            if (!title) continue;
            if (key && seenKeys.has(key)) continue;
            if (key) seenKeys.add(key);

            const isSeries = /S\d{1,2}|Season|Episode|E\d{1,2}/i.test(d.raw_filename);
            const mediaType = isSeries ? "series" : "file";
            uniqueItems.push({
              quote: `A user used @flashfilezbot to convert ${title} to a direct download & stream link.`,
              name: title,
              role: "Fast Download & Stream · Chrome & VLC",
              quality: parsed.quality || d.file_size || "Direct Download",
              date: d.date || "TODAY",
              rawFilename: d.raw_filename,
              rating: 5,
              photoUrl: DEFAULT_AVATARS[uniqueItems.length % DEFAULT_AVATARS.length],
            });
          }

          if (uniqueItems.length > 0) {
            setLiveItems(uniqueItems);
          }
        }
      } catch {
        // Fallback gracefully
      }
    };

    fetchDispatches();
    const interval = setInterval(fetchDispatches, 10000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const items = useMemo(() => parseItems(props.items || liveItems || undefined), [props.items, liveItems]);
  const total = items.length;
  const bodyWidth = cfg.pa.width + 72;
  const stageWidth = bodyWidth + OFFSET_X * 2;
  const geo = { bodyW: bodyWidth, stageW: stageWidth, slotY: 118 };

  const containerRef = useRef<HTMLDivElement>(null);
  const [containerDim, setContainerDim] = useState({ w: 0, h: 0 });
  const [isMuted, setIsMuted] = useState(false);
  const [inView, setInView] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [reduced, setReduced] = useState(isReducedMotion);
  const [isHovered, setIsHovered] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [cycle, setCycle] = useState(0);
  const [droppingTickets, setDroppingTickets] = useState<
    Array<{ idx: number; id: number; tilt: number; drift: number }>
  >([]);
  const [isPrinting, setIsPrinting] = useState(false);
  const [hasPrintedInitial, setHasPrintedInitial] = useState(() => !(cfg.ru.printOnView && !isReducedMotion()));
  const [isFirstRender, setIsFirstRender] = useState(true);

  const isPrintingRef = useRef(false);
  const currentIndexRef = useRef(0);
  currentIndexRef.current = currentIndex;
  const cycleRef = useRef(0);
  cycleRef.current = cycle;
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const fn = () => setReduced(mq.matches);
    fn();
    mq.addEventListener("change", fn);
    return () => mq.removeEventListener("change", fn);
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const fn = () => setIsVisible(document.visibilityState !== "hidden");
    fn();
    document.addEventListener("visibilitychange", fn);
    return () => document.removeEventListener("visibilitychange", fn);
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || typeof IntersectionObserver === "undefined") {
      setInView(true);
      return;
    }
    const io = new IntersectionObserver(([e]) => setInView(Boolean(e && e.isIntersecting)), { threshold: 0.2 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const measure = () => {
      const rect = el.getBoundingClientRect();
      setContainerDim({ w: rect.width, h: rect.height });
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const finishPrinting = useCallback(() => {
    printerAudio.stopPrintSound();
    isPrintingRef.current = false;
    setIsPrinting(false);
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Initial print on view
  useEffect(() => {
    if (hasPrintedInitial || !inView || !isVisible || !total) return;
    isPrintingRef.current = true;
    setHasPrintedInitial(true);
    setIsFirstRender(false);
    setIsPrinting(true);
    printerAudio.startPrintSound(cfg.ru.feed);
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(finishPrinting, (cfg.ru.feed + 1.5) * 1000);
  }, [hasPrintedInitial, inView, isVisible, total, cfg.ru.feed, finishPrinting]);

  // Advance ticket
  const changeTicket = useCallback(
    (delta: number) => {
      if (isPrintingRef.current || total < 2 || !hasPrintedInitial) return;
      isPrintingRef.current = true;
      printerAudio.playTearSound();
      const tilt = (Math.random() > 0.5 ? 1 : -1) * (5 + Math.random() * 9);
      const drift = (Math.random() - 0.5) * 60;
      setDroppingTickets((prev) => [
        ...prev.slice(-2),
        { idx: currentIndexRef.current, id: cycleRef.current, tilt, drift },
      ]);
      setCurrentIndex((idx) => mod(idx + delta, total));
      setCycle((c) => c + 1);
      setIsFirstRender(false);
      setIsPrinting(true);
      printerAudio.startPrintSound(cfg.ru.feed);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(finishPrinting, (cfg.ru.feed + 2) * 1000);
    },
    [total, hasPrintedInitial, cfg.ru.feed, finishPrinting]
  );

  // Autoplay
  useEffect(() => {
    if (
      !cfg.ru.autoplay ||
      reduced ||
      !inView ||
      !isVisible ||
      !hasPrintedInitial ||
      isPrinting ||
      total <= 1 ||
      (cfg.ru.pauseOnHover && isHovered)
    )
      return;
    const t = setTimeout(() => changeTicket(1), Math.max(1500, cfg.ru.delay * 1000));
    return () => clearTimeout(t);
  }, [cfg.ru.autoplay, cfg.ru.delay, cfg.ru.pauseOnHover, reduced, inView, isVisible, hasPrintedInitial, isPrinting, total, isHovered, currentIndex, changeTicket]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      e.preventDefault();
      changeTicket(1);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault();
      changeTicket(-1);
    }
  };

  if (!total) {
    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: props.background,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 14,
          opacity: 0.6,
          ...props.style,
        }}
      >
        Add a testimonial to start
      </div>
    );
  }

  const currentItem = items[clamp(currentIndex, 0, total - 1)];
  const isMobile = containerDim.w > 0 && containerDim.w < 560;
  const scale = containerDim.w > 0 ? clamp((containerDim.w - (isMobile ? 12 : 32)) / geo.stageW, 0.45, 1) : 1;
  const stageH = containerDim.h > 0 ? containerDim.h / scale : 850;
  const feedDuration = reduced ? 0 : Math.max(0.4, cfg.ru.feed);
  const steppedFeed = getSteppedFeed(cfg.ru.stepped);
  const jitterRepeats = Math.max(1, Math.round(feedDuration / 0.16));

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      role="region"
      aria-roledescription="carousel"
      aria-label="Testimonials"
      onKeyDown={handleKeyDown}
      onPointerEnter={() => setIsHovered(true)}
      onPointerLeave={() => setIsHovered(false)}
      style={{
        width: "100%",
        height: "100%",
        background: props.background || "transparent",
        overflow: "hidden",
        position: "relative",
        outline: "none",
        ...props.style,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: 0,
          width: geo.stageW,
          height: stageH,
          marginLeft: -geo.stageW / 2,
          transform: `scale(${scale})`,
          transformOrigin: "50% 0%",
        }}
      >
        {/* Printer chassis with motor vibration */}
        <motion.div
          animate={isPrinting && !reduced ? { x: [0, -0.8, 0.9, -0.6, 0.5, 0] } : { x: 0 }}
          transition={isPrinting && !reduced ? { duration: 0.16, repeat: jitterRepeats, ease: "linear" } : { duration: 0.1 }}
          style={{ position: "absolute", inset: 0, zIndex: 3, pointerEvents: "none" }}
        >
          <div style={{ pointerEvents: "auto" }}>
            <PrinterChassis
              cfg={cfg}
              geo={geo}
              led={
                <motion.span
                  animate={isPrinting && !reduced ? { opacity: [1, 0.25, 1] } : { opacity: 1 }}
                  transition={
                    isPrinting && !reduced
                      ? { duration: 0.5, repeat: Math.ceil(feedDuration / 0.5) }
                      : { duration: 0.2 }
                  }
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: isPrinting ? "#FFB23F" : cfg.pr.led,
                    boxShadow: `0 0 8px ${isPrinting ? "#FFB23F" : cfg.pr.led}`,
                    display: "block",
                  }}
                />
              }
              screen={
                isPrinting ? (
                  <span>PRINTING…</span>
                ) : hasPrintedInitial ? (
                  <span>
                    READY {pad(currentIndex + 1, 2)}/{pad(total, 2)}
                  </span>
                ) : (
                  <span>STANDBY</span>
                )
              }
              keys={
                <>
                  <PrinterSoundButton
                    cfg={cfg}
                    isMuted={isMuted}
                    onToggle={() => {
                      const m = printerAudio.toggleMute();
                      setIsMuted(m);
                    }}
                  />
                  {total > 1 && (
                    <>
                      <PrinterKeyButton back cfg={cfg} onPress={() => changeTicket(-1)} />
                      <PrinterKeyButton cfg={cfg} onPress={() => changeTicket(1)} />
                    </>
                  )}
                </>
              }
            />
          </div>
        </motion.div>

        {/* Paper feeder slot */}
        <div
          style={{
            position: "absolute",
            left: 20,
            top: geo.slotY,
            width: cfg.pa.width + 120,
            bottom: 0,
            overflow: "hidden",
            zIndex: 2,
          }}
        >
          {/* Active printing ticket */}
          {hasPrintedInitial && (
            <motion.div
              key={`print-${cycle}`}
              initial={isFirstRender || reduced ? false : { y: "-101%" }}
              animate={{ y: isFirstRender || reduced ? "0%" : steppedFeed.y }}
              transition={
                isFirstRender || reduced
                  ? { duration: 0 }
                  : { duration: feedDuration, times: steppedFeed.times, ease: "easeOut", delay: cycle > 0 ? 0.3 : 0.15 }
              }
              onAnimationComplete={finishPrinting}
              onClick={() => cfg.ru.tapToTear && changeTicket(1)}
              style={{
                position: "absolute",
                left: 60,
                top: 0,
                width: cfg.pa.width,
                cursor: cfg.ru.tapToTear && total > 1 ? "pointer" : "default",
                zIndex: 1,
              }}
            >
              <ReceiptCard
                item={currentItem}
                index={currentIndex}
                count={total}
                cfg={cfg}
                labelFont={props.labelFont}
                quoteFont={props.quoteFont}
                nameFont={props.nameFont}
              />
            </motion.div>
          )}

          {/* Dropping/torn previous tickets */}
          {droppingTickets.map((t) => {
            const it = items[t.idx];
            if (!it) return null;
            return (
              <motion.div
                key={`drop-${t.id}`}
                initial={{ y: 0, x: 0, rotate: 0, opacity: 1 }}
                animate={
                  reduced
                    ? { opacity: 0 }
                    : {
                        y: [0, 10, stageH],
                        x: [0, 0, t.drift],
                        rotate: [0, t.tilt * 0.15, t.tilt],
                        opacity: [1, 1, 0.9],
                      }
                }
                transition={
                  reduced
                    ? { duration: 0 }
                    : {
                        duration: 0.95,
                        times: [0, 0.18, 1],
                        ease: [0.5, 0, 0.9, 0.5],
                      }
                }
                onAnimationComplete={() =>
                  setDroppingTickets((prev) => prev.filter((item) => item.id !== t.id))
                }
                style={{
                  position: "absolute",
                  left: 60,
                  top: 0,
                  width: cfg.pa.width,
                  zIndex: 2,
                  transformOrigin: "50% 0%",
                  pointerEvents: "none",
                }}
              >
                <ReceiptCard
                  item={it}
                  index={t.idx}
                  count={total}
                  cfg={cfg}
                  labelFont={props.labelFont}
                  quoteFont={props.quoteFont}
                  nameFont={props.nameFont}
                />
              </motion.div>
            );
          })}

          {/* Shadow beneath slot */}
          <div
            aria-hidden="true"
            style={{
              position: "absolute",
              left: 60,
              width: cfg.pa.width,
              top: 0,
              height: 16,
              background: "linear-gradient(180deg, rgba(0,0,0,0.22), rgba(0,0,0,0))",
              zIndex: 3,
              pointerEvents: "none",
            }}
          />
        </div>
      </div>
      <span
        aria-live="polite"
        style={{
          position: "absolute",
          width: 1,
          height: 1,
          overflow: "hidden",
          clip: "rect(0 0 0 0)",
          whiteSpace: "nowrap",
        }}
      >
        {currentItem.quote} {currentItem.name}
      </span>
    </div>
  );
};

export default TestimonialEmber;
