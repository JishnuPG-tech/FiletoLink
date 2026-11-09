/**
 * FlashFile — Telegram Media Stream & Acceleration Platform
 * Pure movie file-to-link and direct 4K streaming (Zero Torrent, Pure HTTP 206)
 * - Pure Black background (#000000)
 * - Claude Orange accent (#D97757)
 * - Generously curved components
 * - Authentic official app logos with uniform 44x44 icon frames
 * - Zero green dots, zero generic emojis, zero AI slop
 * - Bot username: @flashfilezbot
 */
import React, { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { getTelegramBotLink } from "../../content/site-config";
import Copier from "../Copier";
import { TestimonialEmber } from "../TestimonialEmber";

/* ─────────────────────────── helpers ─────────────────────────── */

const reducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const clamp01 = (n: number) => (n < 0 ? 0 : n > 1 ? 1 : n);

function useReveal(root: React.RefObject<HTMLElement | null>) {
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    el.setAttribute("data-js", "");
    const items = Array.from(el.querySelectorAll<HTMLElement>("[data-reveal]"));
    if (typeof IntersectionObserver === "undefined" || reducedMotion()) {
      items.forEach((i) => i.setAttribute("data-in", ""));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries)
          if (e.isIntersecting) {
            e.target.setAttribute("data-in", "");
            io.unobserve(e.target);
          }
      },
      { rootMargin: "0px 0px -8% 0px" },
    );
    items.forEach((i) => io.observe(i));
    return () => io.disconnect();
  }, [root]);
}

function useScrollFrame(ref: React.RefObject<HTMLElement | null>, fn: () => void) {
  const fnRef = useRef(fn);
  fnRef.current = fn;
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let raf = 0;
    let active = true;
    const run = () => {
      raf = 0;
      if (active) fnRef.current();
    };
    const queue = () => {
      if (!raf) raf = requestAnimationFrame(run);
    };
    const io =
      typeof IntersectionObserver !== "undefined"
        ? new IntersectionObserver(
            ([e]) => {
              active = e.isIntersecting;
              if (active) queue();
            },
            { rootMargin: "200px 0px" },
          )
        : undefined;
    io?.observe(el);
    queue();
    window.addEventListener("scroll", queue, { passive: true });
    window.addEventListener("resize", queue);
    return () => {
      io?.disconnect();
      window.removeEventListener("scroll", queue);
      window.removeEventListener("resize", queue);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [ref]);
}

function useInView(ref: React.RefObject<HTMLElement | null>, threshold = 0.35) {
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined" || reducedMotion()) {
      setSeen(true);
      return;
    }
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setSeen(true);
          io.disconnect();
        }
      },
      { threshold },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [ref, threshold]);
  return seen;
}

/* ─────────────────────────── icons & exact brand logos ─────────────────────────── */

function Arrow() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" className="fd-frg-arrow">
      <path d="M3 8h9.5M8.5 3.5L13 8l-4.5 4.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function Tick() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
      <path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function FilmIcon() {
  return (
    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
      <rect x="2" y="2" width="12" height="12" rx="3" fill="none" stroke="currentColor" strokeWidth="1.2" />
      <path d="M6 2v12M10 2v12M2 6h4M10 6h4M2 10h4M10 10h4" fill="none" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

/* Exact official logos with pristine geometry */
const APP_LOGOS: Record<string, ReactNode> = {
  vlc: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <defs>
        <linearGradient id="vlcBaseGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#E65100" />
          <stop offset="100%" stopColor="#BF360C" />
        </linearGradient>
        <linearGradient id="vlcConeGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#FFA726" />
          <stop offset="50%" stopColor="#FF9100" />
          <stop offset="100%" stopColor="#FF6D00" />
        </linearGradient>
      </defs>
      {/* Base square/trapezoid pedestal */}
      <path d="M4 25.5 C4 24.5 28 24.5 28 25.5 L26 28 C25.5 28.5 6.5 28.5 6 28 Z" fill="url(#vlcBaseGrad)" />
      <ellipse cx="16" cy="25.5" rx="12" ry="1.5" fill="#BF360C" />

      {/* Cone base section */}
      <path d="M8.5 25 C11 26 21 26 23.5 25 L21.8 20.5 C19.5 21.3 12.5 21.3 10.2 20.5 Z" fill="url(#vlcConeGrad)" />

      {/* Lower reflective band (white with soft shadow) */}
      <path d="M10.2 20.5 C12.5 21.3 19.5 21.3 21.8 20.5 L20.3 15.5 C18.3 16.2 13.7 16.2 11.7 15.5 Z" fill="#FFFFFF" />
      <path d="M11.7 15.5 C13.7 16.2 18.3 16.2 20.3 15.5 L20.1 14.8 C18.1 15.5 13.9 15.5 11.9 14.8 Z" fill="#E2E8F0" />

      {/* Middle orange section */}
      <path d="M11.9 14.8 C13.9 15.5 18.1 15.5 20.1 14.8 L19 10 C17.5 10.6 14.5 10.6 13 10 Z" fill="url(#vlcConeGrad)" />

      {/* Upper reflective band (white) */}
      <path d="M13 10 C14.5 10.6 17.5 10.6 19 10 L18 6 C17 6.4 15 6.4 14 6 Z" fill="#FFFFFF" />
      <path d="M14 6 C15 6.4 17 6.4 18 6 L17.8 5.4 C16.9 5.8 15.1 5.8 14.2 5.4 Z" fill="#E2E8F0" />

      {/* Tip section */}
      <path d="M14.2 5.4 C15.1 5.8 16.9 5.8 17.8 5.4 L17.2 3.6 C16.8 3.1 15.2 3.1 14.8 3.6 Z" fill="url(#vlcConeGrad)" />
      <ellipse cx="16" cy="3.5" rx="1.6" ry="0.8" fill="#FFA726" />
    </svg>
  ),
  mxplayer: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <defs>
        <linearGradient id="mxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0084FF" />
          <stop offset="100%" stopColor="#0052D4" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="28" height="28" rx="8" fill="url(#mxGrad)" />
      <polygon points="12,9 23,16 12,23" fill="#FFFFFF" />
    </svg>
  ),
  onedm: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <defs>
        <linearGradient id="onedmGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4A00E0" />
          <stop offset="100%" stopColor="#8E2DE2" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="28" height="28" rx="8" fill="url(#onedmGrad)" />
      <path
        d="M16 7 L16 19 M11.5 14.5 L16 19 L20.5 14.5"
        fill="none"
        stroke="#FFFFFF"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <line x1="9" y1="23" x2="23" y2="23" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  ),
  chrome: (
    <svg viewBox="0 0 512 512" width="28" height="28" aria-hidden="true">
      <defs>
        <linearGradient id="chromeRed" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#d93025" />
          <stop offset="100%" stopColor="#ea4335" />
        </linearGradient>
        <linearGradient id="chromeYellow" x1="0.5" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#fcc934" />
          <stop offset="100%" stopColor="#fbbc04" />
        </linearGradient>
        <linearGradient id="chromeGreen" x1="1" y1="0" x2="0.2" y2="1">
          <stop offset="0%" stopColor="#1e8e3e" />
          <stop offset="100%" stopColor="#34a853" />
        </linearGradient>
      </defs>
      <circle cx="256" cy="256" r="128" fill="#FFFFFF" />
      <path
        d="M256 128h221.6C407 5.6 250.5-36.3 128.1 34.3 89.2 56.8 56.8 89.1 34.4 128l110.8 192h.1c-35.4-61.1-14.6-139.3 46.5-174.7 19.4-11.4 41.6-17.3 64.2-17.3"
        fill="url(#chromeRed)"
      />
      <path
        d="M366.8 320 256 512c141.3 0 255.9-114.5 255.9-255.9 0-45-11.8-89.1-34.3-128H256v.1c70.6-.1 127.9 57 128.1 127.6 0 22.5-6 44.7-17.3 64.2"
        fill="url(#chromeYellow)"
      />
      <path
        d="M145.2 320 34.4 128.1C-36.3 250.5 5.6 407 128 477.7c38.9 22.4 83.1 34.3 128 34.3l110.8-192-.1-.1c-35.2 61.2-113.3 82.3-174.5 47.1-19.5-11.2-35.8-27.4-47-47"
        fill="url(#chromeGreen)"
      />
      <circle cx="256" cy="256" r="102" fill="#FFFFFF" />
      <circle cx="256" cy="256" r="82" fill="#1a73e8" />
    </svg>
  ),
  safari: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <circle cx="16" cy="16" r="14" fill="#0071E3" />
      <circle cx="16" cy="16" r="11" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1" strokeDasharray="1.5 2.5" />
      <polygon points="16,5 18.5,16 16,16" fill="#FF3B30" />
      <polygon points="16,5 13.5,16 16,16" fill="#FF453A" />
      <polygon points="16,27 18.5,16 16,16" fill="#E5E5EA" />
      <polygon points="16,27 13.5,16 16,16" fill="#FFFFFF" />
      <circle cx="16" cy="16" r="1.6" fill="#FFFFFF" />
    </svg>
  ),
  android: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <path d="M7 16 A9 9 0 0 1 25 16 Z" fill="#3DDC84" />
      <line x1="10.5" y1="8" x2="8" y2="4.5" stroke="#3DDC84" strokeWidth="2" strokeLinecap="round" />
      <line x1="21.5" y1="8" x2="24" y2="4.5" stroke="#3DDC84" strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="12" r="1.3" fill="#000000" />
      <circle cx="20" cy="12" r="1.3" fill="#000000" />
      <rect x="7" y="18" width="18" height="7" rx="2" fill="#3DDC84" />
    </svg>
  ),
  tv: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <rect x="3" y="5" width="26" height="17" rx="3.5" fill="#18181B" stroke="#3F3F46" strokeWidth="1.5" />
      <polygon points="14,10 20,13.5 14,17" fill="#D97757" />
      <path d="M12 26 L16 22 L20 26 M16 22 L16 26" stroke="#71717A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  windows: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <path d="M3 4 L14.5 4 L14.5 14.5 L3 14.5 Z" fill="#0078D4" />
      <path d="M17.5 4 L29 4 L29 14.5 L17.5 14.5 Z" fill="#0078D4" />
      <path d="M3 17.5 L14.5 17.5 L14.5 28 L3 28 Z" fill="#0078D4" />
      <path d="M17.5 17.5 L29 17.5 L29 28 L17.5 28 Z" fill="#0078D4" />
    </svg>
  ),
  apple: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <path
        d="M19.8 4.2 C20.9 2.8 21.6 1 21.4 0 C19.9 0.1 18 1.1 16.9 2.4 C16 3.4 15.2 5.2 15.5 6.2 C17.1 6.3 18.9 5.3 19.8 4.2 Z M23.5 17.2 C23.5 13.5 26.5 11.6 26.7 11.5 C25 9 22.3 8.7 21.4 8.6 C19.2 8.4 17 9.9 15.9 9.9 C14.7 9.9 12.9 8.6 11.1 8.6 C8.8 8.6 6.7 9.9 5.5 12 C3.1 16.2 4.9 22.3 7.2 25.7 C8.4 27.3 9.7 29.1 11.5 29 C13.3 28.9 14 27.8 16.1 27.8 C18.3 27.8 18.9 29 20.7 29 C22.6 28.9 23.8 27.3 24.9 25.7 C26.2 23.8 26.7 22 26.8 21.9 C26.7 21.8 23.5 20.6 23.5 17.2 Z"
        fill="#FFFFFF"
      />
    </svg>
  ),
  linux: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <ellipse cx="16" cy="18" rx="8" ry="10" fill="#27272A" />
      <ellipse cx="16" cy="19" rx="5.5" ry="7.5" fill="#FAFAFA" />
      <circle cx="16" cy="10" r="5" fill="#27272A" />
      <circle cx="14.5" cy="9.2" r="1.1" fill="#FFFFFF" />
      <circle cx="14.5" cy="9.2" r="0.5" fill="#000000" />
      <circle cx="17.5" cy="9.2" r="1.1" fill="#FFFFFF" />
      <circle cx="17.5" cy="9.2" r="0.5" fill="#000000" />
      <polygon points="14.5,11 17.5,11 16,13.2" fill="#F59E0B" />
      <ellipse cx="11.5" cy="27" rx="3.5" ry="1.5" fill="#F59E0B" />
      <ellipse cx="20.5" cy="27" rx="3.5" ry="1.5" fill="#F59E0B" />
    </svg>
  ),
  telegram: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <circle cx="16" cy="16" r="14" fill="#2AABEE" />
      <path
        d="M8.5 15.5 L22.5 10 L19 22.5 L14.5 19.5 L12 21.5 L12.5 17.5 L20 12 L10.5 16.5 Z"
        fill="#FFFFFF"
      />
    </svg>
  ),
  infuse: (
    <svg viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
      <defs>
        <linearGradient id="infuseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FF6B4A" />
          <stop offset="100%" stopColor="#D92638" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="28" height="28" rx="8" fill="url(#infuseGrad)" />
      <path
        d="M13 8.5 C13 8.5 19 12 21 16 C22.5 19 21.5 22 19 23.5 C16.5 25 13 24 11.5 21.5 C10 19 11 16.5 12.5 14.5 C13.5 13.2 13 11 13 8.5 Z"
        fill="#FFFFFF"
      />
    </svg>
  ),
};

