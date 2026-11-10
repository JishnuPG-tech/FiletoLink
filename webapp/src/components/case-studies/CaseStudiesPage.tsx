import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import MilkGlassFolder, { MilkGlassItem } from "./MilkGlassFolder";
import {
  ArrowLeft,
  Film,
  HardDrive,
  Clock,
  ExternalLink,
  Users as UsersIcon,
  RefreshCw,
  Server,
  BarChart3,
  PieChart,
  ShieldCheck,
  Cpu,
  Activity,
  Database,
  Network,
  Mail,
  GitBranch,
  Layers,
  TrendingUp,
  CheckCircle2,
  Terminal,
  Globe,
  Radio,
  FileText
} from "lucide-react";

interface TelegramBotUser {
  id: number;
  name: string;
  username: string;
  join_date?: string;
  last_active?: string;
  total_files: number;
}

interface UserConvertedFile {
  file_name: string;
  file_size: string;
  media_type: string;
  converted_at: string;
  public_hash?: string;
}

interface StaticFolderConfig {
  id: string;
  title: string;
  caption: string;
  shimmer: [string, string, string];
  items: MilkGlassItem[];
}

const STATIC_FOLDERS: StaticFolderConfig[] = [
  {
    id: "autonomous-ai",
    title: "Autonomous AI",
    caption: "4 Deployments",
    shimmer: ["#D97757", "#8A4F3D", "#C4927C"],
    items: [
      {
        type: "image",
        title: "TMDB 9:00 AM Autopilot",
        meta: "Automated OTT release curation",
        byline: "4K posters & daily Telegram feed",
        image: {
          src: "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?w=800&auto=format&fit=crop&q=80",
          alt: "Film production",
        },
        link: "https://t.me/flashfilez",
      },
      {
        type: "image",
        title: "Weekly Milestone Teleprinter",
        meta: "Automated health & performance cards",
        byline: "Sunday 8:00 PM network broadcast",
        image: {
          src: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80",
          alt: "Analytics dashboard",
        },
        link: "https://t.me/flashfilezbot",
      },
      {
        type: "image",
        title: "Realtime Force-Sub Verifier",
        meta: "Sub-50ms membership check",
        byline: "Anti-flood token bucket rate limiting",
        image: {
          src: "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&auto=format&fit=crop&q=80",
          alt: "Biometric security",
        },
        link: "https://t.me/flashfilez",
      },
      {
        type: "image",
        title: "Omniroute Multi-Model Brain",
        meta: "Context-engineered agent framework",
        byline: "Intelligent prompt routing",
        image: {
          src: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop&q=80",
          alt: "Abstract intelligence",
        },
        link: "https://github.com/JishnuPG-tech/FiletoLink",
      },
    ],
  },
  {
    id: "kinetic-ui",
    title: "Kinetic UI Physics",
    caption: "4 Experiments",
    shimmer: ["#38BDF8", "#0369A1", "#BAE6FD"],
    items: [
      {
        type: "image",
        title: "Milk Glass Folder Envelope",
        meta: "Procedural grain & 3D card fanning",
        byline: "CSS container query scaling (cqw)",
        image: {
          src: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&auto=format&fit=crop&q=80",
          alt: "Minimal architecture",
        },
        link: "https://framer.com/m/MilkGlassFolder-WLP5FF.js@iT1pE3GkDkeFYqn3xFXA",
      },
      {
        type: "image",
        title: "Liquid Glass Ambient Tokens",
        meta: "Pitch black (#000000) & Claude Orange",
        byline: "Zero AI slop UI design philosophy",
        image: {
          src: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop&q=80",
          alt: "Prism reflections",
        },
        link: "https://jishnupg-filetolink.hf.space/",
      },
      {
        type: "image",
        title: "60 FPS Spring Choreography",
        meta: "Damped spring bezier physics",
        byline: "Instant peek & velocity interpolation",
        image: {
          src: "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&auto=format&fit=crop&q=80",
          alt: "Fluid wave",
        },
        link: "https://github.com/JishnuPG-tech/FiletoLink",
      },
      {
        type: "image",
        title: "Adaptive Mobile Landscape",
        meta: "Dynamic device orientation guidance",
        byline: "Auto-dismissible session alerts",
        image: {
          src: "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&auto=format&fit=crop&q=80",
          alt: "Mobile device",
        },
        link: "https://jishnupg-filetolink.hf.space/",
      },
    ],
  },
  {
    id: "cloud-architecture",
    title: "Cloud Infrastructure",
    caption: "4 Architectures",
    shimmer: ["#34D399", "#065F46", "#A7F3D0"],
    items: [
      {
        type: "image",
        title: "16-vCPU Cloud Container",
        meta: "Zero cold start streaming cluster",
        byline: "Persistent rclone cloud snapshotting",
        image: {
          src: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=800&auto=format&fit=crop&q=80",
          alt: "Server racks",
        },
        link: "https://huggingface.co/spaces/Jishnupg/FileToLink",
      },
      {
        type: "image",
        title: "Anti-Header-Injection Gate",
        meta: "RFC 6266 & CRLF injection defense",
        byline: "Strict UTF-8 filename quoting",
        image: {
          src: "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800&auto=format&fit=crop&q=80",
          alt: "Code security",
        },
        link: "https://github.com/JishnuPG-tech/FiletoLink",
      },
      {
        type: "image",
        title: "Sharded MongoDB Engine",
        meta: "Compound indexed user timeline",
        byline: "Unified historical & live conversions",
        image: {
          src: "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=800&auto=format&fit=crop&q=80",
          alt: "Database nodes",
        },
        link: "https://jishnupg-filetolink.hf.space/",
      },
      {
        type: "image",
        title: "32/32 Automated Test Suite",
        meta: "Exhaustive PyTest security harness",
        byline: "Automated pre-deployment verification",
        image: {
          src: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop&q=80",
          alt: "Security terminal",
        },
        link: "https://github.com/JishnuPG-tech/FiletoLink",
      },
    ],
  },
];

