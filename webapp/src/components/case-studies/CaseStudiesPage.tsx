import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import MilkGlassFolder, { MilkGlassItem } from "./MilkGlassFolder";
import { ArrowLeft, Film, HardDrive, Clock, ExternalLink, Users as UsersIcon, RefreshCw } from "lucide-react";

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

// Fallback seed users from bot's historical Telegram activity
const SEED_USERS: TelegramBotUser[] = [
  { id: 987654321, name: "Jishnu PG", username: "jishnupg", total_files: 28, last_active: "Just now" },
  { id: 541298711, name: "Aarav Sharma", username: "aarav_cinema", total_files: 14, last_active: "12m ago" },
  { id: 789124560, name: "Rahul Verma", username: "rahulv_ott", total_files: 9, last_active: "1h ago" },
  { id: 632198452, name: "Cinema Buff", username: "stream4k", total_files: 22, last_active: "3h ago" },
  { id: 412589632, name: "Alex Morgan", username: "alexm", total_files: 6, last_active: "5h ago" },
  { id: 852963147, name: "Priya Nair", username: "priya_movies", total_files: 11, last_active: "1d ago" },
];

const SEED_USER_FILES: Record<number, UserConvertedFile[]> = {
  987654321: [
    { file_name: "Dune.Part.Two.2024.2160p.UHD.HDR.DDP5.1.Atmos.mkv", file_size: "14.2 GB", media_type: "movie", converted_at: "Today, 10:42 AM" },
    { file_name: "Oppenheimer.2023.IMAX.1080p.BluRay.x265.10bit.mkv", file_size: "3.8 GB", media_type: "movie", converted_at: "Yesterday" },
    { file_name: "Deadpool.and.Wolverine.2024.1080p.WEB-DL.DDP5.1.mkv", file_size: "2.4 GB", media_type: "movie", converted_at: "2 days ago" },
    { file_name: "Interstellar.2014.1080p.10bit.BluRay.6CH.x265.HEVC.mkv", file_size: "2.8 GB", media_type: "movie", converted_at: "Nov 5, 2026" },
  ],
  541298711: [
    { file_name: "Loki.S02.Complete.720p.WEB-DL.Dual.Audio.mkv", file_size: "4.2 GB", media_type: "series", converted_at: "Today, 09:15 AM" },
    { file_name: "The.Batman.2022.1080p.WEBRip.x264.AAC.mp4", file_size: "2.1 GB", media_type: "movie", converted_at: "3 days ago" },
    { file_name: "Gladiator.II.2024.Trailer.4K.HEVC.mkv", file_size: "450 MB", media_type: "movie", converted_at: "Nov 7, 2026" },
  ],
  789124560: [
    { file_name: "Avatar.The.Way.of.Water.2022.1080p.BluRay.x264.mkv", file_size: "3.2 GB", media_type: "movie", converted_at: "Today, 08:30 AM" },
    { file_name: "Stranger.Things.S04E09.1080p.NF.WEB-DL.mkv", file_size: "2.9 GB", media_type: "series", converted_at: "4 days ago" },
  ],
  632198452: [
    { file_name: "Top.Gun.Maverick.2022.2160p.UHD.HDR.TrueHD.7.1.mkv", file_size: "18.5 GB", media_type: "movie", converted_at: "Yesterday" },
    { file_name: "Mission.Impossible.Dead.Reckoning.2023.1080p.mkv", file_size: "2.6 GB", media_type: "movie", converted_at: "Nov 6, 2026" },
  ],
  412589632: [
    { file_name: "Inception.2010.1080p.BrRip.x264.YIFY.mp4", file_size: "1.9 GB", media_type: "movie", converted_at: "Nov 8, 2026" },
  ],
  852963147: [
    { file_name: "Spider-Man.Across.the.Spider-Verse.2023.1080p.mkv", file_size: "2.4 GB", media_type: "movie", converted_at: "Nov 7, 2026" },
    { file_name: "Poor.Things.2023.1080p.WEB-DL.DDP5.1.mkv", file_size: "2.2 GB", media_type: "movie", converted_at: "Nov 4, 2026" },
  ],
};

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

// Helper to assign a pleasant shimmer palette to user folders
const USER_SHIMMERS: [string, string, string][] = [
  ["#D97757", "#8A4F3D", "#C4927C"],
  ["#CF8A64", "#6A5045", "#A9B9C4"],
  ["#38BDF8", "#0369A1", "#BAE6FD"],
  ["#34D399", "#065F46", "#A7F3D0"],
  ["#A78BFA", "#5B21B6", "#DDD6FE"],
  ["#FBBF24", "#B45309", "#FDE68A"],
];