/* ─────────────────────────── nav (No FlashFile logo, pure typography) ─────────────────────────── */

const NAV = [
  ["#how", "How It Works"],
  ["#preview", "Instant Preview"],
  ["#speed", "Speed Test"],
  ["#players", "Supported Players"],
  ["#faq", "FAQ"],
];

function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 12);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  return (
    <header className="fd-frg-nav" data-scrolled={scrolled || undefined} data-open={open || undefined}>
      <div className="fd-frg-nav-in">
        <a href="#top" className="fd-frg-brand" aria-label="FlashFile home">
          <span className="fd-frg-brand-text">FlashFile</span>
        </a>
        <nav className="fd-frg-nav-links" aria-label="Primary">
          {NAV.map(([h, l]) => (
            <a key={h} href={h}>
              {l}
            </a>
          ))}
        </nav>
        <div className="fd-frg-nav-right">
          <a
            className="fd-frg-btn fd-frg-btn-sm"
            href={getTelegramBotLink("nav_cta")}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open Telegram Bot
          </a>
          <button
            type="button"
            className="fd-frg-burger"
            aria-expanded={open}
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((o) => !o)}
          >
            <span />
            <span />
          </button>
        </div>
      </div>
      <div className="fd-frg-sheet" hidden={!open}>
        {NAV.map(([h, l]) => (
          <a key={h} href={h} onClick={() => setOpen(false)}>
            {l}
          </a>
        ))}
      </div>
    </header>
  );
}

/* ─────────────────────────── hero terminal (No Green Dots) ─────────────────────────── */

type TLine = { kind: "cmd" | "out" | "ok" | "warn" | "dim" | "sum"; text: string; pause?: number };

const SCRIPT: TLine[] = [
  { kind: "cmd", text: "forward movie: Dune.Part.Two.2024.4K.HDR.mkv (6.4 GB)" },
  { kind: "dim", text: "→ media indexed from Telegram cloud · zero upload wait", pause: 380 },
  { kind: "out", text: "  status: direct cloud video stream ready", pause: 400 },
  { kind: "ok", text: "  ✓ direct stream   · ready in 0.24 seconds", pause: 260 },
  { kind: "ok", text: "  ✓ audio check     · Dolby 5.1, Hindi Dub, Subtitles", pause: 260 },
  { kind: "ok", text: "  ✓ video quality   · 4K Ultra HD — 18.4 Mbps", pause: 260 },
  { kind: "warn", text: "  ◆ streaming link  · https://stream.flashfile.pro/dune2-hdr", pause: 460 },
  { kind: "ok", text: "  ✓ ready to play   · open in VLC, MX Player or Chrome", pause: 360 },
  { kind: "sum", text: "streaming at 124 MB/s · zero phone storage used · no torrents", pause: 0 },
];

function Terminal() {
  const [shown, setShown] = useState<{ line: number; chars: number }>({ line: 0, chars: 0 });
  const [run, setRun] = useState(0);
  const boxRef = useRef<HTMLDivElement>(null);
  const done = shown.line >= SCRIPT.length;

  useEffect(() => {
    if (reducedMotion()) {
      setShown({ line: SCRIPT.length, chars: 0 });
      return;
    }
    let line = 0;
    let chars = 0;
    let t = 0;
    let cancelled = false;
    setShown({ line: 0, chars: 0 });
    const tick = () => {
      if (cancelled) return;
      const cur = SCRIPT[line];
      if (!cur) return;
      if (cur.kind === "cmd" && chars < cur.text.length) {
        chars += 1;
        setShown({ line, chars });
        t = window.setTimeout(tick, 25 + Math.random() * 40);
        return;
      }
      line += 1;
      chars = 0;
      setShown({ line, chars: 0 });
      t = window.setTimeout(tick, cur.pause ?? 300);
    };
    t = window.setTimeout(tick, 600);
    return () => {
      cancelled = true;
      window.clearTimeout(t);
    };
  }, [run]);

  return (
    <div className="fd-frg-term" ref={boxRef}>
      <div className="fd-frg-term-bar">
        <span className="fd-frg-term-dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        <span className="fd-frg-term-title">Telegram Movie Streaming Engine</span>
        <button type="button" className="fd-frg-term-replay" onClick={() => setRun((r) => r + 1)} disabled={!done}>
          Replay
        </button>
      </div>
      <div className="fd-frg-term-body" aria-hidden="true">
        {SCRIPT.map((l, i) => {
          if (i > shown.line) return null;
          const typing = l.kind === "cmd" && i === shown.line;
          const text = typing ? l.text.slice(0, shown.chars) : l.text;
          if (i === shown.line && !typing) return null;
          return (
            <div key={`${run}-${i}`} className={`fd-frg-tl fd-frg-tl-${l.kind}`}>
              {l.kind === "cmd" && <span className="fd-frg-prompt">›</span>}
              <span>{text}</span>
              {typing && <span className="fd-frg-caret" />}
            </div>
          );
        })}
        {done && (
          <div className="fd-frg-tl fd-frg-tl-cmd">
            <span className="fd-frg-prompt">›</span>
            <span className="fd-frg-caret" />
          </div>
        )}
      </div>
      <p className="fd-frg-sr" aria-live="polite">
        {done ? "Demonstration: 6.4 GB Telegram video converted to direct streaming link in 0.24 seconds." : ""}
      </p>
    </div>
  );
}

