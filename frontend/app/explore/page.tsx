"use client";
import { useState, useEffect, useCallback } from"react";
import { useRouter } from"next/navigation";
import { motion } from"framer-motion";
import {
 Brain, Star, GitFork, AlertCircle, Search,
 ChevronRight, Zap, LogOut, User, RefreshCw, Home
} from"lucide-react";
import { useUserStore } from"@/lib/store";

const API = process.env.NEXT_PUBLIC_API_URL ||"http://localhost:8000";

const DIFFICULTY_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
 Easy: { color:"text-slate-700", bg:"bg-slate-100", label:"Easy" },
 Medium: { color:"text-slate-800", bg:"bg-slate-200", label:"Medium" },
 Hard: { color:"text-slate-100", bg:"bg-slate-800", label:"Hard" },
};

function SkillMatchBar({ pct }: { pct: number }) {
 return (
 <div className="mt-4">
 <div className="flex justify-between items-end mb-2">
 <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Skill match</span>
 <span className="text-sm font-extrabold text-slate-900">{pct}%</span>
 </div>
 <div className="h-1.5 bg-slate-100 overflow-hidden">
 <div className="h-full bg-slate-800 transition-all duration-700 ease-out" style={{ width: `${pct}%` }} />
 </div>
 </div>
 );
}

function ProjectCard({ project, onClick }: { project: any; onClick: () => void }) {
 const diff = DIFFICULTY_CONFIG[project.difficulty] || DIFFICULTY_CONFIG.Medium;
 return (
 <motion.div
 whileHover={{ y: -4 }}
 onClick={onClick}
 className="bg-white p-6 cursor-pointer border border-slate-200 hover:-hover transition-all duration-300 flex flex-col group h-full"
 >
 {/* Header */}
 <div className="flex items-start gap-4 mb-4">
 <img
 src={project.avatar_url || `https://github.com/${project.owner}.png`}
 alt={project.owner}
 className="w-12 h-12 border border-slate-200 flex-shrink-0"
 onError={(e: any) => { e.target.src ="https://github.com/github.png"; }}
 />
 <div className="flex-1 min-w-0">
 <h3 className="text-lg font-bold text-slate-900 break-words leading-tight mb-1 group-hover:text-slate-600 transition-colors">
 {project.owner}/<span className="text-slate-500 font-medium">{project.name}</span>
 </h3>
 <p className="text-sm text-slate-500 line-clamp-2 leading-relaxed">
 {project.description}
 </p>
 </div>
 </div>

 {/* Tags */}
 <div className="flex flex-wrap gap-2 mb-5">
 <span className={`px-2.5 py-1 text-xs font-bold border border-white/20 ${diff.bg} ${diff.color}`}>
 {diff.label}
 </span>
 {project.language && (
 <span className="px-2.5 py-1 text-xs font-semibold bg-slate-50 text-slate-600 border border-slate-200">
 {project.language}
 </span>
 )}
 {project.topics?.slice(0, 2).map((t: string) => (
 <span key={t} className="px-2.5 py-1 text-xs font-medium bg-white text-slate-500 border border-slate-200">
 {t}
 </span>
 ))}
 </div>

 {/* Stats */}
 <div className="flex gap-4 mb-2 mt-auto">
 <span className="flex items-center gap-1.5 text-sm font-medium text-slate-500">
 <Star className="w-4 h-4 text-slate-600" />
 {(project.stars || 0).toLocaleString()}
 </span>
 <span className="flex items-center gap-1.5 text-sm font-medium text-slate-500">
 <GitFork className="w-4 h-4 text-slate-400" />
 {(project.forks || 0).toLocaleString()}
 </span>
 <span className="flex items-center gap-1.5 text-sm font-medium text-slate-500">
 <AlertCircle className="w-4 h-4 text-slate-500" />
 {project.open_issues || 0}
 </span>
 </div>

 <SkillMatchBar pct={project.skill_match || 0} />

 <div className="mt-5 flex justify-end">
 <span className="inline-flex items-center gap-1.5 text-sm font-bold text-slate-900 group-hover:text-slate-500 transition-colors">
 Explore project <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
 </span>
 </div>
 </motion.div>
 );
}

