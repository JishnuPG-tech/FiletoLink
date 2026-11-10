import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import MilkGlassFolder, { MilkGlassItem } from "./MilkGlassFolder";
import { ArrowLeft, Film, HardDrive, Clock, ExternalLink, Users as UsersIcon, RefreshCw, Radio } from "lucide-react";

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

export const CaseStudiesPage: React.FC = () => {
  const [activeMainFolder, setActiveMainFolder] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<TelegramBotUser | null>(null);
  const [activeStaticFolder, setActiveStaticFolder] = useState<StaticFolderConfig | null>(null);

  // Live Database States
  const [users, setUsers] = useState<TelegramBotUser[]>([]);
  const [userFiles, setUserFiles] = useState<UserConvertedFile[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [isLiveConnected, setIsLiveConnected] = useState(false);

  // Real-time automatic polling for new users from MongoDB / Telegram
  useEffect(() => {
    let isMounted = true;

    const fetchLiveUsers = async () => {
      try {
        const res = await fetch("/api/admin/users");
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data && Array.isArray(data.users)) {
            setUsers(data.users);
            setIsLiveConnected(true);
          }
        }
      } catch (err) {
        console.debug("Live sync polling...", err);
      } finally {
        if (isMounted) setLoadingUsers(false);
      }
    };

    fetchLiveUsers();
    // Auto-poll every 3.5 seconds to detect new users immediately
    const userInterval = setInterval(fetchLiveUsers, 3500);

    return () => {
      isMounted = false;
      clearInterval(userInterval);
    };
  }, []);

  // Real-time automatic polling for the selected user's files as they are converted
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
    // Fast 2.5s poll while viewing a user's folder to stream new conversions instantly
    const fileInterval = setInterval(fetchLiveUserFiles, 2500);

    return () => {
      isMounted = false;
      clearInterval(fileInterval);
    };
  }, [selectedUser]);

  // Keyboard navigation: Escape key goes back one step
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (selectedUser) {
          setSelectedUser(null);
        } else if (activeMainFolder) {
          setActiveMainFolder(null);
        } else if (activeStaticFolder) {
          setActiveStaticFolder(null);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedUser, activeMainFolder, activeStaticFolder]);

  // Clean filename: trim extensions, replace periods/underscores with clean spaces
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
            {/* Top Left Branding */}
            <div className="pb-3 flex items-center justify-start">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white font-sans">
                Apex
              </h1>
            </div>

            {/* Linear Row-wise Folders aligned left to right */}
            <div className="flex flex-wrap items-start justify-start gap-6 sm:gap-8 w-full">
              {/* 1st Folder: "Users" with ZERO subtitle text */}
              <div
                onClick={() => setActiveMainFolder("users")}
                className="w-[200px] sm:w-[220px] flex-shrink-0 cursor-pointer group transition-transform duration-300 hover:scale-[1.03] active:scale-[0.98]"
              >
                <MilkGlassFolder
                  title="Users"
                  caption=""
                  items={[
                    { type: "image", title: "Active Bot Users", meta: "Telegram Community" },
                    { type: "image", title: "Live Conversions", meta: "Realtime Database" },
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

        {/* ================= LEVEL 2: INSIDE "Users" FOLDER (Linear left-to-right) ================= */}
        {activeMainFolder === "users" && !selectedUser && (
          <motion.div
            key="users-directory"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full flex flex-col gap-6"
          >
            {/* Top Navigation */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] w-full">
              <button
                onClick={() => setActiveMainFolder(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-neutral-200 text-xs font-medium border border-white/[0.08] transition-all cursor-pointer group"
              >
                <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                <span>Back</span>
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

            {/* Sub-Folders: One small MilkGlassFolder per user from Telegram database, aligned LEFT TO RIGHT */}
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

        {/* ================= LEVEL 3: INSIDE SPECIFIC USER FOLDER (Equal-size cards, truncated with ...) ================= */}
        {activeMainFolder === "users" && selectedUser && (
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
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-80" />
                        <span className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-md border border-white/[0.1] text-[10px] font-mono text-neutral-300">
                          0{index + 1}
                        </span>
                      </div>
                    )}

                    <div className="flex flex-col flex-1 justify-between gap-2">
                      <div className="flex flex-col gap-1">
                        <h3 className="text-sm font-semibold text-white tracking-tight leading-snug group-hover:text-[#D97757] transition-colors truncate">
                          {item.title}
                        </h3>
                        {item.meta && (
                          <p className="text-xs text-neutral-400 truncate">
                            {item.meta}
                          </p>
                        )}
                      </div>

                      {item.byline && (
                        <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-[11px] text-neutral-500 font-mono">
                          <span className="truncate">{item.byline}</span>
                          {item.link && (
                            <a
                              href={item.link}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#D97757] hover:text-[#e89073] flex-shrink-0"
                            >
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
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