function Hero() {
  return (
    <section className="fd-frg-hero" id="top">
      <div className="fd-frg-wrap fd-frg-hero-in">
        <a className="fd-frg-pill fd-frg-in" href="#speed" style={{ "--d": "0ms" } as CSSProperties}>
          <span className="fd-frg-pill-new">DIRECT STREAM</span>{" "}
          <span className="fd-frg-pill-txt">Watch movies instantly without saving to phone</span> <Arrow />
        </a>
        <h1 className="fd-frg-h1">
          <span className="fd-frg-in" style={{ "--d": "80ms" } as CSSProperties}>
            Watch any Telegram movie.
          </span>
          <span className="fd-frg-in fd-frg-h1-mute" style={{ "--d": "180ms" } as CSSProperties}>
            Skip the download.
          </span>
        </h1>
        <p className="fd-frg-lede fd-frg-in" style={{ "--d": "280ms" } as CSSProperties}>
          Downloading files inside Telegram is slow, stops when your phone locks, and fills up your phone storage.
          FlashFile turns any Telegram movie into a clean, direct HTTP link that streams 4K video instantly in VLC or MX Player,
          with zero torrents and zero waiting.
        </p>
        <div className="fd-frg-ctas fd-frg-in" style={{ "--d": "360ms" } as CSSProperties}>
          <a
            className="fd-frg-btn"
            href={getTelegramBotLink("hero_primary")}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open Telegram Bot <Arrow />
          </a>
          <a className="fd-frg-btn fd-frg-btn-ghost" href="#how">
            How It Works
          </a>
        </div>
        <div className="fd-frg-hero-term fd-frg-in" style={{ "--d": "460ms" } as CSSProperties}>
          <Terminal />
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────── supported apps bar ─────────────────────────── */

function Logos() {
  const APPS = [
    { name: "VLC Player", href: "#players" },
    { name: "MX Player", href: "#players" },
    { name: "Google Chrome", href: "#players" },
    { name: "1DM Mobile", href: "#players" },
    { name: "Apple iOS", href: "#players" },
    { name: "Android", href: "#players" },
    { name: "Smart TVs", href: "#players" },
    { name: "Windows PC", href: "#players" },
    { name: "Mac & Linux", href: "#players" },
    { name: "Infuse Player", href: "#players" },
  ];

  // Duplicate for seamless infinite horizontal ticker
  const tickerItems = [...APPS, ...APPS];

  return (
    <section className="fd-frg-logos" aria-label="Supported Apps">
      <div className="fd-frg-wrap">
        <p className="fd-frg-mini" data-reveal="">
          Streams and downloads seamlessly with the apps already on your device
        </p>
        <div className="fd-frg-marquee-shell" data-reveal="">
          <div className="fd-frg-marquee-track">
            {tickerItems.map((item, idx) => (
              <a
                key={`${item.name}-${idx}`}
                href={item.href}
                className="fd-frg-marquee-item"
                title={`Jump to ${item.name} details in Supported Players`}
              >
                <span>{item.name}</span>
                <svg
                  className="fd-frg-marquee-arrow"
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M7 17L17 7" />
                  <path d="M7 7h10v10" />
                </svg>
              </a>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────── flow timeline ─────────────────────────── */

function DynamicCloudMeter() {
  const [filled, setFilled] = useState(28);

  useEffect(() => {
    let count = 8;
    const interval = setInterval(() => {
      count = count >= 28 ? 12 : count + 2;
      setFilled(count);
    }, 220);
    return () => clearInterval(interval);
  }, []);

  return (
    <span className="fd-frg-meter" aria-label="100% cloud indexed">
      <span className="fd-frg-meter-grid" aria-hidden="true">
        {Array.from({ length: 28 }, (_, i) => (
          <i key={i} data-on={i < filled ? "true" : undefined} />
        ))}
      </span>
      <b>100% cloud indexed</b>
    </span>
  );
}

const STEPS = [
  {
    t: "00:00",
    time: "Send",
    title: "Send or forward any movie to the bot",
    body: "Forward any movie, series episode, FLAC audio track, or zip archive up to 4 GB to @flashfilezbot on Telegram.",
    meta: <span className="fd-frg-chip">Zero upload wait · Instant</span>,
  },
  {
    t: "00:01",
    time: "Index",
    title: "Instant cloud handshake",
    body: "The bot locates the file directly on Telegram's official cloud servers. No re-uploading needed.",
    meta: <DynamicCloudMeter />,
  },
  {
    t: "00:02",
    time: "Stream",
    title: "Direct high-speed HTTP streaming link",
    body: "Generates a clean HTTP link straight from Telegram cloud servers. 100% direct streaming with zero torrents and zero waiting.",
    meta: <span className="fd-frg-chip">Direct HTTP Stream · Zero Wait</span>,
  },
  {
    t: "00:03",
    time: "Resume",
    title: "Clean direct link generated",
    body: "You get a direct web link with 100% resume support. If your Wi-Fi disconnects, it picks right back up.",
    meta: <span className="fd-frg-chip fd-frg-chip-acc">HTTP 206 · 100% resumable</span>,
  },
  {
    t: "00:04",
    time: "Play",
    title: "Tap play to watch immediately",
    body: "Open in VLC or MX Player. Check language dubbing, print clarity, and subtitles before downloading.",
    meta: <span className="fd-frg-chip">VLC & MX Player 1-tap play</span>,
  },
  {
    t: "00:05",
    time: "Fast DL",
    title: "Download at full internet speed",
    body: "Paste your link into VLC, MX Player, 1DM, or Chrome to stream or download at your connection's top speed.",
    meta: <span className="fd-frg-chip">VLC · MX Player · 1DM Ready</span>,
  },
];

function Timeline() {
  const ref = useRef<HTMLElement>(null);
  const list = useRef<HTMLOListElement>(null);
  useScrollFrame(ref, () => {
    const l = list.current;
    if (!l) return;
    const r = l.getBoundingClientRect();
    const vh = window.innerHeight;
    const startY = vh * 0.72;
    const scrollTravel = r.height * 0.88;
    const p = reducedMotion() ? 1 : clamp01((startY - r.top) / scrollTravel);
    l.style.setProperty("--draw", p.toFixed(4));
    const lineY = p * r.height;
    l.querySelectorAll<HTMLElement>("[data-step]").forEach((li) => {
      if (li.offsetTop + 14 <= lineY + 12) li.setAttribute("data-on", "");
      else li.removeAttribute("data-on");
    });
  });
  return (
    <section className="fd-frg-sec" id="how" ref={ref}>
      <div className="fd-frg-wrap fd-frg-tl-grid">
        <div className="fd-frg-sticky-head" data-reveal="">
          <p className="fd-frg-eyebrow">01 — Simple 5-Second Flow</p>
          <h2 className="fd-frg-h2">
            From Telegram to player,
            <br />
            <span className="fd-frg-h2-mute">in under five seconds.</span>
          </h2>
          <p className="fd-frg-p">
            No registration, no software to install, no passwords. Forward your movie to @flashfilezbot and start watching or downloading right away.
          </p>
        </div>
        <ol className="fd-frg-steps" ref={list}>
          <span className="fd-frg-rail" aria-hidden="true">
            <i />
          </span>
          {STEPS.map((s) => (
            <li key={s.t} data-step="">
              <span className="fd-frg-node" aria-hidden="true" />
              <div className="fd-frg-step-head">
                <span className="fd-frg-mono fd-frg-step-t">{s.t}</span>
                <span className="fd-frg-mono fd-frg-step-k">{s.time}</span>
              </div>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
              <div className="fd-frg-step-meta">{s.meta}</div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

/* ─────────────────────────── Media Quality Preview ─────────────────────────── */

const INSPECTION_LINES = [
  { o: "FILE", n: "NAME", k: " ", code: "Dune.Part.Two.2024.2160p.UHD.HDR.DDP5.1.mkv (6.42 GB)" },
  { o: "STAT", n: "SPEED", k: "+", code: "✓ Direct 4K HTTP streaming link generated in 0.24s" },
  { o: "AUD1", n: "ENG", k: "+", code: "✓ English Dolby Atmos 5.1 Surround Sound verified" },
  { o: "AUD2", n: "DUB", k: "+", code: "✓ Hindi / Tamil / Malayalam dual audio tracks active" },
  { o: "SUBS", n: "SYNC", k: "+", code: "✓ English SDH + Full Subtitles embedded and synced" },
  { o: "VIDO", n: "PRINT", k: "+", code: "✓ True 4K UHD 2160p HDR (not low-quality cam rip)" },
  { o: "RAM", n: "DISK", k: " ", code: "→ Storage: Stream directly to RAM — 0 MB phone storage used" },
];

function Diff() {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useInView(ref, 0.3);
  const [stage, setStage] = useState(0);
  const [applied, setApplied] = useState(false);

  useEffect(() => {
    if (!seen) return;
    if (reducedMotion()) {
      setStage(4);
      return;
    }
    const ts = [300, 1200, 2200, 3100].map((ms, i) => window.setTimeout(() => setStage(i + 1), ms));
    return () => ts.forEach((t) => window.clearTimeout(t));
  }, [seen]);

  return (
    <section className="fd-frg-sec fd-frg-sec-alt" id="preview">
      <div className="fd-frg-wrap">
        <div className="fd-frg-head-row" data-reveal="">
          <div>
            <p className="fd-frg-eyebrow">02 — Instant Quality Verification</p>
            <h2 className="fd-frg-h2">
              Check movie print & audio,
              <br />
              <span className="fd-frg-h2-mute">before downloading 3 GB.</span>
            </h2>
          </div>
          <p className="fd-frg-p fd-frg-head-p">
            Never waste mobile data on a movie with terrible audio dubbing or low-res cam print. Stream the first few seconds to verify quality first.
          </p>
        </div>

        <div className="fd-frg-diff" ref={ref} data-stage={stage} data-reveal="">
          <div className="fd-frg-diff-bar">
            <span className="fd-frg-mono">media-stream-analyzer — 4K HDR</span>
            <span className="fd-frg-diff-stat">
              <b className="fd-frg-add">18.4 Mbps</b>
            </span>
            <span className="fd-frg-diff-status" data-on={stage >= 1 || undefined}>
              <span className="fd-frg-spin" aria-hidden="true" />
              {stage >= 4 ? "Stream Ready — 0.0s Buffer Delay" : stage >= 1 ? "Checking audio & video streams…" : "Ready"}
            </span>
          </div>
          <div className="fd-frg-diff-body">
            <div className="fd-frg-code" role="table" aria-label="Media Stream Inspection">
              {INSPECTION_LINES.map((l, i) => (
                <div key={i} role="row" className={`fd-frg-dl fd-frg-dl-${l.k === "+" ? "add" : "ctx"}`} data-scan={stage >= 1 || undefined} style={{ "--i": i } as CSSProperties}>
                  <span role="cell" className="fd-frg-ln">{l.o}</span>
                  <span role="cell" className="fd-frg-ln">{l.n}</span>
                  <span role="cell" className="fd-frg-sign">{l.k}</span>
                  <span role="cell" className="fd-frg-src">{l.code}</span>
                </div>
              ))}
            </div>
            <div className="fd-frg-comments">
              <article className="fd-frg-cmt" data-show={stage >= 2 || undefined}>
                <header>
                  <b>Audio Stream Inspection</b>
                  <span className="fd-frg-mono">Track 1 & 2</span>
                </header>
                <p>
                  High-fidelity multi-audio stream detected. You can switch between Original English and Dubbed audio right inside VLC or MX Player.
                </p>
              </article>
              <article className="fd-frg-cmt" data-show={stage >= 3 || undefined}>
                <header>
                  <b>Video Quality Inspection</b>
                  <span className="fd-frg-mono">4K UHD Master</span>
                </header>
                <p>
                  Genuine 2160p 4K UHD master print verified. Crisp colors, zero compression artifacts, full HDR support.
                </p>
                <button
                  type="button"
                  className="fd-frg-btn fd-frg-btn-sm fd-frg-btn-ghost"
                  onClick={() => setApplied(true)}
                  disabled={applied}
                >
                  {applied ? (
                    <>
                      <Tick /> Ready to Play in VLC
                    </>
                  ) : (
                    "Test Play Stream"
                  )}
                </button>
              </article>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────── speed comparison (Pixel-Perfect Alignment & Fit) ─────────────────────────── */

const JOBS = [
  { num: "01", name: "Telegram File Handshake", start: 0, dur: 1 },
  { num: "02", name: "Direct Cloud Stream Ready", start: 1, dur: 1 },
  { num: "03", name: "HTTP 206 Chunk Stream", start: 2, dur: 1 },
  { num: "04", name: "Instant VLC / MX Playback", start: 3, dur: 1 },
  { num: "05", name: "Full Speed Saturation", start: 4, dur: 1 },
];
const TOTAL = 5;

function Speed() {
  const ref = useRef<HTMLElement>(null);
  const clock = useRef<HTMLSpanElement>(null);
  const legacy = useRef<HTMLSpanElement>(null);
  useScrollFrame(ref, () => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const vh = window.innerHeight;
    const travel = Math.max(1, r.height - vh);
    const p = reducedMotion() ? 1 : clamp01((-r.top) / travel);
    const t = p * TOTAL;
    el.style.setProperty("--p", p.toFixed(4));
    el.querySelectorAll<HTMLElement>("[data-job]").forEach((row) => {
      const s = Number(row.dataset.start);
      const d = Number(row.dataset.dur);
      const f = clamp01((t - s) / d);
      row.style.setProperty("--f", f.toFixed(4));
      row.dataset.state = f >= 1 ? "done" : f > 0 ? "run" : "wait";
    });
    if (clock.current) {
      const sec = Math.round(t);
      clock.current.textContent = `0:0${sec}`;
    }
    if (legacy.current) {
      const lt = Math.round(p * 2520);
      legacy.current.textContent = `${Math.floor(lt / 60)}:${String(lt % 60).padStart(2, "0")}`;
    }
  });

  return (
    <section className="fd-frg-speed" id="speed" ref={ref}>
      <div className="fd-frg-speed-stick">
        <div className="fd-frg-wrap fd-frg-speed-in">
          <div className="fd-frg-speed-head">
            <div>
              <p className="fd-frg-eyebrow">03 — The 5-Second Stream</p>
              <h2 className="fd-frg-h2">
                Same 4 GB movie. <span className="fd-frg-h2-mute">Watching in 5 seconds.</span>
              </h2>
            </div>
            <p className="fd-frg-mono fd-frg-speed-hint" aria-hidden="true">Scroll to watch speed test ↓</p>
          </div>
          <div className="fd-frg-clock-row">
            <div className="fd-frg-clock">
              <span className="fd-frg-mono">Direct Stream (Ready to Watch)</span>
              <span ref={clock} className="fd-frg-clock-n">
                0:00
              </span>
            </div>
            <div className="fd-frg-clock fd-frg-clock-legacy">
              <span className="fd-frg-mono">Inside Telegram (Must Wait for 100% Download)</span>
              <span ref={legacy} className="fd-frg-clock-n">
                0:00
              </span>
            </div>
          </div>
          <div className="fd-frg-gantt" role="img" aria-label="Comparison: FlashFile plays in 5 seconds vs 42 minutes waiting for Telegram app download">
            <div className="fd-frg-gantt-axis" aria-hidden="true">
              {[0, 1, 2, 3, 4, 5].map((s) => (
                <span key={s} style={{ left: `${(s / TOTAL) * 100}%` }}>
                  {s}s
                </span>
              ))}
            </div>
            {JOBS.map((j) => (
              <div key={j.name} className="fd-frg-job" data-job="" data-start={j.start} data-dur={j.dur} data-state="wait">
                <span className="fd-frg-job-name">
                  <span className="fd-frg-step-idx">{j.num}</span>
                  <span>{j.name}</span>
                </span>
                <span className="fd-frg-job-track">
                  <span
                    className="fd-frg-job-bar"
                    style={{ left: `${(j.start / TOTAL) * 100}%`, width: `${(j.dur / TOTAL) * 100}%` }}
                  >
                    <i />
                  </span>
                </span>
                <span className="fd-frg-job-dur fd-frg-mono">{j.dur}s</span>
              </div>
            ))}
            <span className="fd-frg-playhead" aria-hidden="true" />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────── bento (Pure Direct Streaming) ─────────────────────────── */

const STREAMING_MOVIES = [
  { title: "Dune Part Two (4K UHD)", player: "Playing in VLC", badge: "streaming", info: "124 MB/s · 4K HDR", buffer: "0.0s buffer" },
  { title: "Interstellar FLAC Lossless", player: "Hi-Res Audio", badge: "streaming", info: "24-bit / 96 kHz", buffer: "Direct RAM" },
  { title: "Complete Season 1 MKV", player: "Instant Play", badge: "streaming", info: "1080p 60FPS", buffer: "Multi-Audio" },
];

function DynamicMovieStack() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActive((prev) => (prev + 1) % 3);
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="fd-frg-tile-vis fd-frg-vis-stack" aria-hidden="true">
      {STREAMING_MOVIES.map((m, i) => {
        const isCurrent = i === active;
        return (
          <div
            key={m.title}
            className={`fd-frg-stack-card ${isCurrent ? "fd-frg-stack-active" : ""}`}
            style={{ "--i": i } as CSSProperties}
          >
            <div className="fd-frg-stack-top">
              <FilmIcon />
              <span className="fd-frg-stack-title">{m.title}</span>
              <em className="fd-frg-stack-badge" data-active={isCurrent || undefined}>
                {isCurrent ? "streaming" : "ready"}
              </em>
            </div>
            {isCurrent && (
              <div className="fd-frg-stack-live">
                <span className="fd-frg-mono">{m.info}</span>
                <span className="fd-frg-stack-bar">
                  <i />
                </span>
                <span className="fd-frg-mono">{m.buffer}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function DynamicResumeVisualizer() {
  const [chunkCount, setChunkCount] = useState(26);

  useEffect(() => {
    let c = 24;
    const timer = setInterval(() => {
      c = c >= 48 ? 14 : c + 2;
      setChunkCount(c);
    }, 400);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="fd-frg-tile-vis fd-frg-vis-flake-box" aria-hidden="true">
      <div className="fd-frg-flake-header">
        <span className="fd-frg-mono">HTTP 206 RESUME · CHUNK {chunkCount}/48</span>
        <span className="fd-frg-flake-pct">{Math.round((chunkCount / 48) * 100)}%</span>
      </div>
      <div className="fd-frg-vis-flake">
        {Array.from({ length: 48 }, (_, i) => {
          const isDone = i < chunkCount;
          const isCurrent = i === chunkCount || i === chunkCount + 1;
          return (
            <i
              key={i}
              data-f={isDone ? "done" : isCurrent ? "active" : undefined}
            />
          );
        })}
      </div>
    </div>
  );
}

function Bento() {
  return (
    <section className="fd-frg-sec" aria-label="Features">
      <div className="fd-frg-wrap">
        <div className="fd-frg-head-row" data-reveal="">
          <div>
            <p className="fd-frg-eyebrow">04 — Key Benefits</p>
            <h2 className="fd-frg-h2">
              Less waiting.
              <br />
              <span className="fd-frg-h2-mute">More streaming.</span>
            </h2>
          </div>
        </div>
        <div className="fd-frg-bento">
          <article className="fd-frg-tile fd-frg-tile-wide" data-reveal="">
            <DynamicMovieStack />
            <h3>Stream movies directly without saving</h3>
            <p>Watch full-length 4K movies with zero waiting. Tap play to stream in VLC or MX Player, leaving your phone memory completely free.</p>
          </article>

          <article className="fd-frg-tile" data-reveal="" style={{ "--i": 1 } as CSSProperties}>
            <DynamicResumeVisualizer />
            <h3>Never restarts from zero</h3>
            <p>If your Wi-Fi disconnects or battery dies, your download resumes right where it stopped. No corrupted files, no wasted data.</p>
          </article>

          <article className="fd-frg-tile" data-reveal="" style={{ "--i": 2 } as CSSProperties}>
            <div className="fd-frg-tile-vis fd-frg-vis-cache" aria-hidden="true">
              <span>0 MB</span>
              <small>phone storage used</small>
            </div>
            <h3>Zero phone storage waste</h3>
            <p>Stop Telegram from secretly saving gigabytes of hidden video cache files onto your internal storage.</p>
          </article>

          <article className="fd-frg-tile fd-frg-tile-wide" data-reveal="" style={{ "--i": 3 } as CSSProperties}>
            <div className="fd-frg-tile-vis fd-frg-vis-chart" aria-hidden="true">
              <svg aria-hidden="true" focusable="false" viewBox="0 0 400 110" preserveAspectRatio="none">
                <path d="M0 90 L40 85 L80 80 L120 70 L160 50 L200 30 L240 18 L280 12 L320 8 L360 6 L400 5" fill="none" stroke="var(--fd-frg-accent)" strokeWidth="2" />
                <path d="M0 90 L40 85 L80 80 L120 70 L160 50 L200 30 L240 18 L280 12 L320 8 L360 6 L400 5 L400 110 L0 110Z" fill="var(--fd-frg-accent)" opacity="0.08" />
                <path d="M160 0V110" stroke="rgba(255,255,255,0.2)" strokeDasharray="3 4" />
              </svg>
              <span className="fd-frg-chart-tag">Instant Direct Streaming Active</span>
            </div>
            <h3>Pure direct streaming, zero torrents</h3>
            <p>No torrent files, no seeders, no leechers, and no upload sharing. You stream your own movie directly from Telegram's official high-speed cloud.</p>
          </article>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────── supported players (Uncompressed, Consistent Icons) ─────────────────────────── */

const APPS: { id: string; name: string; desc: string }[] = [
  { id: "vlc", name: "VLC Player", desc: "1-Tap instant 4K streaming & audio track selection" },
  { id: "mxplayer", name: "MX Player", desc: "Smooth mobile hardware acceleration & gestures" },
  { id: "onedm", name: "1DM (Android)", desc: "Best mobile downloader with multi-thread chunking" },
  { id: "chrome", name: "Google Chrome", desc: "Stream video directly in your web browser tab" },
  { id: "safari", name: "Apple Safari & iOS", desc: "Direct Safari streaming and VLC iOS playback" },
  { id: "android", name: "Android Devices", desc: "Universal playback with all Android video players" },
  { id: "tv", name: "Smart TVs & FireStick", desc: "Stream Telegram movies on Android TV & FireStick" },
  { id: "windows", name: "Windows PC", desc: "Full compatibility with Windows media players" },
  { id: "apple", name: "macOS", desc: "Clean HTTP links for QuickTime, IINA, and VLC" },
  { id: "linux", name: "Linux", desc: "Direct media streaming with MPV, VLC, and curl" },
  { id: "telegram", name: "Telegram Cloud", desc: "Direct connection to official Telegram media servers" },
  { id: "infuse", name: "Infuse Player", desc: "High-end 4K HDR playback for Apple TV, Mac & iPhone" },
];

function Integrations() {
  const grid = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const g = grid.current;
    if (!g) return;
    let raf = 0;
    let ex = 0;
    let ey = 0;
    const apply = () => {
      raf = 0;
      const gr = g.getBoundingClientRect();
      g.style.setProperty("--mx", `${ex - gr.left}px`);
      g.style.setProperty("--my", `${ey - gr.top}px`);
      g.querySelectorAll<HTMLElement>("[data-cell]").forEach((c) => {
        const r = c.getBoundingClientRect();
        c.style.setProperty("--mx", `${ex - r.left}px`);
        c.style.setProperty("--my", `${ey - r.top}px`);
      });
    };
    const move = (e: PointerEvent) => {
      ex = e.clientX;
      ey = e.clientY;
      g.setAttribute("data-hot", "");
      if (!raf) raf = requestAnimationFrame(apply);
    };
    const leave = () => g.removeAttribute("data-hot");
    g.addEventListener("pointermove", move);
    g.addEventListener("pointerleave", leave);
    return () => {
      g.removeEventListener("pointermove", move);
      g.removeEventListener("pointerleave", leave);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <section className="fd-frg-sec fd-frg-sec-alt" id="players">
      <div className="fd-frg-wrap">
        <div className="fd-frg-head-row" data-reveal="">
          <div>
            <p className="fd-frg-eyebrow">05 — Universal Compatibility</p>
            <h2 className="fd-frg-h2">
              Works with the apps
              <br />
              <span className="fd-frg-h2-mute">you already have.</span>
            </h2>
          </div>
          <p className="fd-frg-p fd-frg-head-p">
            FlashFile outputs standard, universally compatible HTTP web links. Play in your favorite player or download with any app on any device.
          </p>
        </div>
        <div className="fd-frg-int" ref={grid} data-reveal="">
          {APPS.map((app) => (
            <div key={app.id} className="fd-frg-int-cell" data-cell="">
              <div className="fd-frg-logo-box">
                {APP_LOGOS[app.id]}
              </div>
              <b>{app.name}</b>
              <span>{app.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────── stats + quote ─────────────────────────── */

function Proof() {
  return (
    <section className="fd-frg-sec" aria-label="Recent Conversions" id="conversions">
      <div className="fd-frg-wrap">
        <dl className="fd-frg-stats">
          {[
            ["124 MB/s", "Peak direct streaming throughput"],
            ["0 MB", "Phone storage wasted on temporary caches"],
            ["100%", "Byte-accurate download resumption guarantee"],
            ["4.0 GB", "Max Telegram movie & file size supported"],
          ].map(([k, v], i) => (
            <div key={k} data-reveal="" style={{ "--i": i } as CSSProperties}>
              <dt>{k}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>

        <div className="fd-frg-printer-container" data-reveal="" style={{ marginTop: "64px" }}>
          <div className="fd-frg-head-row" style={{ marginBottom: "36px", textAlign: "center" }}>
            <div style={{ margin: "0 auto", maxWidth: "680px" }}>
              <p className="fd-frg-eyebrow">05 — Recent Stream Conversions</p>
              <h2 className="fd-frg-h2" style={{ textAlign: "center" }}>
                Recent movies and series,
                <br />
                <span className="fd-frg-h2-mute">streamed live with @flashfilezbot.</span>
              </h2>
              <p className="fd-frg-p" style={{ margin: "14px auto 0", textAlign: "center", maxWidth: "560px" }}>
                Every time a user converts a movie or series to an instant streaming link, the engine prints a verified playback ticket.
              </p>
            </div>
          </div>
          <div className="fd-frg-printer-stage">
            <TestimonialEmber
              background="transparent"
              style={{ width: "100%", height: "100%" }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────── FAQ ─────────────────────────── */

const FAQS = [
  {
    q: "Is FlashFile free to use?",
    a: "Yes! FlashFile is 100% free. Forward any movie, video, or song to @flashfilezbot and instantly receive direct download and streaming links.",
  },
  {
    q: "How do I play movies in VLC or MX Player?",
    a: "When the bot replies with your link, simply tap 'Open in VLC' or 'Open in MX Player'. Your video starts playing immediately without waiting for the whole file to download.",
  },
  {
    q: "Does this use torrents or P2P sharing?",
    a: "No! There are zero torrents, zero seeds, and zero uploads. Everything streams cleanly over direct HTTP 206 directly from Telegram's secure media cloud.",
  },
  {
    q: "What if my Wi-Fi drops or phone screen turns off?",
    a: "Your download is never lost. FlashFile direct links support 100% resume. Download managers continue from the exact byte where it paused.",
  },
  {
    q: "Is my Telegram account safe?",
    a: "Completely safe. FlashFile never asks for your phone number, password, or login. You just forward a file to the bot exactly like messaging a friend.",
  },
];

function Faq() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section className="fd-frg-sec" id="faq">
      <div className="fd-frg-wrap">
        <div className="fd-frg-head-row" data-reveal="">
          <div>
            <p className="fd-frg-eyebrow">06 — Answers to Common Questions</p>
            <h2 className="fd-frg-h2">
              Everything you need
              <br />
              <span className="fd-frg-h2-mute">to know about FlashFile.</span>
            </h2>
          </div>
        </div>

        <div className="fd-frg-faq-list" data-reveal="">
          {FAQS.map((f, i) => {
            const isOpen = open === i;
            return (
              <div key={i} className="fd-frg-faq-item" data-open={isOpen || undefined}>
                <button
                  type="button"
                  className="fd-frg-faq-btn"
                  onClick={() => setOpen(isOpen ? null : i)}
                  aria-expanded={isOpen}
                >
                  <span>{f.q}</span>
                  <span className="fd-frg-faq-icon">{isOpen ? "−" : "+"}</span>
                </button>
                {isOpen && <p className="fd-frg-faq-a">{f.a}</p>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────── CTA + footer ─────────────────────────── */

function Cta() {
  const [copied, setCopied] = useState(false);

  return (
    <section className="fd-frg-cta">
      <div className="fd-frg-wrap">
        <div className="fd-frg-cta-grid" data-reveal="">
          <div className="fd-frg-cta-left">
            <p className="fd-frg-eyebrow">07 — Instant Access</p>
            <h2 className="fd-frg-cta-h">Stop waiting for slow Telegram downloads.</h2>
            <p className="fd-frg-p">
              Forward any movie or file to @flashfilezbot right now. It takes five seconds, uses zero phone storage, and requires zero setup.
            </p>
            <div className="fd-frg-cta-hint">
              {copied ? (
                <span className="fd-frg-copied-badge">
                  <Tick /> Copied @flashfilezbot to clipboard!
                </span>
              ) : (
                <span>
                  Tip: Drag the slip onto the photocopier or tap it to print & copy.
                </span>
              )}
            </div>
            <div className="fd-frg-ctas">
              <a
                className="fd-frg-btn"
                href={getTelegramBotLink("final_cta")}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open Telegram Bot <Arrow />
              </a>
              <a className="fd-frg-btn fd-frg-btn-ghost" href="#players">
                View Supported Players
              </a>
            </div>
          </div>
          <div className="fd-frg-cta-right">
            <div className="fd-frg-copier-frame">
              <Copier
                theme="dark"
                content={{
                  label: "TELEGRAM BOT",
                  value: "@flashfilezbot",
                  mark: "FLASHFILE·01",
                }}
                dark={{
                  body: "rgb(28, 28, 30)",
                  tray: "rgb(24, 24, 26)",
                  accent: "rgb(217, 119, 87)",
                  paper: "rgb(244, 242, 236)",
                  ink: "rgb(35, 35, 39)",
                  shadow: "rgb(0, 0, 0)",
                  strength: 100,
                }}
                behavior={{
                  sound: true,
                  haptics: true,
                  keepCopies: true,
                  canvasState: "rest",
                }}
                onCopy={() => {
                  setCopied(true);
                  setTimeout(() => setCopied(false), 3500);
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="fd-frg-foot">
      <div className="fd-frg-wrap">
        <div className="fd-frg-foot-top">
          <div>
            <a href="#top" className="fd-frg-brand" aria-label="FlashFile home">
              <span className="fd-frg-brand-text">FlashFile</span>
            </a>
            <p className="fd-frg-foot-p">High-speed Telegram media streaming and resumable download engine.</p>
            <span className="fd-frg-status">
              All streaming servers operational
            </span>
          </div>
        </div>
        <div className="fd-frg-foot-bot">
          <span>&copy; {new Date().getFullYear()} FlashFile Engine. Free & Open Source.</span>
          <span className="fd-frg-mono">Direct HTTP 206 Streaming Infrastructure · @flashfilezbot</span>
        </div>
      </div>
    </footer>
  );
}

/* ─────────────────────────── page ─────────────────────────── */

export function Page() {
  const root = useRef<HTMLDivElement>(null);
  useReveal(root);
  return (
    <div className="fd-frg" ref={root}>
      <style>{css}</style>
      <Nav />
      <main>
        <Hero />
        <Logos />
        <Timeline />
        <Diff />
        <Speed />
        <Bento />
        <Integrations />
        <Proof />
        <Faq />
        <Cta />
      </main>
      <Footer />
    </div>
  );
}

export const FlashFilePage = Page;
export default Page;

/* ─────────────────────────── styles ─────────────────────────── */

const css = `
.fd-frg {
  --fd-ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --fd-ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --fd-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --fd-dur-1: 120ms;
  --fd-dur-2: 240ms;
  --fd-dur-3: 420ms;
  --fd-dur-4: 700ms;

  --fd-frg-bg: #000000;
  --fd-frg-bg-2: #080808;
  --fd-frg-surface: #101010;
  --fd-frg-surface-2: #161616;
  --fd-frg-fg: #F4EDE2;
  --fd-frg-mute: #A1A1AA;
  --fd-frg-dim: #71717A;
  --fd-frg-line: rgba(255, 255, 255, 0.08);
  --fd-frg-line-2: rgba(255, 255, 255, 0.14);
  --fd-frg-accent: #D97757;
  --fd-frg-accent-soft: rgba(217, 119, 87, 0.14);
  --fd-frg-add: #D97757;
  --fd-frg-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --fd-frg-mono-f: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace;

  position: relative; display: block; margin: 0; padding: 0;
  background: var(--fd-frg-bg); color: var(--fd-frg-fg);
  font: 400 1rem/1.5 var(--fd-frg-sans); letter-spacing: -0.006em; text-align: left;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
  overflow-x: clip; color-scheme: dark;
}
.fd-frg, .fd-frg *, .fd-frg *::before, .fd-frg *::after { box-sizing: border-box; }
.fd-frg :where(h1, h2, h3, h4, p, ul, ol, li, dl, dt, dd, figure, figcaption, blockquote, main, header, footer, section, nav, article, label) {
  margin: 0; padding: 0; border: 0; font: inherit; color: inherit; letter-spacing: inherit; background: none;
}
.fd-frg :where(ul, ol) { list-style: none; }
.fd-frg :where(a) { color: inherit; text-decoration: none; }
.fd-frg :where(button) { appearance: none; -webkit-appearance: none; margin: 0; padding: 0; border: 0; background: none; font: inherit; color: inherit; letter-spacing: inherit; cursor: pointer; text-align: inherit; line-height: inherit; }
.fd-frg :where(button:disabled) { cursor: default; }
.fd-frg :where(svg) { display: block; overflow: visible; }
.fd-frg :where(code) { font: 400 0.92em/1.5 var(--fd-frg-mono-f); background: none; padding: 0; color: inherit; }
.fd-frg :where(b, strong) { font-weight: 600; }
.fd-frg :where(em) { font-style: normal; }
.fd-frg :where(small) { font-size: inherit; }
.fd-frg :where(a, button, input, [tabindex]):focus-visible { outline: 2px solid rgba(217, 119, 87, 0.7); outline-offset: 2px; border-radius: 9999px; }
.fd-frg-sr { position: absolute !important; width: 1px; height: 1px; margin: -1px; padding: 0; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }

.fd-frg-wrap { width: 100%; max-width: 1200px; margin: 0 auto; padding: 0 32px; }
.fd-frg-mono { font: 400 0.75rem/1.4 var(--fd-frg-mono-f); letter-spacing: 0; }
.fd-frg-mini { font: 400 0.8125rem/1.4 var(--fd-frg-sans); color: var(--fd-frg-mute); text-align: center; }
.fd-frg-eyebrow { font: 600 0.8125rem/1.4 var(--fd-frg-mono-f); color: var(--fd-frg-accent); letter-spacing: 0.04em; text-transform: uppercase; }
.fd-frg-h2 { margin-top: 14px; font: 600 clamp(2rem, 4.2vw, 3.25rem)/1.1 var(--fd-frg-sans); letter-spacing: -0.04em; }
.fd-frg-h2-mute { color: var(--fd-frg-dim); }
.fd-frg-p { margin-top: 18px; max-width: 34em; font: 400 1.0625rem/1.55 var(--fd-frg-sans); color: var(--fd-frg-mute); }
.fd-frg-head-row { display: flex; justify-content: space-between; align-items: flex-end; gap: 32px; flex-wrap: wrap; }
.fd-frg-head-p { max-width: 26em; margin: 0; }

/* Buttons & Pills (All Curved Edges) */
.fd-frg-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 46px; padding: 0 24px;
  border: 1px solid var(--fd-frg-accent); border-radius: 9999px; background: var(--fd-frg-accent); color: #fff;
  font: 500 0.9375rem/1 var(--fd-frg-sans); letter-spacing: -0.01em; white-space: nowrap;
  transition: transform var(--fd-dur-1) var(--fd-ease-out), background-color var(--fd-dur-2) var(--fd-ease-out);
  box-shadow: 0 4px 16px rgba(217, 119, 87, 0.25);
}
.fd-frg-btn:hover { background: #e58a69; transform: translateY(-1px); }
.fd-frg-btn:active { transform: scale(0.97); }
.fd-frg-btn .fd-frg-arrow { transition: transform var(--fd-dur-2) var(--fd-spring); }
.fd-frg-btn:hover .fd-frg-arrow { transform: translateX(3px); }
.fd-frg-btn-sm { height: 36px; padding: 0 18px; font-size: 0.8125rem; }
.fd-frg-btn-ghost { background: transparent; color: var(--fd-frg-fg); border-color: var(--fd-frg-line-2); box-shadow: none; }
.fd-frg-btn-ghost:hover { background: var(--fd-frg-surface-2); border-color: rgba(255,255,255,0.3); }
.fd-frg-btn-ghost:disabled { color: var(--fd-frg-mute); }

.fd-frg-chip { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 12px; border: 1px solid var(--fd-frg-line-2); border-radius: 9999px; font: 400 0.75rem/1 var(--fd-frg-mono-f); color: var(--fd-frg-mute); white-space: nowrap; }
.fd-frg-chip-acc { color: var(--fd-frg-accent); border-color: rgba(217,119,87,0.35); background: var(--fd-frg-accent-soft); }

/* nav */
.fd-frg-nav { position: sticky; top: 0; z-index: 50; display: block; border-bottom: 1px solid transparent; transition: background-color var(--fd-dur-3) var(--fd-ease-out), border-color var(--fd-dur-3) var(--fd-ease-out); }
.fd-frg-nav[data-scrolled], .fd-frg-nav[data-open] { background: rgba(0,0,0,0.88); border-bottom-color: var(--fd-frg-line); -webkit-backdrop-filter: saturate(160%) blur(14px); backdrop-filter: saturate(160%) blur(14px); }
.fd-frg-nav-in { display: flex; align-items: center; gap: 28px; max-width: 1200px; height: 68px; margin: 0 auto; padding: 0 32px; transition: height var(--fd-dur-3) var(--fd-ease-out); }
.fd-frg-nav[data-scrolled] .fd-frg-nav-in { height: 56px; }
.fd-frg-brand { display: inline-flex; align-items: center; text-decoration: none; }
.fd-frg-brand-text { font: 700 1.25rem/1 var(--fd-frg-sans); letter-spacing: -0.03em; color: var(--fd-frg-fg); }
.fd-frg-nav-links { display: flex; gap: 6px; }
.fd-frg-nav-links a { display: inline-flex; align-items: center; height: 34px; padding: 0 14px; border-radius: 9999px; font: 400 0.875rem/1 var(--fd-frg-sans); color: var(--fd-frg-mute); transition: color var(--fd-dur-1) linear, background-color var(--fd-dur-1) linear; }
.fd-frg-nav-links a:hover { color: var(--fd-frg-fg); background: var(--fd-frg-surface-2); }
.fd-frg-nav-right { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.fd-frg-burger { display: none; position: relative; width: 40px; height: 40px; border-radius: 9999px; }
.fd-frg-burger span { position: absolute; left: 11px; right: 11px; height: 1.5px; background: var(--fd-frg-fg); transition: transform var(--fd-dur-3) var(--fd-spring); }
.fd-frg-burger span:first-child { top: 16px; }
.fd-frg-burger span:last-child { top: 23px; }
.fd-frg-nav[data-open] .fd-frg-burger span:first-child { transform: translateY(3.5px) rotate(45deg); }
.fd-frg-nav[data-open] .fd-frg-burger span:last-child { transform: translateY(-3.5px) rotate(-45deg); }
.fd-frg-sheet { display: grid; padding: 8px 24px 20px; border-radius: 0 0 24px 24px; background: #000; }
.fd-frg-sheet[hidden] { display: none; }
.fd-frg-sheet a { padding: 14px 0; border-bottom: 1px solid var(--fd-frg-line); font: 500 1.125rem/1.2 var(--fd-frg-sans); }

/* hero */
.fd-frg-hero { position: relative; padding: 96px 0 120px; margin-top: -68px; padding-top: 160px; overflow: hidden; isolation: isolate; }
.fd-frg-hero-in { display: flex; flex-direction: column; align-items: center; text-align: center; }
.fd-frg-pill { display: inline-flex; align-items: center; gap: 10px; height: 34px; padding: 0 14px 0 6px; border: 1px solid var(--fd-frg-line-2); border-radius: 9999px; background: rgba(16,16,16,0.9); font: 400 0.8125rem/1 var(--fd-frg-sans); color: var(--fd-frg-mute); transition: border-color var(--fd-dur-2) var(--fd-ease-out), color var(--fd-dur-2); }
.fd-frg-pill:hover { border-color: rgba(255,255,255,0.3); color: var(--fd-frg-fg); }
.fd-frg-pill-new { display: inline-flex; align-items: center; height: 24px; padding: 0 10px; border-radius: 9999px; background: var(--fd-frg-accent-soft); color: var(--fd-frg-accent); font: 600 0.75rem/1 var(--fd-frg-mono-f); }
.fd-frg-h1 { display: flex; flex-direction: column; margin-top: 28px; font: 600 clamp(3rem, 7.5vw, 6.25rem)/0.98 var(--fd-frg-sans); letter-spacing: -0.055em; }
.fd-frg-h1-mute { color: var(--fd-frg-dim); }
.fd-frg-in { animation: fd-frg-in 1000ms var(--fd-ease-out) both; animation-delay: var(--d, 0ms); }
@keyframes fd-frg-in { from { opacity: 0; transform: translateY(16px); filter: blur(6px); } to { opacity: 1; transform: none; filter: none; } }
.fd-frg-lede { max-width: 36em; margin-top: 26px; font: 400 clamp(1.0625rem, 1.5vw, 1.25rem)/1.55 var(--fd-frg-sans); color: var(--fd-frg-mute); }
.fd-frg-ctas { display: flex; flex-wrap: wrap; justify-content: center; gap: 14px; margin-top: 34px; }
.fd-frg-hero-term { width: 100%; max-width: 820px; margin-top: 64px; text-align: left; }

/* terminal (Curved Edges) */
.fd-frg-term { position: relative; border: 1px solid var(--fd-frg-line-2); border-radius: 24px; background: #0A0A0A; box-shadow: 0 20px 60px -20px rgba(0,0,0,0.9), 0 0 100px -40px rgba(217,119,87,0.18); overflow: hidden; }
.fd-frg-term-bar { display: flex; align-items: center; gap: 12px; height: 44px; padding: 0 16px; border-bottom: 1px solid var(--fd-frg-line); }
.fd-frg-term-dots { display: flex; gap: 6px; }
.fd-frg-term-dots i { width: 10px; height: 10px; border-radius: 50%; background: var(--fd-frg-surface-2); border: 1px solid var(--fd-frg-line-2); }
.fd-frg-term-title { flex: 1; font: 500 0.75rem/1 var(--fd-frg-mono-f); color: var(--fd-frg-dim); text-align: center; }
.fd-frg-term-replay { height: 26px; padding: 0 12px; border-radius: 9999px; border: 1px solid var(--fd-frg-line-2); font: 500 0.6875rem/1 var(--fd-frg-sans); color: var(--fd-frg-mute); transition: opacity var(--fd-dur-2); }
.fd-frg-term-replay:disabled { opacity: 0.35; }
.fd-frg-term-body { height: 320px; padding: 20px 24px; font: 400 0.8125rem/1.85 var(--fd-frg-mono-f); color: var(--fd-frg-fg); overflow: hidden; }
.fd-frg-tl { display: flex; gap: 10px; align-items: center; white-space: pre; animation: fd-frg-line 280ms var(--fd-ease-out) both; }
@keyframes fd-frg-line { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
.fd-frg-tl-cmd { animation: none; }
.fd-frg-tl-dim { color: var(--fd-frg-dim); }
.fd-frg-tl-out { color: var(--fd-frg-mute); }
.fd-frg-tl-ok { color: var(--fd-frg-fg); }
.fd-frg-tl-warn { color: var(--fd-frg-accent); }
.fd-frg-tl-sum { margin-top: 6px; color: var(--fd-frg-accent); font-weight: 500; }
.fd-frg-prompt { color: var(--fd-frg-accent); font-weight: bold; }
.fd-frg-caret { display: inline-block; width: 8px; height: 1.1em; margin-left: -6px; background: var(--fd-frg-accent); animation: fd-frg-blink 1s steps(2, start) infinite; }
@keyframes fd-frg-blink { to { visibility: hidden; } }

/* logos marquee bar (infinite horizontal ticker with href links) */
.fd-frg-logos { padding: 0 0 96px; }
.fd-frg-marquee-shell {
  position: relative;
  margin-top: 28px;
  overflow: hidden;
  border-top: 1px solid var(--fd-frg-line);
  border-bottom: 1px solid var(--fd-frg-line);
  background: rgba(255, 255, 255, 0.015);
  mask-image: linear-gradient(to right, transparent, black 6%, black 94%, transparent);
  -webkit-mask-image: linear-gradient(to right, transparent, black 6%, black 94%, transparent);
}
.fd-frg-marquee-track {
  display: flex;
  width: max-content;
  animation: fd-frg-ticker 28s linear infinite;
  will-change: transform;
}
.fd-frg-marquee-shell:hover .fd-frg-marquee-track {
  animation-play-state: paused;
}
.fd-frg-marquee-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 76px;
  padding: 0 32px;
  min-width: 175px;
  color: var(--fd-frg-mute);
  border-right: 1px solid var(--fd-frg-line);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  white-space: nowrap;
  background: transparent;
  transition: color var(--fd-dur-2) var(--fd-ease-out), background var(--fd-dur-2) var(--fd-ease-out);
}
.fd-frg-marquee-item:hover {
  color: #fff;
  background: rgba(217, 119, 87, 0.08);
}
.fd-frg-marquee-arrow {
  opacity: 0.35;
  transition: transform var(--fd-dur-2) var(--fd-ease-out), opacity var(--fd-dur-2) var(--fd-ease-out), stroke var(--fd-dur-2) var(--fd-ease-out);
}
.fd-frg-marquee-item:hover .fd-frg-marquee-arrow {
  opacity: 1;
  stroke: var(--fd-frg-accent);
  transform: translate(2px, -2px);
}
@keyframes fd-frg-ticker {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) {
  .fd-frg-marquee-track {
    animation: none;
    overflow-x: auto;
  }
}

/* sections */
.fd-frg-sec { padding: 128px 0; border-top: 1px solid var(--fd-frg-line); background: #000; }
.fd-frg-sec-alt { background: #070707; }

/* timeline */
.fd-frg-tl-grid { display: grid; grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr); gap: 72px; align-items: start; }
.fd-frg-sticky-head { position: sticky; top: 120px; }
.fd-frg-steps { --draw: 0; position: relative; padding-left: 44px; }
.fd-frg-rail { position: absolute; left: 11px; top: 14px; bottom: 14px; width: 2px; background: var(--fd-frg-line-2); border-radius: 9999px; }
.fd-frg-rail i { position: absolute; inset: 0; background: linear-gradient(to bottom, var(--fd-frg-accent), #FF9E80); transform-origin: top; transform: scaleY(var(--draw)); box-shadow: 0 0 10px rgba(217,119,87,0.7); border-radius: 9999px; transition: transform 0.08s linear; }
.fd-frg-steps li { position: relative; padding: 0 0 56px; opacity: 0.4; transition: opacity var(--fd-dur-3) var(--fd-ease-out); }
.fd-frg-steps li:last-child { padding-bottom: 0; }
.fd-frg-steps li[data-on] { opacity: 1; }
.fd-frg-node { position: absolute; left: -38px; top: 8px; width: 11px; height: 11px; border-radius: 50%; background: var(--fd-frg-bg); border: 1px solid var(--fd-frg-line-2); transition: background-color var(--fd-dur-2) var(--fd-ease-out), border-color var(--fd-dur-2), box-shadow var(--fd-dur-3) var(--fd-ease-out), transform var(--fd-dur-3) var(--fd-spring); }
.fd-frg-steps li[data-on] .fd-frg-node { background: var(--fd-frg-accent); border-color: var(--fd-frg-accent); box-shadow: 0 0 0 5px var(--fd-frg-accent-soft); transform: scale(1.1); }
.fd-frg-step-head { display: flex; gap: 12px; align-items: center; }
.fd-frg-step-t { color: var(--fd-frg-accent); font-variant-numeric: tabular-nums; font-weight: 600; }
.fd-frg-step-k { color: var(--fd-frg-dim); text-transform: uppercase; letter-spacing: 0.06em; }
.fd-frg-steps h3 { margin-top: 8px; font: 600 1.375rem/1.25 var(--fd-frg-sans); letter-spacing: -0.025em; }
.fd-frg-steps p { margin-top: 8px; max-width: 32em; font: 400 0.9688rem/1.55 var(--fd-frg-sans); color: var(--fd-frg-mute); }
.fd-frg-step-meta { margin-top: 14px; }
.fd-frg-meter { display: inline-flex; align-items: center; gap: 12px; }
.fd-frg-meter-grid {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 18px;
  padding: 2px 6px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--fd-frg-line);
}
.fd-frg-meter-grid i {
  width: 3px;
  height: 11px;
  border-radius: 1px;
  background: #202020;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}
.fd-frg-meter-grid i[data-on] {
  background: var(--fd-frg-accent);
  box-shadow: 0 0 6px rgba(217, 119, 87, 0.7);
}
.fd-frg-meter b { font: 500 0.75rem/1 var(--fd-frg-mono-f); color: var(--fd-frg-fg); white-space: nowrap; }

/* diff preview (Curved Edges) */
.fd-frg-diff { margin-top: 56px; border: 1px solid var(--fd-frg-line-2); border-radius: 28px; background: var(--fd-frg-bg); overflow: hidden; box-shadow: 0 20px 60px -20px rgba(0,0,0,0.8); }
.fd-frg-diff-bar { display: flex; align-items: center; gap: 16px; height: 48px; padding: 0 20px; border-bottom: 1px solid var(--fd-frg-line); color: var(--fd-frg-fg); }
.fd-frg-diff-stat { font: 500 0.75rem/1 var(--fd-frg-mono-f); }
.fd-frg-diff-status { display: inline-flex; align-items: center; gap: 8px; margin-left: auto; font: 400 0.8125rem/1 var(--fd-frg-sans); color: var(--fd-frg-mute); }
.fd-frg-spin { width: 12px; height: 12px; border-radius: 50%; border: 1.5px solid var(--fd-frg-line-2); border-top-color: var(--fd-frg-accent); }
.fd-frg-diff-status[data-on] .fd-frg-spin { animation: fd-frg-spin 0.8s linear infinite; }
.fd-frg-diff[data-stage="4"] .fd-frg-spin { animation: none; border-color: var(--fd-frg-accent); background: var(--fd-frg-accent); }
@keyframes fd-frg-spin { to { transform: rotate(360deg); } }
.fd-frg-diff-body { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 0.75fr); }
.fd-frg-code { padding: 16px 0; font: 400 0.8125rem/1.9 var(--fd-frg-mono-f); overflow-x: auto; border-right: 1px solid var(--fd-frg-line); }
.fd-frg-dl { position: relative; display: grid; grid-template-columns: 48px 48px 24px max-content; min-width: 100%; white-space: pre; }
.fd-frg-dl::after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(217,119,87,0.18), transparent); opacity: 0; pointer-events: none; }
.fd-frg-dl[data-scan]::after { animation: fd-frg-scan 900ms var(--fd-ease-out) both; animation-delay: calc(var(--i) * 70ms); }
@keyframes fd-frg-scan { 0% { opacity: 0; transform: translateX(-30%); } 40% { opacity: 1; } 100% { opacity: 0; transform: translateX(30%); } }
.fd-frg-ln { padding-right: 12px; color: #5f5f63; text-align: right; user-select: none; font-variant-numeric: tabular-nums; }
.fd-frg-sign { color: var(--fd-frg-dim); user-select: none; }
.fd-frg-src { padding-right: 20px; color: #d6d6d6; }
.fd-frg-dl-add { background: rgba(217,119,87,0.08); }
.fd-frg-dl-add .fd-frg-sign, .fd-frg-dl-add .fd-frg-ln { color: var(--fd-frg-accent); }
.fd-frg-comments { display: flex; flex-direction: column; gap: 14px; padding: 20px; background: var(--fd-frg-bg-2); }
.fd-frg-cmt { padding: 18px; border: 1px solid var(--fd-frg-line-2); border-radius: 20px; background: var(--fd-frg-surface); opacity: 0; transform: translateY(10px) scale(0.96); transform-origin: top left; transition: opacity var(--fd-dur-3) var(--fd-ease-out), transform var(--fd-dur-3) var(--fd-spring); }
.fd-frg-cmt[data-show] { opacity: 1; transform: none; }
.fd-frg-cmt header { display: flex; align-items: center; gap: 8px; font: 600 0.8125rem/1 var(--fd-frg-sans); color: var(--fd-frg-fg); }
.fd-frg-cmt header .fd-frg-mono { margin-left: auto; color: var(--fd-frg-dim); font-size: 0.6875rem; }
.fd-frg-cmt p { margin-top: 10px; font: 400 0.875rem/1.55 var(--fd-frg-sans); color: #c9c9c9; }

/* speed (Pixel-Perfect Alignment & Fit) */
.fd-frg-speed { --p: 0; position: relative; height: 320vh; border-top: 1px solid var(--fd-frg-line); background: var(--fd-frg-bg); }
.fd-frg-speed-stick {
  position: sticky;
  top: 68px;
  height: calc(100vh - 68px);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 12px 0 24px;
}
.fd-frg-speed-in {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}
.fd-frg-speed-head { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 12px; }
.fd-frg-speed-head .fd-frg-h2 { margin-top: 8px; font-size: clamp(1.75rem, 3.2vw, 2.5rem); }
.fd-frg-speed-hint { color: var(--fd-frg-dim); }

.fd-frg-clock-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border: 1px solid var(--fd-frg-line-2);
  border-radius: 22px;
  overflow: hidden;
  background: #0A0A0A;
}
.fd-frg-clock { display: flex; flex-direction: column; gap: 6px; padding: 16px 24px; }
.fd-frg-clock .fd-frg-mono { color: var(--fd-frg-accent); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; font-size: 0.6875rem; }
.fd-frg-clock-n { font: 600 clamp(2.5rem, 5vw, 4.25rem)/0.95 var(--fd-frg-sans); letter-spacing: -0.05em; font-variant-numeric: tabular-nums; }
.fd-frg-clock-legacy { border-left: 1px solid var(--fd-frg-line); background: repeating-linear-gradient(135deg, transparent 0 8px, rgba(255,255,255,0.02) 8px 9px); }
.fd-frg-clock-legacy .fd-frg-mono { color: var(--fd-frg-dim); }
.fd-frg-clock-legacy .fd-frg-clock-n { color: #5f5f63; }

.fd-frg-gantt {
  position: relative;
  display: grid;
  gap: 8px;
  padding: 28px 0 4px;
}
.fd-frg-gantt-axis {
  position: absolute;
  left: 230px;
  right: 64px;
  top: 0;
  height: 20px;
}
.fd-frg-gantt-axis span {
  position: absolute;
  transform: translateX(-50%);
  font: 500 0.75rem/1 var(--fd-frg-mono-f);
  color: var(--fd-frg-dim);
}
.fd-frg-gantt-axis span:first-child { transform: translateX(0); }
.fd-frg-gantt-axis span:last-child { transform: translateX(-100%); }

.fd-frg-job {
  --f: 0;
  display: grid;
  grid-template-columns: 230px 1fr 64px;
  align-items: center;
  height: 32px;
}
.fd-frg-job-name {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-right: 16px;
  font: 400 0.875rem/1 var(--fd-frg-sans);
  color: var(--fd-frg-mute);
  transition: color var(--fd-dur-2);
}
.fd-frg-step-idx {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font: 600 0.6875rem/1 var(--fd-frg-mono-f);
  color: var(--fd-frg-dim);
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: var(--fd-frg-surface-2);
  transition: color var(--fd-dur-2), background-color var(--fd-dur-2);
}
.fd-frg-job[data-state="run"] .fd-frg-job-name { color: var(--fd-frg-fg); }
.fd-frg-job[data-state="run"] .fd-frg-step-idx { color: #fff; background: var(--fd-frg-accent); }
.fd-frg-job[data-state="done"] .fd-frg-job-name { color: var(--fd-frg-fg); }
.fd-frg-job[data-state="done"] .fd-frg-step-idx { color: #fff; background: var(--fd-frg-accent); }

.fd-frg-job-track {
  position: relative;
  height: 100%;
  border-left: 1px solid var(--fd-frg-line);
  border-right: 1px solid var(--fd-frg-line);
  background-image: linear-gradient(to right, var(--fd-frg-line) 1px, transparent 1px);
  background-size: 20% 100%;
}
.fd-frg-job-bar {
  position: absolute;
  top: 5px;
  bottom: 5px;
  border-radius: 9999px;
  background: var(--fd-frg-surface-2);
  border: 1px solid var(--fd-frg-line-2);
  overflow: hidden;
}
.fd-frg-job-bar i {
  position: absolute;
  inset: 0;
  border-radius: 9999px;
  background: linear-gradient(90deg, rgba(217,119,87,0.7), var(--fd-frg-accent));
  transform-origin: left;
  transform: scaleX(var(--f));
}
.fd-frg-job[data-state="done"] .fd-frg-job-bar i { background: var(--fd-frg-accent); }
.fd-frg-job-dur { text-align: right; color: var(--fd-frg-dim); padding-left: 12px; }
.fd-frg-playhead {
  position: absolute;
  top: 20px;
  bottom: 0;
  left: calc(230px + (100% - 230px - 64px) * var(--p));
  width: 1px;
  background: var(--fd-frg-accent);
  box-shadow: 0 0 10px var(--fd-frg-accent);
}

/* bento (All Curved Tiles) */
.fd-frg-bento { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 56px; }
.fd-frg-tile { display: flex; flex-direction: column; padding: 32px; background: #0A0A0A; border: 1px solid var(--fd-frg-line); border-radius: 28px; min-height: 360px; transition: border-color var(--fd-dur-2), transform var(--fd-dur-2); }
.fd-frg-tile:hover { border-color: rgba(217,119,87,0.3); transform: translateY(-2px); }
.fd-frg-tile-wide { grid-column: span 2; }
.fd-frg-tile h3 { margin-top: auto; padding-top: 24px; font: 600 1.25rem/1.3 var(--fd-frg-sans); letter-spacing: -0.02em; }
.fd-frg-tile p { margin-top: 8px; max-width: 34em; font: 400 0.9375rem/1.55 var(--fd-frg-sans); color: var(--fd-frg-mute); }
.fd-frg-tile-vis { flex: 1; min-height: 160px; }
.fd-frg-vis-stack { display: flex; flex-direction: column; justify-content: center; gap: 10px; }
.fd-frg-stack-card {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  padding: 12px 16px;
  border: 1px solid var(--fd-frg-line-2);
  border-radius: 16px;
  background: var(--fd-frg-surface);
  margin-left: calc(var(--i) * 20px);
  font: 400 0.8125rem/1 var(--fd-frg-mono-f);
  color: var(--fd-frg-fg);
  transition: transform var(--fd-dur-3) var(--fd-spring), border-color 0.3s ease, background-color 0.3s ease;
}
.fd-frg-stack-card.fd-frg-stack-active {
  border-color: rgba(217, 119, 87, 0.45);
  background: #141414;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
}
.fd-frg-tile:hover .fd-frg-stack-card { transform: translateX(calc(var(--i) * 6px)); }
.fd-frg-stack-top { display: flex; align-items: center; gap: 10px; width: 100%; }
.fd-frg-stack-top svg { color: var(--fd-frg-accent); flex: none; }
.fd-frg-stack-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.fd-frg-stack-badge {
  font-size: 0.6875rem;
  color: var(--fd-frg-dim);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-style: normal;
}
.fd-frg-stack-badge[data-active] {
  color: var(--fd-frg-accent);
  font-weight: 600;
}
.fd-frg-stack-live {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.fd-frg-stack-live span { font-size: 0.6875rem; color: var(--fd-frg-mute); }
.fd-frg-stack-live em { font-size: 0.6875rem; color: var(--fd-frg-accent); font-style: normal; font-family: var(--fd-frg-mono-f); }
.fd-frg-stack-bar {
  flex: 1;
  max-width: 80px;
  height: 4px;
  border-radius: 9999px;
  background: var(--fd-frg-surface-2);
  overflow: hidden;
  position: relative;
}
.fd-frg-stack-bar i {
  position: absolute;
  inset: 0;
  border-radius: 9999px;
  background: linear-gradient(90deg, #D97757, #FFA726);
  animation: fd-frg-stack-flow 1.8s ease-in-out infinite alternate;
}
@keyframes fd-frg-stack-flow { from { width: 35%; } to { width: 100%; } }

.fd-frg-vis-flake-box { display: flex; flex-direction: column; justify-content: center; gap: 14px; }
.fd-frg-flake-header { display: flex; justify-content: space-between; align-items: center; font-size: 0.6875rem; color: var(--fd-frg-accent); letter-spacing: 0.04em; }
.fd-frg-flake-pct { font-weight: 600; font-family: var(--fd-frg-mono-f); }
.fd-frg-vis-flake { display: grid; grid-template-columns: repeat(12, 1fr); gap: 6px; align-content: center; }
.fd-frg-vis-flake i { aspect-ratio: 1; border-radius: 4px; background: var(--fd-frg-surface-2); transition: background-color 0.25s ease, transform 0.25s ease; }
.fd-frg-vis-flake i[data-f="done"] { background: var(--fd-frg-accent); opacity: 0.9; }
.fd-frg-vis-flake i[data-f="active"] { background: #FFA726; box-shadow: 0 0 8px #FFA726; animation: fd-frg-chunk-pulse 0.7s infinite alternate; }
@keyframes fd-frg-chunk-pulse { from { opacity: 0.5; transform: scale(0.92); } to { opacity: 1; transform: scale(1.08); } }
.fd-frg-vis-cache { display: flex; flex-direction: column; justify-content: center; }
.fd-frg-vis-cache span { font: 600 4.5rem/1 var(--fd-frg-sans); letter-spacing: -0.06em; color: #fff; }
.fd-frg-vis-cache small { margin-top: 8px; font: 400 0.75rem/1 var(--fd-frg-mono-f); color: var(--fd-frg-accent); }
.fd-frg-vis-chart { position: relative; }
.fd-frg-vis-chart svg { width: 100%; height: 100%; min-height: 160px; }
.fd-frg-chart-tag { position: absolute; left: 41%; top: 6px; font: 400 0.6875rem/1 var(--fd-frg-mono-f); color: var(--fd-frg-accent); }

/* supported players (Uniform, Uncompressed, Authentic Icons) */
.fd-frg-int {
  --mx: -999px; --my: -999px;
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-top: 56px;
  align-items: stretch;
}
.fd-frg-int-cell {
  --mx: -999px; --my: -999px;
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: #0A0A0A;
  border: 1px solid var(--fd-frg-line);
  border-radius: 24px;
  color: var(--fd-frg-fg);
  transition: border-color var(--fd-dur-2) var(--fd-ease-out), transform var(--fd-dur-2);
}
.fd-frg-int-cell:hover {
  border-color: rgba(217,119,87,0.35);
  transform: translateY(-2px);
}
.fd-frg-logo-box {
  width: 48px;
  height: 48px;
  flex: none;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}
.fd-frg-int-cell b {
  display: block;
  font: 600 1.0625rem/1.25 var(--fd-frg-sans);
  letter-spacing: -0.015em;
  color: #FFFFFF;
}
.fd-frg-int-cell span {
  display: block;
  margin-top: 8px;
  font: 400 0.8125rem/1.55 var(--fd-frg-sans);
  color: var(--fd-frg-mute);
}

/* proof */
.fd-frg-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-top: 1px solid var(--fd-frg-line-2); border-bottom: 1px solid var(--fd-frg-line); }
.fd-frg-stats div { padding: 32px 24px 32px 0; }
.fd-frg-stats div + div { padding-left: 24px; border-left: 1px solid var(--fd-frg-line); }
.fd-frg-stats dt { font: 600 clamp(1.75rem, 3vw, 2.5rem)/1 var(--fd-frg-sans); letter-spacing: -0.045em; white-space: nowrap; color: #fff; }
.fd-frg-stats dd { margin-top: 10px; font: 400 0.875rem/1.45 var(--fd-frg-sans); color: var(--fd-frg-mute); }
.fd-frg-quote { max-width: 900px; margin: 96px auto 0; text-align: center; }
.fd-frg-quote blockquote { font: 500 clamp(1.5rem, 2.8vw, 2.25rem)/1.35 var(--fd-frg-sans); letter-spacing: -0.03em; color: #fff; }
.fd-frg-quote figcaption { display: inline-flex; align-items: center; gap: 12px; margin-top: 32px; text-align: left; }
.fd-frg-quote b { display: block; font: 500 0.9375rem/1.3 var(--fd-frg-sans); }
.fd-frg-quote small { display: block; font: 400 0.8125rem/1.3 var(--fd-frg-sans); color: var(--fd-frg-accent); }

/* FAQ (Curved Items) */
.fd-frg-faq-list { margin-top: 56px; display: grid; gap: 12px; max-width: 900px; }
.fd-frg-faq-item { border: 1px solid var(--fd-frg-line); border-radius: 20px; background: #0A0A0A; overflow: hidden; transition: border-color var(--fd-dur-2); }
.fd-frg-faq-item:hover { border-color: rgba(217,119,87,0.25); }
.fd-frg-faq-btn { display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 22px 28px; font: 600 1.0625rem/1.3 var(--fd-frg-sans); color: #fff; text-align: left; }
.fd-frg-faq-icon { font-size: 1.25rem; color: var(--fd-frg-accent); }
.fd-frg-faq-a { padding: 0 28px 24px; font: 400 0.9375rem/1.6 var(--fd-frg-sans); color: var(--fd-frg-mute); }

/* cta with Copier station */
.fd-frg-cta { position: relative; padding: 120px 0; border-top: 1px solid var(--fd-frg-line); overflow: hidden; isolation: isolate; }
.fd-frg-cta-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: 56px;
  align-items: center;
}
.fd-frg-cta-left {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}
.fd-frg-cta-left .fd-frg-cta-h {
  text-align: left;
  margin-top: 14px;
  max-width: 14em;
  font: 600 clamp(2.25rem, 5vw, 4rem)/1.1 var(--fd-frg-sans);
  letter-spacing: -0.05em;
  color: #fff;
}
.fd-frg-cta-left .fd-frg-p {
  margin-left: 0;
  margin-right: 0;
  max-width: 32em;
}
.fd-frg-cta-hint {
  font-size: 0.875rem;
  color: var(--fd-frg-dim);
  margin-top: 16px;
}
.fd-frg-copied-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #3DDC84;
  font-weight: 600;
  animation: fd-frg-in 0.3s ease-out;
}
.fd-frg-cta-left .fd-frg-ctas {
  justify-content: flex-start;
  margin-top: 28px;
}
.fd-frg-cta-right {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}
.fd-frg-copier-frame {
  position: relative;
  width: 100%;
  max-width: 440px;
  height: 580px;
  border-radius: 32px;
  background: radial-gradient(circle at 50% 15%, rgba(217, 119, 87, 0.08) 0%, #0A0A0A 70%);
  border: 1px solid var(--fd-frg-line-2);
  padding: 18px;
  box-shadow: 0 24px 64px -24px rgba(0, 0, 0, 0.95), 0 0 80px -40px rgba(217, 119, 87, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.fd-frg-printer-container {
  margin-top: 64px;
  width: 100%;
}
.fd-frg-printer-stage {
  width: 100%;
  height: 640px;
  border-radius: 28px;
  overflow: hidden;
  position: relative;
  background: radial-gradient(ellipse at 50% 18%, rgba(217, 119, 87, 0.08) 0%, rgba(13, 14, 19, 0.96) 55%, #08090C 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 32px 64px -24px rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 960px) {
  .fd-frg-cta-grid {
    grid-template-columns: 1fr;
    gap: 48px;
    text-align: center;
  }
  .fd-frg-cta-left {
    align-items: center;
    text-align: center;
  }
  .fd-frg-cta-left .fd-frg-cta-h {
    text-align: center;
    max-width: 100%;
  }
  .fd-frg-cta-left .fd-frg-ctas {
    justify-content: center;
  }
  .fd-frg-copier-frame {
    height: 520px;
    max-width: 380px;
  }
}
@media (max-width: 480px) {
  .fd-frg-copier-frame {
    height: 440px;
    max-width: 320px;
    padding: 10px;
  }
}

/* footer (No Green Dot) */
.fd-frg-foot { padding: 72px 0 32px; border-top: 1px solid var(--fd-frg-line); background: var(--fd-frg-bg); }
.fd-frg-foot-top { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 24px; }
.fd-frg-foot-p { margin-top: 10px; max-width: 26em; font: 400 0.875rem/1.5 var(--fd-frg-sans); color: var(--fd-frg-mute); }
.fd-frg-status {
  display: inline-flex;
  align-items: center;
  margin-top: 14px;
  height: 30px;
  padding: 0 14px;
  border: 1px solid var(--fd-frg-line-2);
  border-radius: 9999px;
  font: 500 0.75rem/1 var(--fd-frg-sans);
  color: var(--fd-frg-mute);
  letter-spacing: 0.02em;
}
.fd-frg-foot-bot { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--fd-frg-line); font: 400 0.8125rem/1.3 var(--fd-frg-sans); color: var(--fd-frg-dim); }

/* reveal */
.fd-frg[data-js] [data-reveal] { opacity: 0; transform: translateY(18px); transition: opacity var(--fd-dur-4) var(--fd-ease-out), transform 900ms var(--fd-ease-out); transition-delay: calc(var(--i, 0) * 70ms); }
.fd-frg[data-js] [data-reveal][data-in] { opacity: 1; transform: none; }

/* responsive */
@media (max-width: 1000px) {
  .fd-frg-nav-links { display: none; }
  .fd-frg-burger { display: block; }
  .fd-frg-tl-grid { grid-template-columns: 1fr; gap: 48px; }
  .fd-frg-sticky-head { position: static; }
  .fd-frg-diff-body { grid-template-columns: 1fr; }
  .fd-frg-code { border-right: 0; border-bottom: 1px solid var(--fd-frg-line); }
  .fd-frg-int { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fd-frg-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fd-frg-stats div:nth-child(3) { padding-left: 0; border-left: 0; }
  .fd-frg-stats div:nth-child(n + 3) { border-top: 1px solid var(--fd-frg-line); }
}
/* responsive mobile & tablet styling (World-Class Desktop Feel on Mobile) */
@media (max-width: 1000px) {
  .fd-frg-nav-links { display: none; }
  .fd-frg-burger { display: block; }
  .fd-frg-tl-grid { grid-template-columns: 1fr; gap: 48px; }
  .fd-frg-sticky-head { position: static; }
  .fd-frg-diff-body { grid-template-columns: 1fr; }
  .fd-frg-code { border-right: 0; border-bottom: 1px solid var(--fd-frg-line); }
  .fd-frg-int { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fd-frg-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fd-frg-stats div:nth-child(3) { padding-left: 0; border-left: 0; }
  .fd-frg-stats div:nth-child(n + 3) { border-top: 1px solid var(--fd-frg-line); }
}

@media (max-width: 768px) {
  .fd-frg { overflow-x: hidden; }
  .fd-frg-wrap { padding: 0 20px; }
  .fd-frg-nav-in { padding: 0 16px; height: 60px; }
  
  /* Navbar */
  .fd-frg-brand-text { font-size: 1.1875rem; }
  .fd-frg-nav-right { gap: 8px; }
  .fd-frg-nav-right .fd-frg-btn { height: 36px; padding: 0 14px; font-size: 0.8125rem; }
  .fd-frg-burger { width: 38px; height: 38px; }

  /* Hero Section */
  .fd-frg-hero { padding-top: 108px; padding-bottom: 72px; }
  .fd-frg-pill {
    max-width: 100%;
    height: auto;
    padding: 6px 14px;
    gap: 8px;
    font-size: 0.78125rem;
    line-height: 1.4;
  }
  .fd-frg-pill-txt {
    overflow: visible;
    text-overflow: unset;
    white-space: normal;
  }
  .fd-frg-h1 {
    font-size: clamp(2.25rem, 6.8vw, 3rem);
    line-height: 1.08;
    letter-spacing: -0.04em;
    margin-top: 20px;
  }
  .fd-frg-lede {
    font-size: 0.9688rem;
    line-height: 1.6;
    margin-top: 18px;
    padding: 0 4px;
    max-width: 32em;
  }
  .fd-frg-ctas {
    flex-direction: row;
    justify-content: center;
    width: 100%;
    margin: 28px auto 0;
    gap: 12px;
  }
  .fd-frg-ctas .fd-frg-btn {
    height: 46px;
    padding: 0 20px;
    font-size: 0.875rem;
  }

  /* Hero Terminal (Full Desktop Alignment & Proportions) */
  .fd-frg-hero-term { margin-top: 40px; }
  .fd-frg-term { border-radius: 22px; }
  .fd-frg-term-bar { height: 40px; padding: 0 16px; justify-content: space-between; }
  .fd-frg-term-title { display: block; font-size: 0.72rem; }
  .fd-frg-term-body {
    height: auto;
    min-height: 280px;
    padding: 16px 20px;
    font-size: 0.7188rem;
    line-height: 1.85;
    white-space: pre;
    overflow-x: auto;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }
  .fd-frg-tl {
    white-space: pre;
    gap: 8px;
  }

  /* Section Spacing */
  .fd-frg-sec { padding: 84px 0; }
  .fd-frg-eyebrow { font-size: 0.75rem; }
  .fd-frg-h2 { font-size: clamp(1.875rem, 5.2vw, 2.5rem); line-height: 1.15; letter-spacing: -0.03em; }
  .fd-frg-p { font-size: 0.9375rem; line-height: 1.55; }

  /* Supported Apps Marquee */
  .fd-frg-logos { padding: 0 0 68px; }
  .fd-frg-marquee-item { height: 62px; padding: 0 24px; min-width: 150px; font-size: 0.8125rem; gap: 8px; }

  /* Step 01 Timeline Flow - Pixel-Perfect Rail & Node Alignment */
  .fd-frg-steps { padding-left: 44px; }
  .fd-frg-rail { left: 14px; width: 2px; }
  .fd-frg-node { left: -36px; top: 6px; width: 12px; height: 12px; }
  .fd-frg-steps li { padding-bottom: 48px; }
  .fd-frg-steps h3 { font-size: 1.25rem; line-height: 1.28; }
  .fd-frg-steps p { font-size: 0.9063rem; line-height: 1.55; }
  .fd-frg-meter { flex-wrap: wrap; gap: 10px; }
  .fd-frg-meter-grid { max-width: 170px; }
  .fd-frg-meter-grid i:nth-child(n + 25) { display: none; }
  .fd-frg-meter b { font-size: 0.72rem; }

  /* Step 02 Media Stream Analyzer (Full Desktop Inspection Table) */
  .fd-frg-diff { border-radius: 22px; margin-top: 40px; }
  .fd-frg-diff-bar { flex-wrap: nowrap; height: 46px; padding: 0 18px; }
  .fd-frg-diff-status { font-size: 0.75rem; }
  .fd-frg-code {
    padding: 14px 16px;
    font-size: 0.7188rem;
    overflow-x: auto;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }
  .fd-frg-dl {
    grid-template-columns: 44px 44px 18px 1fr;
    white-space: nowrap;
    gap: 4px;
    line-height: 1.85;
  }
  .fd-frg-ln:first-child { display: block; }
  .fd-frg-ln { text-align: left; color: var(--fd-frg-dim); font-weight: 500; padding-right: 4px; }
  .fd-frg-src { overflow: hidden; text-overflow: ellipsis; }
  .fd-frg-comments { padding: 18px; }
  .fd-frg-cmt { padding: 16px; border-radius: 16px; }
  .fd-frg-cmt header b { font-size: 0.8438rem; }
  .fd-frg-cmt p { font-size: 0.8125rem; line-height: 1.55; }

  /* Step 03 Speed Test Waterfall Chart (Spacious Side-by-Side Desktop Layout) */
  .fd-frg-speed { height: 280vh; }
  .fd-frg-speed-stick { top: 60px; height: calc(100vh - 60px); }
  .fd-frg-clock-row {
    grid-template-columns: 1fr 1fr;
    gap: 0;
    border-radius: 20px;
  }
  .fd-frg-clock { padding: 14px 18px; }
  .fd-frg-clock-n { font-size: 2.5rem; }
  .fd-frg-gantt {
    margin-top: 14px;
    padding: 24px 0 4px;
    display: grid;
    gap: 8px;
  }
  .fd-frg-gantt-axis {
    position: absolute;
    left: 155px;
    right: 48px;
    top: 0;
    height: 18px;
  }
  .fd-frg-gantt-axis span { font-size: 0.72rem; }
  .fd-frg-job {
    display: grid;
    grid-template-columns: 155px 1fr 48px;
    align-items: center;
    height: 32px;
  }
  .fd-frg-job-name {
    grid-column: 1 / 2;
    font-size: 0.72rem;
    font-weight: 500;
    gap: 8px;
    padding-right: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .fd-frg-step-idx { width: 18px; height: 18px; font-size: 0.625rem; }
  .fd-frg-job-track {
    grid-column: 2 / 3;
    height: 100%;
  }
  .fd-frg-job-dur {
    grid-column: 3 / 4;
    font-size: 0.72rem;
    line-height: 32px;
    padding-left: 8px;
    text-align: right;
  }
  .fd-frg-playhead {
    top: 20px;
    bottom: 0;
    left: calc(155px + (100% - 155px - 48px) * var(--p));
  }

  /* Step 04 Bento Benefits */
  .fd-frg-bento { grid-template-columns: 1fr; gap: 16px; margin-top: 40px; }
  .fd-frg-tile-wide { grid-column: auto; }
  .fd-frg-tile { min-height: auto; padding: 26px; border-radius: 22px; }
  .fd-frg-tile h3 { font-size: 1.1875rem; }
  .fd-frg-vis-stack { margin: 10px 0; }
  .fd-frg-vis-stack .fd-frg-stack-card { margin-left: calc(var(--i) * 10px); padding: 12px 14px; gap: 6px; font-size: 0.72rem; }
  .fd-frg-vis-flake { grid-template-columns: repeat(12, 1fr); gap: 4px; }

  /* Step 05 Live Receipt Printer */
  .fd-frg-printer-container { margin-top: 36px; }
  .fd-frg-printer-stage { height: 540px; border-radius: 22px; padding: 12px; }

  /* Supported Players Grid */
  .fd-frg-int { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 36px; }
  .fd-frg-int-cell { padding: 18px; border-radius: 18px; }

  /* Final CTA */
  .fd-frg-cta { padding: 96px 0; }
  .fd-frg-cta-grid { gap: 42px; }
  .fd-frg-cta-h { font-size: clamp(2rem, 5.5vw, 2.75rem); }
  .fd-frg-copier-frame { height: 460px; max-width: 360px; margin: 0 auto; padding: 12px; }
  .fd-frg-foot-top { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  .fd-frg *, .fd-frg *::before, .fd-frg *::after { animation: none !important; }
  .fd-frg[data-js] [data-reveal] { transform: none; transition: opacity 120ms linear; transition-delay: 0ms; }
  .fd-frg-cmt { transform: none; transition: opacity 120ms linear; }
  .fd-frg-speed { height: auto; padding: 96px 0; }
  .fd-frg-speed-stick { position: relative; height: auto; }
  .fd-frg-caret { display: none; }
}
`;