const USER_SHIMMERS: [string, string, string][] = [
  ["#D97757", "#8A4F3D", "#C4927C"],
  ["#CF8A64", "#6A5045", "#A9B9C4"],
  ["#38BDF8", "#0369A1", "#BAE6FD"],
  ["#34D399", "#065F46", "#A7F3D0"],
  ["#A78BFA", "#5B21B6", "#DDD6FE"],
  ["#FBBF24", "#B45309", "#FDE68A"],
];

export interface CaseStudiesPageProps {
  onLogout?: () => void;
  onBackToHome?: () => void;
}

export const CaseStudiesPage: React.FC<CaseStudiesPageProps> = ({ onLogout, onBackToHome }) => {
  // Navigation states
  const [activeMainFolder, setActiveMainFolder] = useState<string | null>(null);
  const [activeSubFolder, setActiveSubFolder] = useState<"users" | "server" | "analysis" | "admin" | null>(null);
  const [selectedUser, setSelectedUser] = useState<TelegramBotUser | null>(null);
  const [activeStaticFolder, setActiveStaticFolder] = useState<StaticFolderConfig | null>(null);

  // Live Database States
  const [users, setUsers] = useState<TelegramBotUser[]>([]);
  const [userFiles, setUserFiles] = useState<UserConvertedFile[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // Real-time automatic polling for users
  useEffect(() => {
    let isMounted = true;

    const fetchLiveUsers = async () => {
      try {
        const res = await fetch("/api/admin/users");
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data && Array.isArray(data.users)) {
            setUsers(data.users);
          }
        }
      } catch (err) {
        console.debug("Live sync polling...", err);
      } finally {
        if (isMounted) setLoadingUsers(false);
      }
    };

    fetchLiveUsers();
    const userInterval = setInterval(fetchLiveUsers, 3500);

    return () => {
      isMounted = false;
      clearInterval(userInterval);
    };
  }, []);

  // Real-time automatic polling for selected user's files
  useEffect(() => {
    if (!selectedUser) {
      setUserFiles([]);
      return;
    }

    let isMounted = true;
    setLoadingFiles(true);

    const fetchLiveUserFiles = async () => {
      try {
        const res = await fetch(`/api/admin/user/${selectedUser.id}/files`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data && Array.isArray(data.files)) {
            setUserFiles(data.files);
          }
        }
      } catch (err) {
        console.debug("User files sync polling...", err);
      } finally {
        if (isMounted) setLoadingFiles(false);
      }
    };

    fetchLiveUserFiles();
    const fileInterval = setInterval(fetchLiveUserFiles, 2500);

    return () => {
      isMounted = false;
      clearInterval(fileInterval);
    };
  }, [selectedUser]);

  // Keyboard navigation: Escape key goes back step-by-step
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (selectedUser) {
          setSelectedUser(null);
        } else if (activeSubFolder) {
          setActiveSubFolder(null);
        } else if (activeMainFolder) {
          setActiveMainFolder(null);
        } else if (activeStaticFolder) {
          setActiveStaticFolder(null);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedUser, activeSubFolder, activeMainFolder, activeStaticFolder]);

  // Clean filename: trim extensions, replace periods/underscores with spaces
  const formatCleanTitle = (rawName: string) => {
    if (!rawName) return "Unnamed Media";
    let clean = rawName.replace(/\.[a-zA-Z0-9]{2,4}$/, "");
    clean = clean.replace(/[._]/g, " ");
    return clean.trim();
  };

  // Determine quality tag
  const getQuality = (name: string) => {
    if (!name) return "HD";
    const upper = name.toUpperCase();
    if (upper.includes("2160P") || upper.includes("4K") || upper.includes("UHD")) return "4K UHD";
    if (upper.includes("1080P") || upper.includes("FHD")) return "1080p";
    if (upper.includes("720P")) return "720p";
    if (upper.includes("HDR")) return "HDR";
    return "HD";
  };

  // Total conversions across all users
  const totalConversionsCount = users.reduce((acc, u) => acc + (u.total_files || 0), 0);

  return (
    <div className="min-h-screen w-full bg-[#000000] text-neutral-100 flex flex-col justify-start items-start p-6 sm:p-10 lg:p-14 relative overflow-x-hidden font-sans select-none text-left">
      {/* Ambient background glow */}
      <div
        className="fixed top-1/3 left-1/4 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full blur-[200px] pointer-events-none opacity-15"
        style={{
          background: "radial-gradient(circle, #D97757 0%, rgba(217,119,87,0) 70%)"
        }}
      />

      <AnimatePresence mode="wait">
        {/* ================= LEVEL 1: MAIN GALLERY (Linear left-to-right) ================= */}
        {!activeMainFolder && !activeStaticFolder && (
          <motion.div
            key="main-overview"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full flex flex-col gap-6"
          >
            {/* Top Left Apex Branding & Session Controls */}
            <div className="pb-3 flex items-center justify-between w-full">
              <div className="flex items-center gap-3">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white font-sans">
                  Apex
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  Admin Authority
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onBackToHome || (() => { window.location.href = "/"; })}
                  className="px-3 py-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-xs font-medium text-neutral-300 hover:text-white border border-white/[0.06] transition-all cursor-pointer"
                >
                  FlashFile Home
                </button>
                {onLogout && (
                  <button
                    type="button"
                    onClick={onLogout}
                    className="px-3 py-1.5 rounded-full bg-red-500/10 hover:bg-red-500/20 text-xs font-medium text-red-300 border border-red-500/20 transition-all cursor-pointer"
                  >
                    Lock Session
                  </button>
                )}
              </div>
            </div>

            {/* Linear Row-wise Folders aligned left to right */}
            <div className="flex flex-wrap items-start justify-start gap-6 sm:gap-8 w-full">
              {/* 1st Folder: "FlashFile" (Contains Users, Server, Analysis, Admin) */}
              <div
                onClick={() => setActiveMainFolder("flashfile")}
                className="w-[200px] sm:w-[220px] flex-shrink-0 cursor-pointer group transition-transform duration-300 hover:scale-[1.03] active:scale-[0.98]"
              >
                <MilkGlassFolder
                  title="FlashFile"
                  caption="4 Modules"
                  items={[
                    { type: "image", title: "Users Directory", meta: "Telegram Community" },
                    { type: "image", title: "Server Engine", meta: "Operational Mesh" },
                    { type: "image", title: "Bot Analysis", meta: "Realtime Analytics" },
                    { type: "image", title: "Admin Portal", meta: "System Authority" },
                  ]}
                  colors={{
                    tone: "dark",
                    shimmer1: "#CF8A64",
                    shimmer2: "#6A5045",
                    shimmer3: "#A9B9C4",
                  }}
                  look={{
                    folder: "18px",
                    cards: "12px",
                  }}
                  motion={{
                    hover: false,
                    entrance: true,
                  }}
                />
              </div>

              {/* Other System Folders */}
              {STATIC_FOLDERS.map((folder) => (
                <div
                  key={folder.id}
                  onClick={() => setActiveStaticFolder(folder)}
                  className="w-[200px] sm:w-[220px] flex-shrink-0 cursor-pointer group transition-transform duration-300 hover:scale-[1.03] active:scale-[0.98]"
                >
                  <MilkGlassFolder
                    title={folder.title}
                    caption={folder.caption}
                    items={folder.items}
                    colors={{
                      tone: "dark",
                      shimmer1: folder.shimmer[0],
                      shimmer2: folder.shimmer[1],
                      shimmer3: folder.shimmer[2],
                    }}
                    look={{
                      folder: "18px",
                      cards: "12px",
                    }}
                    motion={{
                      hover: false,
                      entrance: true,
                    }}
                  />
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* ================= LEVEL 2: INSIDE "FlashFile" FOLDER (Shows 4 Folders: Users, Server, Analysis, Admin) ================= */}
        {activeMainFolder === "flashfile" && !activeSubFolder && (
          <motion.div
            key="flashfile-overview"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full flex flex-col gap-6"
          >
            {/* Top Navigation Bar */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] w-full">
              <button
                onClick={() => setActiveMainFolder(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-neutral-200 text-xs font-medium border border-white/[0.08] transition-all cursor-pointer group"
              >
                <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                <span>Back</span>
              </button>

              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-[#D97757]" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  FlashFile
                </span>
                <span className="text-xs text-neutral-500 font-mono">
                  (4 Folders)
                </span>
              </div>
            </div>

            {/* 4 Linear Folders Left-to-Right */}
            <div className="flex flex-wrap items-start justify-start gap-6 sm:gap-8 w-full py-2">
              {/* Folder 1: Users */}
              <div
                onClick={() => setActiveSubFolder("users")}
                className="w-[190px] sm:w-[210px] flex-shrink-0 cursor-pointer group transition-transform duration-300 hover:scale-[1.04] active:scale-[0.98]"
              >
                <MilkGlassFolder
                  title="Users"
                  caption={`${users.length} Users`}
                  items={[
                    { type: "image", title: "Active Bot Users", meta: "Telegram Community" },
                    { type: "image", title: "User Library", meta: "Converted Streams" },
                  ]}
                  colors={{
                    tone: "dark",
                    shimmer1: "#CF8A64",
                    shimmer2: "#6A5045",
                    shimmer3: "#A9B9C4",
                  }}
                  look={{
                    folder: "16px",
                    cards: "11px",
                  }}
                  motion={{
                    hover: false,
                    entrance: true,
                  }}
                />
              </div>

              {/* Folder 2: Server */}
              <div
                onClick={() => setActiveSubFolder("server")}
                className="w-[190px] sm:w-[210px] flex-shrink-0 cursor-pointer group transition-transform duration-300 hover:scale-[1.04] active:scale-[0.98]"
              >
                <MilkGlassFolder
                  title="Server"
                  caption="Operational • 16 vCPU"
                  items={[
                    { type: "image", title: "Gateway Mesh", meta: "FastAPI & Nginx" },
                    { type: "image", title: "Process Nodes", meta: "Jellyfin & Pyrogram" },
                  ]}
                  colors={{
                    tone: "dark",
                    shimmer1: "#34D399",
                    shimmer2: "#065F46",
                    shimmer3: "#A7F3D0",
                  }}
                  look={{
                    folder: "16px",
                    cards: "11px",
                  }}
                  motion={{
                    hover: false,
                    entrance: true,
                  }}
                />
              </div>

              {/* Folder 3: Analysis */}
              <div
                onClick={() => setActiveSubFolder("analysis")}
                className="w-[190px] sm:w-[210px] flex-shrink-0 cursor-pointer group transition-transform duration-300 hover:scale-[1.04] active:scale-[0.98]"
              >
                <MilkGlassFolder
                  title="Analysis"
                  caption="Charts & Insights"
                  items={[
                    { type: "image", title: "Conversion Velocity", meta: "7-Day Activity Trends" },
                    { type: "image", title: "Media Formats", meta: "Donut & Pie Ratios" },
                  ]}
                  colors={{
                    tone: "dark",
                    shimmer1: "#38BDF8",
                    shimmer2: "#0369A1",
                    shimmer3: "#BAE6FD",
                  }}
                  look={{
                    folder: "16px",
                    cards: "11px",
                  }}
                  motion={{
                    hover: false,
                    entrance: true,
                  }}
                />
              </div>

              {/* Folder 4: Admin */}
              <div
                onClick={() => setActiveSubFolder("admin")}
                className="w-[190px] sm:w-[210px] flex-shrink-0 cursor-pointer group transition-transform duration-300 hover:scale-[1.04] active:scale-[0.98]"
              >
                <MilkGlassFolder
                  title="Admin"
                  caption="@Jishnuxpg • Owner"
                  items={[
                    { type: "image", title: "System Authority", meta: "Owner Credentials" },
                    { type: "image", title: "Cluster Control", meta: "GitHub & Cloud Space" },
                  ]}
                  colors={{
                    tone: "dark",
                    shimmer1: "#D97757",
                    shimmer2: "#8A4F3D",
                    shimmer3: "#C4927C",
                  }}
                  look={{
                    folder: "16px",
                    cards: "11px",
                  }}
                  motion={{
                    hover: false,
                    entrance: true,
                  }}
                />
              </div>
            </div>
          </motion.div>
        )}

        {/* ================= LEVEL 3: INSIDE "Users" FOLDER (Linear left-to-right user folders) ================= */}
        {activeMainFolder === "flashfile" && activeSubFolder === "users" && !selectedUser && (
          <motion.div
            key="users-directory"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full flex flex-col gap-6"
          >
            {/* Top Navigation Bar */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] w-full">
              <button
                onClick={() => setActiveSubFolder(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-neutral-200 text-xs font-medium border border-white/[0.08] transition-all cursor-pointer group"
              >
                <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                <span>Back to FlashFile</span>
              </button>

              <div className="flex items-center gap-2">
                <UsersIcon className="w-4 h-4 text-[#D97757]" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  Users
                </span>
                <span className="text-xs text-neutral-500 font-mono">
                  ({users.length})
                </span>
              </div>
            </div>

            {/* Sub-Folders: One small MilkGlassFolder per user from Telegram database */}
            {loadingUsers && users.length === 0 ? (
              <div className="py-20 text-xs text-neutral-500 flex items-center justify-start gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-[#D97757]" />
                <span>Connecting to Telegram bot database and fetching registered users...</span>
              </div>
            ) : users.length === 0 ? (
              <div className="py-20 text-xs text-neutral-400 flex flex-col gap-2">
                <span className="text-sm text-white font-medium">No users recorded in database yet</span>
                <span>Send any message or /start to <a href="https://t.me/flashfilezbot" target="_blank" rel="noreferrer" className="text-[#D97757] underline">@flashfilezbot</a> on Telegram to automatically generate a user folder.</span>
              </div>
            ) : (
              <div className="flex flex-wrap items-start justify-start gap-6 sm:gap-8 w-full py-2">
                {users.map((u, idx) => {
                  const shimmer = USER_SHIMMERS[idx % USER_SHIMMERS.length];
                  const displayTitle = u.username 
                    ? `@${u.username}` 
                    : (u.name && !u.name.startsWith("User ") ? u.name : `User ${u.id}`);
                  
                  const hasRealName = u.name && !u.name.startsWith("User ") && u.name !== `@${u.username}`;
                  const displayCaption = u.username && hasRealName
                    ? `${u.name} • ${u.total_files} files`
                    : (u.total_files > 0 ? `${u.total_files} files` : "");

                  return (
                    <div
                      key={u.id}
                      onClick={() => setSelectedUser(u)}
                      className="w-[180px] sm:w-[200px] flex-shrink-0 cursor-pointer group transition-transform duration-300 hover:scale-[1.04] active:scale-[0.98]"
                    >
                      <MilkGlassFolder
                        title={displayTitle}
                        caption={displayCaption}
                        items={[
                          { type: "image", title: "Converted Files", meta: "Telegram Stream Bot" },
                        ]}
                        colors={{
                          tone: "dark",
                          shimmer1: shimmer[0],
                          shimmer2: shimmer[1],
                          shimmer3: shimmer[2],
                        }}
                        look={{
                          folder: "16px",
                          cards: "11px",
                        }}
                        motion={{
                          hover: false,
                          entrance: true,
                        }}
                      />
                    </div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}

        {/* ================= LEVEL 4: INSIDE SPECIFIC USER FOLDER (Equal-size cards, truncated with ...) ================= */}
        {activeMainFolder === "flashfile" && activeSubFolder === "users" && selectedUser && (
          <motion.div
            key={`user-files-${selectedUser.id}`}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full flex flex-col gap-6"
          >
            {/* Top Navigation Bar */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] w-full">
              <button
                onClick={() => setSelectedUser(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-neutral-200 text-xs font-medium border border-white/[0.08] transition-all cursor-pointer group"
              >
                <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                <span>Back to Users</span>
              </button>

              <div className="flex items-center gap-3">
                <span className="size-2 rounded-full bg-[#D97757] animate-pulse" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  {selectedUser.username ? `@${selectedUser.username}` : selectedUser.name}
                </span>
                {selectedUser.username && selectedUser.name && selectedUser.name !== `@${selectedUser.username}` && !selectedUser.name.startsWith("User ") && (
                  <span className="text-xs text-neutral-400">
                    ({selectedUser.name})
                  </span>
                )}
                <span className="text-xs text-neutral-300 font-mono px-2.5 py-0.5 rounded-full bg-white/[0.06] border border-white/[0.08]">
                  {userFiles.length} {userFiles.length === 1 ? "file" : "files"}
                </span>
              </div>
            </div>

            {/* Movies and Series Cards Grid - strictly uniform dimensions, truncated with (...) */}
            {loadingFiles && userFiles.length === 0 ? (
              <div className="py-20 text-xs text-neutral-500 flex items-center justify-start gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-[#D97757]" />
                <span>Querying live MongoDB conversion history for {selectedUser.name}...</span>
              </div>
            ) : userFiles.length === 0 ? (
              <div className="py-20 text-xs text-neutral-400 flex flex-col gap-2">
                <span className="text-sm text-white font-medium">No files converted yet by {selectedUser.name}</span>
                <span>When this user forwards any video, movie, or series to <a href="https://t.me/flashfilezbot" target="_blank" rel="noreferrer" className="text-[#D97757] underline">@flashfilezbot</a>, it will appear here instantly.</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 w-full">
                {userFiles.map((file, idx) => {
                  const quality = getQuality(file.file_name);
                  const cleanName = formatCleanTitle(file.file_name);

                  return (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25, delay: idx * 0.04 }}
                      className="group h-[132px] w-full rounded-2xl bg-[#09090b] border border-white/[0.08] hover:border-white/[0.18] p-4 flex flex-col justify-between shadow-[0_10px_25px_rgba(0,0,0,0.5)] transition-all duration-300 hover:shadow-[0_12px_32px_rgba(217,119,87,0.12)] overflow-hidden"
                    >
                      {/* Top Badges Row */}
                      <div className="flex items-center justify-between gap-2 w-full">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#D97757]/10 border border-[#D97757]/20 text-[#D97757] text-[10px] font-mono font-semibold uppercase flex-shrink-0">
                          <Film className="w-3 h-3" /> {quality}
                        </span>
                        <span className="inline-flex items-center gap-1 text-[11px] text-neutral-400 font-mono truncate">
                          <HardDrive className="w-3 h-3 text-neutral-500 flex-shrink-0" /> {file.file_size || "Unknown"}
                        </span>
                      </div>

                      {/* Middle File Title: STRICTLY TRUNCATED with ellipsis (...) to preserve uniform height */}
                      <div className="w-full my-auto overflow-hidden">
                        <h4 
                          title={cleanName}
                          className="text-xs font-semibold text-white tracking-tight leading-snug group-hover:text-[#D97757] transition-colors truncate block"
                        >
                          {cleanName}
                        </h4>
                      </div>

                      {/* Bottom Footer Details */}
                      <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-[11px] text-neutral-500 font-mono w-full">
                        <span className="flex items-center gap-1 truncate">
                          <Clock className="w-3 h-3 text-neutral-600 flex-shrink-0" />
                          <span className="truncate">{file.converted_at || "Recent"}</span>
                        </span>
                        {file.public_hash && (
                          <span className="text-[10px] text-neutral-600 font-mono flex-shrink-0">
                            #{file.public_hash.slice(0, 6)}
                          </span>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}

        {/* ================= LEVEL 3: INSIDE "Server" FOLDER ================= */}
        {activeMainFolder === "flashfile" && activeSubFolder === "server" && (
          <motion.div
            key="server-view"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full flex flex-col gap-6"
          >
            {/* Top Navigation */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] w-full">
              <button
                onClick={() => setActiveSubFolder(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-neutral-200 text-xs font-medium border border-white/[0.08] transition-all cursor-pointer group"
              >
                <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                <span>Back to FlashFile</span>
              </button>

              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  Server Information
                </span>
                <span className="text-xs text-emerald-400 font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                  Operational
                </span>
              </div>
            </div>

            {/* Server Grid Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 w-full">
              {/* Card 1: Core Host & Architecture */}
              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-5 flex flex-col gap-4 shadow-[0_10px_25px_rgba(0,0,0,0.5)]">
                <div className="flex items-center gap-2 pb-2 border-b border-white/[0.06]">
                  <Cpu className="w-4 h-4 text-[#D97757]" />
                  <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-200">
                    Host & Compute Engine
                  </h3>
                </div>
                <div className="flex flex-col gap-2.5 text-xs">
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Processor Capacity</span>
                    <span className="font-mono text-white font-medium">16 vCPU Container</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Memory Allocation</span>
                    <span className="font-mono text-white font-medium">32 GB RAM</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Operating System</span>
                    <span className="font-mono text-white font-medium">Debian 12 Bookworm (Linux x86_64)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Python Runtime</span>
                    <span className="font-mono text-emerald-400 font-medium">Python 3.13 (AsyncIO)</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-neutral-400">Timezone</span>
                    <span className="font-mono text-white font-medium">Asia/Kolkata (UTC +5:30)</span>
                  </div>
                </div>
              </div>

              {/* Card 2: Microservice Mesh & Ports */}
              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-5 flex flex-col gap-4 shadow-[0_10px_25px_rgba(0,0,0,0.5)]">
                <div className="flex items-center gap-2 pb-2 border-b border-white/[0.06]">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-200">
                    Microservice Mesh
                  </h3>
                </div>
                <div className="flex flex-col gap-2.5 text-xs">
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">FastAPI Gateway</span>
                    <span className="font-mono text-emerald-400 font-medium">Port 8000 • Active</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">FileToLink Core</span>
                    <span className="font-mono text-emerald-400 font-medium">Port 8081 • Streaming</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Nginx Reverse Proxy</span>
                    <span className="font-mono text-white font-medium">Port 7860 • Edge Router</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Jellyfin Media Server</span>
                    <span className="font-mono text-emerald-400 font-medium">Port 8096 • Synchronized</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-neutral-400">Pyrogram Mesh</span>
                    <span className="font-mono text-emerald-400 font-medium">6 Worker Nodes Active</span>
                  </div>
                </div>
              </div>

              {/* Card 3: Storage & Network Volumes */}
              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-5 flex flex-col gap-4 shadow-[0_10px_25px_rgba(0,0,0,0.5)]">
                <div className="flex items-center gap-2 pb-2 border-b border-white/[0.06]">
                  <Database className="w-4 h-4 text-[#38BDF8]" />
                  <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-200">
                    Storage & Cloud Sync
                  </h3>
                </div>
                <div className="flex flex-col gap-2.5 text-xs">
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Persistent State</span>
                    <span className="font-mono text-white font-medium">/data (Durable NVMe Volume)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Remote Cloud Mirror</span>
                    <span className="font-mono text-white font-medium">gdrive:Antigravity (rclone)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Database Engine</span>
                    <span className="font-mono text-white font-medium">MongoDB Cluster (Async Motor)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Streaming Protocol</span>
                    <span className="font-mono text-[#38BDF8] font-medium">RFC 7233 Resumable Ranges</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-neutral-400">Telegram Bot Node</span>
                    <span className="font-mono text-[#D97757] font-medium">@flashfilezbot</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* ================= LEVEL 3: INSIDE "Analysis" FOLDER ================= */}
        {activeMainFolder === "flashfile" && activeSubFolder === "analysis" && (
          <motion.div
            key="analysis-view"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full flex flex-col gap-6"
          >
            {/* Top Navigation */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] w-full">
              <button
                onClick={() => setActiveSubFolder(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-neutral-200 text-xs font-medium border border-white/[0.08] transition-all cursor-pointer group"
              >
                <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                <span>Back to FlashFile</span>
              </button>

              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-[#38BDF8]" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  Bot Usage & Analytics
                </span>
                <span className="text-xs text-neutral-500 font-mono">
                  (Live Metrics)
                </span>
              </div>
            </div>

            {/* KPI Metric Counter Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full">
              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-4 flex flex-col gap-1">
                <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-wider">Total Files</span>
                <span className="text-2xl font-bold font-mono text-white">{totalConversionsCount > 0 ? totalConversionsCount : "140+"}</span>
                <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" /> +18% this week
                </span>
              </div>

              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-4 flex flex-col gap-1">
                <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-wider">Registered Users</span>
                <span className="text-2xl font-bold font-mono text-[#D97757]">{users.length}</span>
                <span className="text-[10px] text-neutral-400 font-mono">100% Verified Handles</span>
              </div>

              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-4 flex flex-col gap-1">
                <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-wider">Bandwidth Delivered</span>
                <span className="text-2xl font-bold font-mono text-[#38BDF8]">142.8 GB</span>
                <span className="text-[10px] text-neutral-400 font-mono">Resumable Chunk Streams</span>
              </div>

              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-4 flex flex-col gap-1">
                <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-wider">Avg File Size</span>
                <span className="text-2xl font-bold font-mono text-[#34D399]">1.42 GB</span>
                <span className="text-[10px] text-neutral-400 font-mono">Full HD & 4K HDR</span>
              </div>
            </div>

            {/* Charts Row: SVG Donut Chart + 7-Day Velocity Curve */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
              {/* Chart 1: Media Types Donut Chart */}
              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-5 flex flex-col gap-4 shadow-[0_10px_25px_rgba(0,0,0,0.5)]">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <PieChart className="w-4 h-4 text-[#D97757]" />
                    <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-200">
                      Media Format Ratio
                    </h3>
                  </div>
                  <span className="text-[11px] font-mono text-neutral-500">All Collections</span>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-around gap-6 py-2">
                  {/* SVG Donut */}
                  <div className="relative w-36 h-36 flex items-center justify-center flex-shrink-0">
                    <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                      {/* Movies: 64% -> stroke-dasharray 64, 36 */}
                      <circle
                        cx="50"
                        cy="50"
                        r="38"
                        fill="transparent"
                        stroke="#D97757"
                        strokeWidth="14"
                        strokeDasharray="152 238"
                        strokeDashoffset="0"
                        className="transition-all duration-500"
                      />
                      {/* TV Series: 28% -> stroke-dasharray 67, 171 */}
                      <circle
                        cx="50"
                        cy="50"
                        r="38"
                        fill="transparent"
                        stroke="#38BDF8"
                        strokeWidth="14"
                        strokeDasharray="67 238"
                        strokeDashoffset="-152"
                        className="transition-all duration-500"
                      />
                      {/* Audio / Others: 8% -> stroke-dasharray 19, 219 */}
                      <circle
                        cx="50"
                        cy="50"
                        r="38"
                        fill="transparent"
                        stroke="#34D399"
                        strokeWidth="14"
                        strokeDasharray="19 238"
                        strokeDashoffset="-219"
                        className="transition-all duration-500"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                      <span className="text-base font-bold font-mono text-white">100%</span>
                      <span className="text-[9px] font-mono uppercase text-neutral-500 tracking-wider">Indexed</span>
                    </div>
                  </div>

                  {/* Donut Legend */}
                  <div className="flex flex-col gap-3 text-xs w-full sm:w-auto">
                    <div className="flex items-center justify-between sm:justify-start gap-3">
                      <div className="flex items-center gap-2">
                        <span className="size-2.5 rounded-sm bg-[#D97757]" />
                        <span className="text-neutral-300">Feature Movies</span>
                      </div>
                      <span className="font-mono text-white font-semibold">64%</span>
                    </div>

                    <div className="flex items-center justify-between sm:justify-start gap-3">
                      <div className="flex items-center gap-2">
                        <span className="size-2.5 rounded-sm bg-[#38BDF8]" />
                        <span className="text-neutral-300">TV Series & Episodes</span>
                      </div>
                      <span className="font-mono text-white font-semibold">28%</span>
                    </div>

                    <div className="flex items-center justify-between sm:justify-start gap-3">
                      <div className="flex items-center gap-2">
                        <span className="size-2.5 rounded-sm bg-[#34D399]" />
                        <span className="text-neutral-300">Audio & Documents</span>
                      </div>
                      <span className="font-mono text-white font-semibold">8%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Chart 2: 7-Day Conversion Velocity Trend (SVG Line & Area) */}
              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-5 flex flex-col gap-4 shadow-[0_10px_25px_rgba(0,0,0,0.5)]">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-200">
                      7-Day Conversion Velocity
                    </h3>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-400">Peak: 63 Files</span>
                </div>

                {/* SVG Area Chart */}
                <div className="w-full h-36 relative flex flex-col justify-end">
                  <svg className="w-full h-28 overflow-visible" viewBox="0 0 350 100" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#D97757" stopOpacity="0.3" />
                        <stop offset="100%" stopColor="#D97757" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>
                    {/* Area fill */}
                    <path
                      d="M 10 75 Q 60 65 110 50 T 210 40 T 290 20 L 340 10 L 340 100 L 10 100 Z"
                      fill="url(#areaGradient)"
                    />
                    {/* Line curve */}
                    <path
                      d="M 10 75 Q 60 65 110 50 T 210 40 T 290 20 L 340 10"
                      fill="transparent"
                      stroke="#D97757"
                      strokeWidth="2.5"
                    />
                    {/* Points */}
                    {[
                      { cx: 10, cy: 75 },
                      { cx: 65, cy: 62 },
                      { cx: 120, cy: 50 },
                      { cx: 175, cy: 45 },
                      { cx: 230, cy: 38 },
                      { cx: 285, cy: 22 },
                      { cx: 340, cy: 10 },
                    ].map((pt, i) => (
                      <circle key={i} cx={pt.cx} cy={pt.cy} r="3.5" fill="#FFFFFF" stroke="#D97757" strokeWidth="2" />
                    ))}
                  </svg>
                  {/* Days Labels */}
                  <div className="flex justify-between text-[10px] font-mono text-neutral-500 pt-2 border-t border-white/[0.04]">
                    <span>Mon (18)</span>
                    <span>Tue (24)</span>
                    <span>Wed (31)</span>
                    <span>Thu (29)</span>
                    <span>Fri (42)</span>
                    <span>Sat (56)</span>
                    <span className="text-emerald-400 font-semibold">Sun (63)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Quality & Resolution Breakdown Progress Meters */}
            <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-5 flex flex-col gap-4">
              <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-200">
                Resolution & Encode Distribution
              </h3>
              <div className="flex flex-col gap-3">
                <div className="flex flex-col gap-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-neutral-300">1080p FHD (HEVC / x265)</span>
                    <span className="text-white font-medium">54%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-neutral-900 overflow-hidden">
                    <div className="h-full rounded-full bg-[#D97757]" style={{ width: "54%" }} />
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-neutral-300">4K UHD / HDR10+ / Dolby Vision</span>
                    <span className="text-white font-medium">28%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-neutral-900 overflow-hidden">
                    <div className="h-full rounded-full bg-[#38BDF8]" style={{ width: "28%" }} />
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-neutral-300">720p HD Mobile Optimized</span>
                    <span className="text-white font-medium">18%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-neutral-900 overflow-hidden">
                    <div className="h-full rounded-full bg-[#34D399]" style={{ width: "18%" }} />
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* ================= LEVEL 3: INSIDE "Admin" FOLDER ================= */}
        {activeMainFolder === "flashfile" && activeSubFolder === "admin" && (
          <motion.div
            key="admin-view"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full flex flex-col gap-6"
          >
            {/* Top Navigation */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] w-full">
              <button
                onClick={() => setActiveSubFolder(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-neutral-200 text-xs font-medium border border-white/[0.08] transition-all cursor-pointer group"
              >
                <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                <span>Back to FlashFile</span>
              </button>

              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#D97757]" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  Administrator Profile
                </span>
                <span className="text-xs text-neutral-500 font-mono">
                  (Root Authority)
                </span>
              </div>
            </div>

            {/* Admin Profile & Authority Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
              {/* Profile Card */}
              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-5 flex flex-col gap-4 shadow-[0_10px_25px_rgba(0,0,0,0.5)]">
                <div className="flex items-center gap-3 pb-3 border-b border-white/[0.06]">
                  <div className="size-10 rounded-full bg-[#D97757]/20 border border-[#D97757]/40 flex items-center justify-center text-[#D97757] font-bold font-mono">
                    JP
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight">
                      Jishnu P G
                    </h3>
                    <p className="text-[11px] font-mono text-neutral-400">
                      System Architect & Bot Owner
                    </p>
                  </div>
                </div>

                <div className="flex flex-col gap-3 text-xs">
                  <div className="flex items-center justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400 flex items-center gap-2">
                      <Terminal className="w-3.5 h-3.5 text-neutral-500" /> Telegram Handle
                    </span>
                    <a
                      href="https://t.me/Jishnuxpg"
                      target="_blank"
                      rel="noreferrer"
                      className="font-mono text-[#D97757] hover:underline flex items-center gap-1"
                    >
                      @Jishnuxpg <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="flex items-center justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400 flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-neutral-500" /> Contact Email
                    </span>
                    <a
                      href="mailto:jishnupg2005@gmail.com"
                      className="font-mono text-white hover:text-[#D97757] transition-colors"
                    >
                      jishnupg2005@gmail.com
                    </a>
                  </div>

                  <div className="flex items-center justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400 flex items-center gap-2">
                      <GitBranch className="w-3.5 h-3.5 text-neutral-500" /> GitHub Repository
                    </span>
                    <a
                      href="https://github.com/JishnuPG-tech/FiletoLink"
                      target="_blank"
                      rel="noreferrer"
                      className="font-mono text-neutral-300 hover:text-white hover:underline flex items-center gap-1"
                    >
                      JishnuPG-tech/FiletoLink <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="flex items-center justify-between py-1">
                    <span className="text-neutral-400 flex items-center gap-2">
                      <Globe className="w-3.5 h-3.5 text-neutral-500" /> Hugging Face Space
                    </span>
                    <a
                      href="https://huggingface.co/spaces/Jishnupg/FileToLink"
                      target="_blank"
                      rel="noreferrer"
                      className="font-mono text-neutral-300 hover:text-white hover:underline flex items-center gap-1"
                    >
                      jishnupg/FileToLink <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>

              {/* Security & Access Authority Card */}
              <div className="rounded-2xl bg-[#09090b] border border-white/[0.08] p-5 flex flex-col gap-4 shadow-[0_10px_25px_rgba(0,0,0,0.5)]">
                <div className="flex items-center gap-2 pb-3 border-b border-white/[0.06]">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-neutral-200">
                    Security & Authorization Matrix
                  </h3>
                </div>

                <div className="flex flex-col gap-3 text-xs">
                  <div className="flex items-center justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Root Access ID</span>
                    <span className="font-mono text-white font-medium">1769298522 (Primary Owner)</span>
                  </div>

                  <div className="flex items-center justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Target Channel</span>
                    <span className="font-mono text-white font-medium">-1003931672617 (BIN_CHANNEL)</span>
                  </div>

                  <div className="flex items-center justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Session Verification</span>
                    <span className="font-mono text-emerald-400 font-medium">SHA-256 HMAC Active</span>
                  </div>

                  <div className="flex items-center justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Anti-Flood Protection</span>
                    <span className="font-mono text-white font-medium">50ms Token Bucket Rate-Limit</span>
                  </div>

                  <div className="flex items-center justify-between py-1">
                    <span className="text-neutral-400">CRLF Injection Shield</span>
                    <span className="font-mono text-emerald-400 font-medium">RFC 6266 Strict Quoting</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* ================= STATIC FOLDER CONTENT VIEW ================= */}
        {activeStaticFolder && (
          <motion.div
            key={`static-${activeStaticFolder.id}`}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full flex flex-col gap-6"
          >
            {/* Top Navigation */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] w-full">
              <button
                onClick={() => setActiveStaticFolder(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-neutral-200 text-xs font-medium border border-white/[0.08] transition-all cursor-pointer group"
              >
                <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                <span>Back</span>
              </button>

              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-[#D97757]" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  {activeStaticFolder.title}
                </span>
                <span className="text-xs text-neutral-500 font-mono">
                  ({activeStaticFolder.items.length})
                </span>
              </div>
            </div>

            {/* Static Items Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 w-full">
              {activeStaticFolder.items.map((item, index) => {
                const imgUrl = typeof item.image === "object" ? item.image.src : item.image;
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    className="group rounded-2xl bg-[#09090b] border border-white/[0.08] hover:border-white/[0.18] p-3 flex flex-col gap-3 shadow-[0_12px_30px_rgba(0,0,0,0.6)] transition-all duration-300 hover:shadow-[0_16px_40px_rgba(217,119,87,0.12)]"
                  >
                    {imgUrl && (
                      <div className="w-full aspect-[4/3] rounded-xl overflow-hidden bg-neutral-900 relative">
                        <img
                          src={imgUrl}
                          alt={item.title || "Card"}
                          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                          loading="lazy"
                        />
                      </div>
                    )}
                    <div className="flex flex-col gap-1 p-1">
                      <h4 className="text-xs font-semibold text-white tracking-tight group-hover:text-[#D97757] transition-colors">
                        {item.title}
                      </h4>
                      {item.meta && (
                        <p className="text-[11px] text-neutral-400 line-clamp-1 font-mono">
                          {item.meta}
                        </p>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default CaseStudiesPage;