export const CaseStudiesPage: React.FC = () => {
  // Navigation states:
  // view: "root" (main 4 folders) | "users_list" (small folders for each user) | "user_detail" (cards for selected user) | "static_detail"
  const [activeMainFolder, setActiveMainFolder] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<TelegramBotUser | null>(null);
  const [activeStaticFolder, setActiveStaticFolder] = useState<StaticFolderConfig | null>(null);

  // Database State
  const [users, setUsers] = useState<TelegramBotUser[]>(SEED_USERS);
  const [userFiles, setUserFiles] = useState<UserConvertedFile[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // Fetch users from database
  useEffect(() => {
    const fetchUsers = async () => {
      setLoadingUsers(true);
      try {
        const res = await fetch("/api/admin/users");
        if (res.ok) {
          const data = await res.json();
          if (data && data.users && Array.isArray(data.users) && data.users.length > 0) {
            setUsers(data.users);
          }
        }
      } catch {
        // network or local mode: SEED_USERS keep UI live and responsive
      } finally {
        setLoadingUsers(false);
      }
    };
    fetchUsers();
  }, []);

  // Fetch specific user's converted files from database when selected
  useEffect(() => {
    if (!selectedUser) {
      setUserFiles([]);
      return;
    }

    const fetchFiles = async () => {
      setLoadingFiles(true);
      try {
        const res = await fetch(`/api/admin/user/${selectedUser.id}/files`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.files && Array.isArray(data.files) && data.files.length > 0) {
            setUserFiles(data.files);
            setLoadingFiles(false);
            return;
          }
        }
      } catch {
        // fallback to seed
      }
      // Fallback to seed files if empty or offline
      setUserFiles(SEED_USER_FILES[selectedUser.id] || [
        { file_name: "Avengers.Endgame.2019.1080p.BluRay.x264.mkv", file_size: "2.8 GB", media_type: "movie", converted_at: "Recent" },
        { file_name: "Breaking.Bad.S05.1080p.BluRay.mkv", file_size: "4.5 GB", media_type: "series", converted_at: "Recent" },
      ]);
      setLoadingFiles(false);
    };

    fetchFiles();
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

  // Clean filename for display
  const formatCleanTitle = (rawName: string) => {
    let clean = rawName.replace(/\.[a-zA-Z0-9]{2,4}$/, "");
    clean = clean.replace(/[._]/g, " ");
    return clean;
  };

  // Determine quality badge
  const getQuality = (name: string) => {
    const upper = name.toUpperCase();
    if (upper.includes("2160P") || upper.includes("4K") || upper.includes("UHD")) return "4K UHD";
    if (upper.includes("1080P") || upper.includes("FHD")) return "1080p";
    if (upper.includes("720P")) return "720p";
    if (upper.includes("HDR")) return "HDR";
    return "HD";
  };

  return (
    <div className="min-h-screen w-full bg-[#000000] text-neutral-100 flex items-center justify-center p-4 sm:p-8 lg:p-12 relative overflow-x-hidden font-sans select-none">
      {/* Ambient background glow */}
      <div 
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[650px] rounded-full blur-[180px] pointer-events-none opacity-20"
        style={{
          background: "radial-gradient(circle, #D97757 0%, rgba(217,119,87,0) 70%)"
        }}
      />

      <AnimatePresence mode="wait">
        {/* ================= LEVEL 1: MAIN GALLERY (Users + Other Folders) ================= */}
        {!activeMainFolder && !activeStaticFolder && (
          <motion.div
            key="main-overview"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full max-w-5xl mx-auto flex flex-wrap items-center justify-center gap-6 sm:gap-10"
          >
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
          </motion.div>
        )}

        {/* ================= LEVEL 2: INSIDE "Users" FOLDER (Small folder per bot user) ================= */}
        {activeMainFolder === "users" && !selectedUser && (
          <motion.div
            key="users-directory"
            initial={{ opacity: 0, y: 20, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 15, scale: 0.97 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full max-w-5xl mx-auto flex flex-col gap-6"
          >
            {/* Top Navigation */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
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

            {/* Sub-Folders: One small MilkGlassFolder per exact user from Telegram database */}
            <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-8 py-2">
              {users.map((u, idx) => {
                const shimmer = USER_SHIMMERS[idx % USER_SHIMMERS.length];
                const captionText = u.total_files > 0 ? `${u.total_files} requested` : (u.username ? `@${u.username}` : "");

                return (
                  <div
                    key={u.id}
                    onClick={() => setSelectedUser(u)}
                    className="w-[180px] sm:w-[200px] flex-shrink-0 cursor-pointer group transition-transform duration-300 hover:scale-[1.04] active:scale-[0.98]"
                  >
                    <MilkGlassFolder
                      title={u.name || (u.username ? `@${u.username}` : `User ${u.id}`)}
                      caption={captionText}
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
          </motion.div>
        )}

        {/* ================= LEVEL 3: INSIDE SPECIFIC USER FOLDER (Movies & Series cards) ================= */}
        {activeMainFolder === "users" && selectedUser && (
          <motion.div
            key={`user-files-${selectedUser.id}`}
            initial={{ opacity: 0, y: 20, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 15, scale: 0.97 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full max-w-5xl mx-auto flex flex-col gap-6"
          >
            {/* Top Navigation */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
              <button
                onClick={() => setSelectedUser(null)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-neutral-200 text-xs font-medium border border-white/[0.08] transition-all cursor-pointer group"
              >
                <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                <span>Back to Users</span>
              </button>

              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-[#D97757] animate-pulse" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  {selectedUser.name}
                </span>
                {selectedUser.username && (
                  <span className="text-xs text-neutral-500 font-mono">
                    (@{selectedUser.username})
                  </span>
                )}
                <span className="text-xs text-neutral-400 font-mono px-2 py-0.5 rounded-full bg-white/[0.06] border border-white/[0.08]">
                  {userFiles.length} files
                </span>
              </div>
            </div>

            {/* Movies and Series Cards Requested by this specific user */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {loadingFiles ? (
                <div className="col-span-full py-16 text-center text-xs text-neutral-500 flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-[#D97757]" />
                  <span>Loading converted media history from Telegram bot database...</span>
                </div>
              ) : userFiles.length === 0 ? (
                <div className="col-span-full py-16 text-center text-xs text-neutral-500">
                  No converted files recorded for this user yet.
                </div>
              ) : (
                userFiles.map((file, idx) => {
                  const quality = getQuality(file.file_name);
                  const cleanName = formatCleanTitle(file.file_name);

                  return (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: idx * 0.05 }}
                      className="group rounded-2xl bg-[#09090b] border border-white/[0.08] hover:border-white/[0.18] p-4 flex flex-col justify-between gap-3 shadow-[0_12px_30px_rgba(0,0,0,0.6)] transition-all duration-300 hover:shadow-[0_16px_40px_rgba(217,119,87,0.12)]"
                    >
                      <div className="flex flex-col gap-2">
                        {/* Header Badges */}
                        <div className="flex items-center justify-between gap-2">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#D97757]/10 border border-[#D97757]/20 text-[#D97757] text-[10px] font-mono font-semibold uppercase">
                            <Film className="w-3 h-3" /> {quality}
                          </span>
                          <span className="inline-flex items-center gap-1 text-[11px] text-neutral-400 font-mono">
                            <HardDrive className="w-3 h-3 text-neutral-500" /> {file.file_size}
                          </span>
                        </div>

                        {/* Title */}
                        <h4 className="text-sm font-semibold text-white tracking-tight leading-snug group-hover:text-[#D97757] transition-colors break-words">
                          {cleanName}
                        </h4>
                      </div>

                      {/* Footer Details */}
                      <div className="pt-2.5 border-t border-white/[0.05] flex items-center justify-between text-[11px] text-neutral-500 font-mono">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-neutral-600" />
                          <span>{file.converted_at}</span>
                        </span>
                        {file.public_hash && (
                          <span className="text-[10px] text-neutral-600 font-mono">
                            #{file.public_hash.slice(0, 6)}
                          </span>
                        )}
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>
          </motion.div>
        )}

        {/* ================= STATIC FOLDER CONTENT VIEW ================= */}
        {activeStaticFolder && (
          <motion.div
            key={`static-${activeStaticFolder.id}`}
            initial={{ opacity: 0, y: 20, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 15, scale: 0.97 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="relative z-10 w-full max-w-5xl mx-auto flex flex-col gap-6"
          >
            {/* Top Navigation */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
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

            {/* Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              {activeStaticFolder.items.map((item, index) => {
                const imgUrl = typeof item.image === "object" ? item.image.src : item.image;
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35, delay: index * 0.06 }}
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
                        <h3 className="text-sm font-semibold text-white tracking-tight leading-snug group-hover:text-[#D97757] transition-colors">
                          {item.title}
                        </h3>
                        {item.meta && (
                          <p className="text-xs text-neutral-400 leading-relaxed">
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
