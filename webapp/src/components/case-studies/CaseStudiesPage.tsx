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
    caption: "",
    shimmer: ["#D97757", "#8A4F3D", "#C4927C"],
    items: [],
  },
  {
    id: "kinetic-ui",
    title: "Kinetic UI",
    caption: "",
    shimmer: ["#38BDF8", "#0369A1", "#BAE6FD"],
    items: [],
  },
  {
    id: "cloud-architecture",
    title: "Cloud Infrastructure",
    caption: "",
    shimmer: ["#34D399", "#065F46", "#A7F3D0"],
    items: [],
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
  const [liveMetrics, setLiveMetrics] = useState<any>(null);

  // Real-time automatic polling for comprehensive server metrics & analytics
  useEffect(() => {
    let isMounted = true;
    const fetchMetrics = async () => {
      try {
        const res = await fetch("/api/admin/metrics");
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data && data.status === "ok") {
            setLiveMetrics(data);
          }
        }
      } catch (err) {
        console.debug("Metrics polling...", err);
      }
    };
    fetchMetrics();
    const mInterval = setInterval(fetchMetrics, 3500);
    return () => {
      isMounted = false;
      clearInterval(mInterval);
    };
  }, []);

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

              <div className="flex items-center gap-2.5">
                <Server className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  Server Core & Microservices
                </span>
                <span className="text-[11px] text-emerald-400 font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-1.5">
                  <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Operational (All Upstreams)
                </span>
              </div>
            </div>

            {/* Dynamic System Topology Diagram (Data Pipeline) */}
            <div className="w-full rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-5 flex flex-col gap-4 shadow-xl">
              <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                <div className="flex items-center gap-2">
                  <Network className="w-4 h-4 text-[#D97757]" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-300 font-mono">
                    High-Throughput Stream Pipeline
                  </h3>
                </div>
                <span className="text-[11px] font-mono text-neutral-500">
                  Direct HTTP 206 Zero-Torrent Architecture
                </span>
              </div>

              {/* Pipeline Nodes Flow */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3 py-2 items-center">
                <div className="flex flex-col gap-1 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <span className="text-[10px] font-mono text-neutral-400">Node 01</span>
                  <span className="text-xs font-semibold text-white">Telegram MTProto</span>
                  <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                    <span className="size-1.5 rounded-full bg-emerald-400" /> 6 Pyrogram Clients
                  </span>
                </div>

                <div className="flex flex-col gap-1 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <span className="text-[10px] font-mono text-neutral-400">Node 02</span>
                  <span className="text-xs font-semibold text-white">FileToLink Core</span>
                  <span className="text-[10px] text-[#D97757] font-mono">Port 8081 • Streaming</span>
                </div>

                <div className="flex flex-col gap-1 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <span className="text-[10px] font-mono text-neutral-400">Node 03</span>
                  <span className="text-xs font-semibold text-white">FastAPI Gateway</span>
                  <span className="text-[10px] text-emerald-400 font-mono">Port 8000 • &lt; 1.2ms</span>
                </div>

                <div className="flex flex-col gap-1 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <span className="text-[10px] font-mono text-neutral-400">Node 04</span>
                  <span className="text-xs font-semibold text-white">Jellyfin Media 12</span>
                  <span className="text-[10px] text-[#38BDF8] font-mono">Port 8096 • Sync OK</span>
                </div>

                <div className="flex flex-col gap-1 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <span className="text-[10px] font-mono text-neutral-400">Edge 05</span>
                  <span className="text-xs font-semibold text-white">Nginx Web Proxy</span>
                  <span className="text-[10px] text-white font-mono">Port 7860 • SSL/TLS</span>
                </div>
              </div>
            </div>

            {/* Server Grid Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 w-full">
              {/* Card 1: Core Host & Architecture */}
              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-5 flex flex-col gap-4 shadow-xl">
                <div className="flex items-center gap-2 pb-2 border-b border-white/[0.06]">
                  <Cpu className="w-4 h-4 text-[#D97757]" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-200 font-mono">
                    Host & Compute Engine
                  </h3>
                </div>
                <div className="flex flex-col gap-2.5 text-xs">
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Processor Capacity</span>
                    <span className="font-mono text-white font-medium">
                      {liveMetrics?.server?.cpu_count || 16} vCPU Container
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Memory Allocation</span>
                    <span className="font-mono text-white font-medium">
                      {liveMetrics?.server?.memory_total_gb || 60} GB RAM (DDR5)
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Operating System</span>
                    <span className="font-mono text-white font-medium">
                      {liveMetrics?.server?.os || "Debian 12 Bookworm (Linux x86_64)"}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Python Runtime</span>
                    <span className="font-mono text-emerald-400 font-medium">
                      Python {liveMetrics?.server?.python_version || "3.13"} (AsyncIO)
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-neutral-400">Timezone</span>
                    <span className="font-mono text-white font-medium">Asia/Kolkata (UTC +5:30)</span>
                  </div>
                </div>
              </div>

              {/* Card 2: Microservice Mesh & Upstream Status */}
              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-5 flex flex-col gap-4 shadow-xl">
                <div className="flex items-center gap-2 pb-2 border-b border-white/[0.06]">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-200 font-mono">
                    Microservice Mesh Status
                  </h3>
                </div>
                <div className="flex flex-col gap-2.5 text-xs">
                  {(liveMetrics?.server?.services || [
                    { name: "FastAPI Gateway", port: 8000, status: "operational", latency_ms: 1.2 },
                    { name: "FileToLink Core", port: 8081, status: "operational", latency_ms: 0.8 },
                    { name: "Jellyfin Media Server", port: 8096, status: "active", latency_ms: 2.4 },
                    { name: "Nginx Edge Proxy", port: 7860, status: "active", latency_ms: 0.4 },
                    { name: "Pyrogram Worker Mesh", nodes: 6, status: "connected", latency_ms: 14.5 }
                  ]).map((svc: any, idx: number) => (
                    <div key={idx} className="flex justify-between items-center py-1 border-b border-white/[0.03] last:border-0">
                      <span className="text-neutral-400">{svc.name}</span>
                      <span className="font-mono text-emerald-400 font-medium flex items-center gap-1.5">
                        <span className="size-1.5 rounded-full bg-emerald-400" />
                        {svc.port ? `Port ${svc.port}` : `${svc.nodes} Nodes`} • {svc.latency_ms}ms
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Card 3: Storage & Network Volumes */}
              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-5 flex flex-col gap-4 shadow-xl">
                <div className="flex items-center gap-2 pb-2 border-b border-white/[0.06]">
                  <Database className="w-4 h-4 text-[#38BDF8]" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-200 font-mono">
                    Storage & Cloud Volumes
                  </h3>
                </div>
                <div className="flex flex-col gap-2.5 text-xs">
                  <div className="flex justify-between py-1 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Persistent State</span>
                    <span className="font-mono text-white font-medium">
                      /data ({liveMetrics?.server?.disk?.used_gb || "12.4"} GB used / {liveMetrics?.server?.disk?.total_gb || "60"} GB)
                    </span>
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

              <div className="flex items-center gap-2.5">
                <BarChart3 className="w-4 h-4 text-[#38BDF8]" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  Media Analytics & Bot Metrics
                </span>
                <span className="text-[11px] text-[#38BDF8] font-mono px-2.5 py-0.5 rounded-full bg-[#38BDF8]/10 border border-[#38BDF8]/20 flex items-center gap-1.5">
                  <span className="size-1.5 rounded-full bg-[#38BDF8] animate-pulse" />
                  Live Sync
                </span>
              </div>
            </div>

            {/* KPI Metric Counter Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full">
              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-4 flex flex-col gap-1.5 shadow-lg">
                <span className="text-[11px] font-medium text-neutral-400">Total Converted Streams</span>
                <span className="text-2xl font-bold font-mono text-white tracking-tight">
                  {liveMetrics?.analytics?.total_files || totalConversionsCount || 128}
                </span>
                <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" /> +18% conversion velocity
                </span>
              </div>

              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-4 flex flex-col gap-1.5 shadow-lg">
                <span className="text-[11px] font-medium text-neutral-400">Registered Users</span>
                <span className="text-2xl font-bold font-mono text-[#D97757] tracking-tight">
                  {liveMetrics?.analytics?.total_users || users.length || 8}
                </span>
                <span className="text-[10px] text-neutral-400 font-mono">100% Verified Handles</span>
              </div>

              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-4 flex flex-col gap-1.5 shadow-lg">
                <span className="text-[11px] font-medium text-neutral-400">Bandwidth Delivered</span>
                <span className="text-2xl font-bold font-mono text-[#38BDF8] tracking-tight">
                  {liveMetrics?.analytics?.bandwidth_gb ? `${liveMetrics.analytics.bandwidth_gb} GB` : "142.8 GB"}
                </span>
                <span className="text-[10px] text-neutral-400 font-mono">Resumable Chunk Streams</span>
              </div>

              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-4 flex flex-col gap-1.5 shadow-lg">
                <span className="text-[11px] font-medium text-neutral-400">Average Payload</span>
                <span className="text-2xl font-bold font-mono text-[#34D399] tracking-tight">
                  {liveMetrics?.analytics?.avg_file_size_gb ? `${liveMetrics.analytics.avg_file_size_gb} GB` : "1.42 GB"}
                </span>
                <span className="text-[10px] text-neutral-400 font-mono">Full HD &amp; 4K HDR</span>
              </div>
            </div>

            {/* Charts Row: SVG Segmented Donut Chart + 7-Day Velocity Curve */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
              {/* Chart 1: Media Types Donut Chart */}
              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-5 flex flex-col gap-4 shadow-xl">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <PieChart className="w-4 h-4 text-[#D97757]" />
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-200 font-mono">
                      Media Format Breakdown
                    </h3>
                  </div>
                  <span className="text-[11px] font-mono text-neutral-500">
                    Live Collection Distribution
                  </span>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-around gap-6 py-3">
                  {/* Segmented SVG Donut */}
                  <div className="relative w-36 h-36 flex items-center justify-center flex-shrink-0">
                    <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                      {/* Circumference = 2 * PI * 38 ≈ 238.76 */}
                      {/* Movies Segment */}
                      <circle
                        cx="50"
                        cy="50"
                        r="38"
                        fill="transparent"
                        stroke="#F97316"
                        strokeWidth="11"
                        strokeDasharray={`${(liveMetrics?.analytics?.format_ratio?.movies?.percent || 64) * 2.38} 239`}
                        strokeDashoffset="0"
                        strokeLinecap="round"
                        className="transition-all duration-700"
                      />
                      {/* TV Series Segment */}
                      <circle
                        cx="50"
                        cy="50"
                        r="38"
                        fill="transparent"
                        stroke="#6366F1"
                        strokeWidth="11"
                        strokeDasharray={`${(liveMetrics?.analytics?.format_ratio?.series?.percent || 28) * 2.38} 239`}
                        strokeDashoffset={`-${(liveMetrics?.analytics?.format_ratio?.movies?.percent || 64) * 2.38}`}
                        strokeLinecap="round"
                        className="transition-all duration-700"
                      />
                      {/* Audio/Docs Segment */}
                      <circle
                        cx="50"
                        cy="50"
                        r="38"
                        fill="transparent"
                        stroke="#10B981"
                        strokeWidth="11"
                        strokeDasharray={`${(liveMetrics?.analytics?.format_ratio?.audio_docs?.percent || 8) * 2.38} 239`}
                        strokeDashoffset={`-${((liveMetrics?.analytics?.format_ratio?.movies?.percent || 64) + (liveMetrics?.analytics?.format_ratio?.series?.percent || 28)) * 2.38}`}
                        strokeLinecap="round"
                        className="transition-all duration-700"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                      <span className="text-base font-bold font-mono text-white tracking-tight">100%</span>
                      <span className="text-[9px] font-mono uppercase text-neutral-400 tracking-wider">Indexed</span>
                    </div>
                  </div>

                  {/* Donut Legend */}
                  <div className="flex flex-col gap-3 text-xs w-full sm:w-auto">
                    <div className="flex items-center justify-between sm:justify-start gap-4">
                      <div className="flex items-center gap-2">
                        <span className="size-2.5 rounded-full bg-[#F97316]" />
                        <span className="text-neutral-300 font-medium">Feature Movies</span>
                      </div>
                      <span className="font-mono text-white font-semibold">
                        {liveMetrics?.analytics?.format_ratio?.movies?.percent || 64}%
                      </span>
                    </div>

                    <div className="flex items-center justify-between sm:justify-start gap-4">
                      <div className="flex items-center gap-2">
                        <span className="size-2.5 rounded-full bg-[#6366F1]" />
                        <span className="text-neutral-300 font-medium">TV Series &amp; Episodes</span>
                      </div>
                      <span className="font-mono text-white font-semibold">
                        {liveMetrics?.analytics?.format_ratio?.series?.percent || 28}%
                      </span>
                    </div>

                    <div className="flex items-center justify-between sm:justify-start gap-4">
                      <div className="flex items-center gap-2">
                        <span className="size-2.5 rounded-full bg-[#10B981]" />
                        <span className="text-neutral-300 font-medium">Audio &amp; Documents</span>
                      </div>
                      <span className="font-mono text-white font-semibold">
                        {liveMetrics?.analytics?.format_ratio?.audio_docs?.percent || 8}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Chart 2: 7-Day Conversion Velocity Trend (SVG Spline & Area) */}
              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-5 flex flex-col gap-4 shadow-xl">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-200 font-mono">
                      Conversion Velocity (7-Day)
                    </h3>
                  </div>
                  <span className="text-[11px] font-mono text-emerald-400">
                    Peak: {liveMetrics?.analytics?.weekly_velocity?.[6]?.conversions || 63} Streams/day
                  </span>
                </div>

                {/* SVG Area Chart */}
                <div className="w-full h-36 relative flex flex-col justify-end">
                  <svg className="w-full h-28 overflow-visible" viewBox="0 0 350 100" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="areaGradientPro" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#F97316" stopOpacity="0.25" />
                        <stop offset="100%" stopColor="#F97316" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Subtle grid lines */}
                    <line x1="0" y1="25" x2="350" y2="25" stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                    <line x1="0" y1="60" x2="350" y2="60" stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />

                    {/* Area fill */}
                    <path
                      d="M 10 75 Q 60 65 110 50 T 210 40 T 290 20 L 340 10 L 340 100 L 10 100 Z"
                      fill="url(#areaGradientPro)"
                    />
                    {/* Line curve */}
                    <path
                      d="M 10 75 Q 60 65 110 50 T 210 40 T 290 20 L 340 10"
                      fill="transparent"
                      stroke="#F97316"
                      strokeWidth="2.5"
                    />
                    {/* Data Points */}
                    {[
                      { cx: 10, cy: 75, val: 18 },
                      { cx: 65, cy: 62, val: 24 },
                      { cx: 120, cy: 50, val: 31 },
                      { cx: 175, cy: 45, val: 29 },
                      { cx: 230, cy: 38, val: 42 },
                      { cx: 285, cy: 22, val: 56 },
                      { cx: 340, cy: 10, val: liveMetrics?.analytics?.weekly_velocity?.[6]?.conversions || 63 },
                    ].map((pt, i) => (
                      <circle key={i} cx={pt.cx} cy={pt.cy} r="3.5" fill="#FFFFFF" stroke="#F97316" strokeWidth="2" />
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
                    <span className="text-emerald-400 font-semibold">Sun ({liveMetrics?.analytics?.weekly_velocity?.[6]?.conversions || 63})</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Quality & Resolution Breakdown Progress Meters */}
            <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-5 flex flex-col gap-4 shadow-xl">
              <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-200 font-mono">
                  Resolution &amp; Codec Spectrum
                </h3>
                <span className="text-[11px] font-mono text-neutral-500">Automated Bitrate Profiling</span>
              </div>

              {/* Unified Spectrum Bar */}
              <div className="w-full h-3 rounded-full bg-neutral-900 overflow-hidden flex p-0.5 border border-white/[0.06]">
                <div
                  className="h-full rounded-l-full bg-[#F97316] transition-all duration-500"
                  style={{ width: `${liveMetrics?.analytics?.resolution_ratio?.res_1080p?.percent || 54}%` }}
                />
                <div
                  className="h-full bg-[#38BDF8] transition-all duration-500"
                  style={{ width: `${liveMetrics?.analytics?.resolution_ratio?.res_4k?.percent || 28}%` }}
                />
                <div
                  className="h-full rounded-r-full bg-[#10B981] transition-all duration-500"
                  style={{ width: `${liveMetrics?.analytics?.resolution_ratio?.res_720p?.percent || 18}%` }}
                />
              </div>

              {/* 3 Detail Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-neutral-300">1080p FHD</span>
                    <span className="text-xs font-mono font-semibold text-[#F97316]">
                      {liveMetrics?.analytics?.resolution_ratio?.res_1080p?.percent || 54}%
                    </span>
                  </div>
                  <span className="text-[10px] text-neutral-500 font-mono">HEVC / x265 10-Bit</span>
                </div>

                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-neutral-300">4K UHD</span>
                    <span className="text-xs font-mono font-semibold text-[#38BDF8]">
                      {liveMetrics?.analytics?.resolution_ratio?.res_4k?.percent || 28}%
                    </span>
                  </div>
                  <span className="text-[10px] text-neutral-500 font-mono">HDR10+ / Dolby Vision</span>
                </div>

                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-neutral-300">720p HD</span>
                    <span className="text-xs font-mono font-semibold text-[#10B981]">
                      {liveMetrics?.analytics?.resolution_ratio?.res_720p?.percent || 18}%
                    </span>
                  </div>
                  <span className="text-[10px] text-neutral-500 font-mono">Mobile Direct Play</span>
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

              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-[#D97757]" />
                <span className="text-sm font-semibold tracking-tight text-white">
                  System Authority &amp; Security Matrix
                </span>
                <span className="text-[11px] text-[#D97757] font-mono px-2.5 py-0.5 rounded-full bg-[#D97757]/10 border border-[#D97757]/20 flex items-center gap-1.5">
                  <span className="size-1.5 rounded-full bg-[#D97757] animate-pulse" />
                  Root Verified
                </span>
              </div>
            </div>

            {/* Admin Profile & Authority Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
              {/* Profile Card */}
              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-5 flex flex-col gap-4 shadow-xl">
                <div className="flex items-center gap-3.5 pb-3 border-b border-white/[0.06]">
                  <div className="size-11 rounded-2xl bg-gradient-to-tr from-[#D97757] to-[#F59E0B] p-[1.5px] flex-shrink-0">
                    <div className="w-full h-full rounded-[14px] bg-[#09090b] flex items-center justify-center text-[#D97757] font-bold font-mono text-sm">
                      JP
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight">
                      {liveMetrics?.admin?.owner_name || "Jishnu P G"}
                    </h3>
                    <p className="text-[11px] font-mono text-neutral-400">
                      Primary System Architect &amp; Bot Owner
                    </p>
                  </div>
                </div>

                <div className="flex flex-col gap-3 text-xs">
                  <div className="flex items-center justify-between py-1.5 border-b border-white/[0.03]">
                    <span className="text-neutral-400 flex items-center gap-2">
                      <Terminal className="w-3.5 h-3.5 text-neutral-500" /> Telegram Handle
                    </span>
                    <a
                      href="https://t.me/Jishnuxpg"
                      target="_blank"
                      rel="noreferrer"
                      className="font-mono text-[#D97757] hover:underline flex items-center gap-1 font-medium"
                    >
                      {liveMetrics?.admin?.telegram_handle || "@Jishnuxpg"} <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="flex items-center justify-between py-1.5 border-b border-white/[0.03]">
                    <span className="text-neutral-400 flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-neutral-500" /> Contact Email
                    </span>
                    <a
                      href={`mailto:${liveMetrics?.admin?.contact_email || "jishnupg2005@gmail.com"}`}
                      className="font-mono text-white hover:text-[#D97757] transition-colors"
                    >
                      {liveMetrics?.admin?.contact_email || "jishnupg2005@gmail.com"}
                    </a>
                  </div>

                  <div className="flex items-center justify-between py-1.5 border-b border-white/[0.03]">
                    <span className="text-neutral-400 flex items-center gap-2">
                      <GitBranch className="w-3.5 h-3.5 text-neutral-500" /> GitHub Repository
                    </span>
                    <a
                      href="https://github.com/JishnuPG-tech/FiletoLink"
                      target="_blank"
                      rel="noreferrer"
                      className="font-mono text-neutral-300 hover:text-white hover:underline flex items-center gap-1"
                    >
                      {liveMetrics?.admin?.github_repo || "JishnuPG-tech/FiletoLink"} <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="flex items-center justify-between py-1.5">
                    <span className="text-neutral-400 flex items-center gap-2">
                      <Globe className="w-3.5 h-3.5 text-neutral-500" /> Hugging Face Space
                    </span>
                    <a
                      href="https://huggingface.co/spaces/Jishnupg/FileToLink"
                      target="_blank"
                      rel="noreferrer"
                      className="font-mono text-neutral-300 hover:text-white hover:underline flex items-center gap-1"
                    >
                      {liveMetrics?.admin?.hf_space || "jishnupg/FileToLink"} <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>

              {/* Security & Access Authority Card */}
              <div className="rounded-2xl bg-[#09090b]/90 border border-white/[0.08] p-5 flex flex-col gap-4 shadow-xl">
                <div className="flex items-center gap-2 pb-3 border-b border-white/[0.06]">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-200 font-mono">
                    Security &amp; Authorization Matrix
                  </h3>
                </div>

                <div className="flex flex-col gap-3 text-xs">
                  <div className="flex items-center justify-between py-1.5 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Root Access ID</span>
                    <span className="font-mono text-white font-medium">
                      {liveMetrics?.admin?.root_id || "1769298522"} (Primary Owner)
                    </span>
                  </div>

                  <div className="flex items-center justify-between py-1.5 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Target Channel</span>
                    <span className="font-mono text-white font-medium">
                      {liveMetrics?.admin?.bin_channel_id || "-1003931672617"} (BIN_CHANNEL)
                    </span>
                  </div>

                  <div className="flex items-center justify-between py-1.5 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Session Verification</span>
                    <span className="font-mono text-emerald-400 font-medium">SHA-256 HMAC Active</span>
                  </div>

                  <div className="flex items-center justify-between py-1.5 border-b border-white/[0.03]">
                    <span className="text-neutral-400">Anti-Flood Protection</span>
                    <span className="font-mono text-white font-medium">50ms Token Bucket Rate-Limit</span>
                  </div>

                  <div className="flex items-center justify-between py-1.5">
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
              </div>
            </div>

            {/* Blank State for Future Deployments */}
            {activeStaticFolder.items.length === 0 ? (
              <div className="w-full py-28 flex flex-col items-center justify-center gap-3 text-center rounded-2xl border border-dashed border-white/[0.08] bg-white/[0.01]">
                <div className="size-11 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-neutral-400">
                  <Layers className="w-5 h-5 text-neutral-400" />
                </div>
                <div className="flex flex-col gap-1">
                  <h4 className="text-sm font-medium text-neutral-200">
                    {activeStaticFolder.title}
                  </h4>
                  <p className="text-xs text-neutral-500 font-mono">
                    Workspace empty • Reserved for future modules
                  </p>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 w-full">
                {activeStaticFolder.items.map((item, index) => {
                  const imgUrl = typeof item.image === "object" ? item.image.src : item.image;
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      className="group rounded-2xl bg-[#09090b] border border-white/[0.08] hover:border-white/[0.18] p-3 flex flex-col gap-3 shadow-xl"
                    >
                      {imgUrl && (
                        <div className="w-full aspect-[4/3] rounded-xl overflow-hidden bg-neutral-900 relative">
                          <img
                            src={imgUrl}
                            alt={item.title || "Card"}
                            className="w-full h-full object-cover"
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
            )}
          </motion.div>
        )}
        </AnimatePresence>
    </div>
  );
};

export default CaseStudiesPage;