export default function ExplorePage() {
 const router = useRouter();
 const { user, token, logout } = useUserStore();
 const [projects, setProjects] = useState<any[]>([]);
 const [loading, setLoading] = useState(true);
 const [search, setSearch] = useState("");
 const [difficulty, setDifficulty] = useState<string>("");
 const [language, setLanguage] = useState<string>("");
 const [page, setPage] = useState(1);
 const [hasMore, setHasMore] = useState(true);
 const [loadingMore, setLoadingMore] = useState(false);

 const fetchProjects = useCallback(async (pageNum: number = 1, append: boolean = false) => {
 if (!token) return;
 if (!append) setLoading(true);
 else setLoadingMore(true);

 try {
 const params = new URLSearchParams({ limit:"18", page: pageNum.toString() });
 if (difficulty) params.set("difficulty", difficulty);
 if (language) params.set("language", language);
 const res = await fetch(`${API}/api/discover/projects?${params}`, {
 headers: { Authorization: `Bearer ${token}` },
 });
 const data = await res.json();
 if (append) {
 setProjects(prev => [...prev, ...(data.projects || [])]);
 } else {
 setProjects(data.projects || []);
 }
 setHasMore(data.has_more);
 setPage(data.page);
 } catch (e) {
 if (!append) setProjects([]);
 } finally {
 setLoading(false);
 setLoadingMore(false);
 }
 }, [token, difficulty, language]);

 useEffect(() => {
 if (!user) { router.push("/"); return; }
 fetchProjects(1, false);
 }, [user, router, fetchProjects]);

 const handleRefresh = () => {
 setPage(1);
 fetchProjects(1, false);
 };

 const handleLoadMore = () => {
 fetchProjects(page + 1, true);
 };

 const filtered = projects.filter(p =>
 !search || `${p.owner}/${p.name} ${p.description}`.toLowerCase().includes(search.toLowerCase())
 );

 return (
 <div className="min-h-screen bg-slate-50 font-sans selection:bg-slate-800 selection:text-white">
 {/* Navbar */}
 <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200 h-16 flex items-center justify-between px-6 sm:px-12">
 <div className="flex items-center gap-2">
 <div className="w-8 h-8 bg-slate-900 flex items-center justify-center text-white">
 <Brain className="w-4 h-4" />
 </div>
 <span className="font-extrabold text-lg text-slate-900 tracking-tight">Codora</span>
 </div>
 <div className="flex items-center gap-3">
 <button onClick={() => router.push("/explore")} className="hidden sm:flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 hover:text-slate-900 text-sm font-semibold transition-colors">
 <Home className="w-4 h-4" /> Explore
 </button>
 {user && (
 <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200">
 <img src={user.github_avatar_url} alt={user.github_login} className="w-6 h-6" />
 <span className="text-sm font-semibold text-slate-700 pr-1">{user.github_login}</span>
 </div>
 )}
 <button onClick={() => router.push("/profile/setup")} className="p-2 text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors" title="Edit skills">
 <User className="w-5 h-5" />
 </button>
 <button onClick={() => { logout(); router.push("/"); }} className="p-2 text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors" title="Sign out">
 <LogOut className="w-5 h-5" />
 </button>
 </div>
 </nav>

 {/* Hero */}
 <div className="bg-white border-b border-slate-200 pt-16 pb-12 px-6 sm:px-12 relative overflow-hidden">
 <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-slate-100 mix-blend-multiply filter blur-3xl opacity-50 pointer-events-none" />
 
 <div className="max-w-6xl mx-auto relative z-10">
 <div className="flex items-center gap-2 mb-4">
 <div className="w-8 h-8 bg-slate-100 flex items-center justify-center">
 <Zap className="w-4 h-4 text-slate-700" />
 </div>
 <span className="text-xs font-bold text-slate-700 uppercase tracking-widest">AI-Matched Projects</span>
 </div>
 <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 mb-4 tracking-tight">
 Open source projects <br className="hidden sm:block" />
 <span className="text-gradient">built for you</span>
 </h1>
 <p className="text-lg text-slate-500 mb-10 max-w-2xl font-medium">
 Matched to <span className="font-bold text-slate-700">{user?.github_login}'s</span> skills in{""}
 <span className="font-bold text-slate-900">{user?.top_languages?.slice(0, 3).join(",") ||"your languages"}</span>
 </p>

 {/* Filters */}
 <div className="flex flex-col sm:flex-row gap-4">
 <div className="relative flex-1 max-w-md">
 <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
 <input
 type="text" placeholder="Search projects by name or description..."
 value={search} onChange={e => setSearch(e.target.value)}
 className="w-full pl-11 pr-4 py-3 bg-white border border-slate-200 text-sm font-medium text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500/20 focus:border-slate-500 transition-all"
 />
 </div>
 <select value={difficulty} onChange={e => setDifficulty(e.target.value)}
 className="px-4 py-3 bg-white border border-slate-200 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500/20 focus:border-slate-500 transition-all cursor-pointer">
 <option value="">All difficulties</option>
 <option value="Easy">Easy</option>
 <option value="Medium">Medium</option>
 <option value="Hard">Hard</option>
 </select>
 <select value={language} onChange={e => setLanguage(e.target.value)}
 className="px-4 py-3 bg-white border border-slate-200 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500/20 focus:border-slate-500 transition-all cursor-pointer">
 <option value="">All languages</option>
 {["Python","JavaScript","TypeScript","Go","Rust","Java","C++","Ruby"].map(l => (
 <option key={l} value={l}>{l}</option>
 ))}
 </select>
 <button onClick={handleRefresh} className="flex items-center justify-center gap-2 px-6 py-3 bg-slate-900 text-white text-sm font-bold hover:bg-slate-800 transition-colors group">
 <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" /> Refresh
 </button>
 </div>
 </div>
 </div>

 {/* Projects Grid */}
 <div className="max-w-7xl mx-auto px-6 sm:px-12 py-12">
 {loading ? (
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
 {Array.from({ length: 6 }).map((_, i) => (
 <div key={i} className="bg-white p-6 border border-slate-200 h-64 flex flex-col gap-4">
 <div className="flex items-center gap-4">
 <div className="w-12 h-12 bg-slate-100 animate-pulse" />
 <div className="flex-1 space-y-2">
 <div className="h-4 bg-slate-100 w-3/4 animate-pulse" />
 <div className="h-3 bg-slate-100 w-1/2 animate-pulse" />
 </div>
 </div>
 <div className="space-y-2 mt-2">
 <div className="h-3 bg-slate-100 w-full animate-pulse" />
 <div className="h-3 bg-slate-100 w-5/6 animate-pulse" />
 </div>
 <div className="mt-auto h-2 bg-slate-100 w-full animate-pulse" />
 </div>
 ))}
 </div>
 ) : filtered.length === 0 ? (
 <div className="text-center py-24 bg-white border border-slate-200">
 <div className="w-16 h-16 bg-slate-100 flex items-center justify-center mx-auto mb-4">
 <Search className="w-8 h-8 text-slate-400" />
 </div>
 <h3 className="text-xl font-bold text-slate-900 mb-2">No projects found</h3>
 <p className="text-slate-500 mb-6 font-medium">Try updating your skills or changing the active filters.</p>
 <button onClick={() => router.push("/profile/setup")} className="px-6 py-3 bg-slate-900 hover:bg-slate-800 text-white font-bold hover:-translate-y-0.5 transition-all">
 Update skills
 </button>
 </div>
 ) : (
 <>
 <div className="flex items-center justify-between mb-8">
 <p className="text-sm font-semibold text-slate-500">
 Showing <span className="text-slate-900 font-bold">{filtered.length}</span> projects matched to you
 </p>
 </div>
 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
 {filtered.map((project, i) => (
 <motion.div
 key={`${project.owner}/${project.name}`}
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: Math.min(i * 0.05, 0.5) }}
 >
 <ProjectCard
 project={project}
 onClick={() => router.push(`/project/${project.owner}/${project.name}`)}
 />
 </motion.div>
 ))}
 </div>
 
 {hasMore && (
 <div className="text-center mt-12">
 <button 
 onClick={handleLoadMore} 
 disabled={loadingMore}
 className="px-8 py-3 bg-white text-slate-700 font-bold border border-slate-200 hover: hover:border-slate-300 disabled:opacity-50 transition-all"
 >
 {loadingMore ?"Loading..." :"Load More Repositories"}
 </button>
 </div>
 )}
 </>
 )}
 </div>
 </div>
 );
}
