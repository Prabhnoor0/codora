"use client";

import { useEffect, useState, useCallback } from"react";
import { motion } from"framer-motion";
import { useParams, useRouter } from"next/navigation";
import {
 Star, GitFork, ExternalLink, Brain, BookOpen,
 Target, Code2, Network, Layers, ArrowRight,
 CheckCircle2, Loader2, Clock, Zap, Shield,
 Database, Globe, Cpu, Lock
} from"lucide-react";
import { repoApi } from"@/lib/api";

const SUBSYSTEM_ICONS: Record<string, any> = {
 auth: Lock, authentication: Lock, security: Shield,
 database: Database, db: Database, storage: Database,
 api: Globe, rest: Globe, graphql: Globe,
 ml: Cpu, ai: Cpu, model: Cpu,
 payment: Zap, billing: Zap,
};

const getSubsystemIcon = (name: string) => {
 const lower = name.toLowerCase();
 for (const [key, Icon] of Object.entries(SUBSYSTEM_ICONS)) {
 if (lower.includes(key)) return Icon;
 }
 return Layers;
};

const STAGE_LABELS: Record<string, string> = {
"Fetching repository data":"Fetching repository data...",
"Analyzing architecture":"Analyzing architecture with AI...",
"Identifying subsystems":"Identifying subsystems...",
"Saving analysis":"Saving results...",
"Building knowledge graph":"Building knowledge graph in Neo4j...",
"Indexing documentation":"Indexing documentation into Qdrant...",
"Indexing codebase":"Embedding codebase with CodeBERT...",
"Analyzing issues":"Analyzing open issues...",
"Completed":"Analysis complete!",
};

export default function RepoPage() {
 const params = useParams();
 const router = useRouter();
 const owner = params.owner as string;
 const name = params.name as string;

 const [repo, setRepo] = useState<any>(null);
 const [loading, setLoading] = useState(true);
 const [activeTab, setActiveTab] = useState<"overview" |"subsystems" |"architecture" |"issues" |"mentor">("overview");

 const fetchRepo = useCallback(async () => {
 try {
 const data = await repoApi.get(owner, name);
 setRepo(data);
 if (data.analysis_status ==="running" || data.analysis_status ==="pending") {
 setTimeout(fetchRepo, 2000); // Poll every 2s
 }
 } catch (e) {
 console.error(e);
 } finally {
 setLoading(false);
 }
 }, [owner, name]);

 useEffect(() => { fetchRepo(); }, [fetchRepo]);

 if (loading) return (
 <div className="min-h-screen flex items-center justify-center">
 <div className="text-center">
 <div className="w-16 h-16 border-2 border-violet-500 border-t-transparent animate-spin mx-auto mb-4" />
 <p className="text-slate-400">Loading repository...</p>
 </div>
 </div>
 );

 if (!repo) return (
 <div className="min-h-screen flex items-center justify-center text-slate-400">
 Repository not found. <a href="/dashboard" className="text-violet-400 ml-2">Go back →</a>
 </div>
 );

 const isAnalyzing = repo.analysis_status ==="running" || repo.analysis_status ==="pending";

 return (
 <div className="min-h-screen p-8 max-w-7xl mx-auto">
 {/* Header */}
 <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
 <div className="flex items-start justify-between">
 <div>
 <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
 <a href="/dashboard" className="hover:text-slate-300 transition-colors">Dashboard</a>
 <span>/</span>
 <span className="text-slate-300">{owner}/{name}</span>
 </div>
 <h1 className="text-4xl font-black mb-2">
 <span className="text-slate-400">{owner}/</span>
 <span className="gradient-text">{name}</span>
 </h1>
 {repo.description && (
 <p className="text-slate-400 text-lg max-w-3xl">{repo.description}</p>
 )}
 <div className="flex items-center gap-4 mt-3">
 <span className="flex items-center gap-1 text-sm text-slate-500">
 <Star className="w-4 h-4 text-yellow-500" /> {repo.stars?.toLocaleString()}
 </span>
 <span className="flex items-center gap-1 text-sm text-slate-500">
 <GitFork className="w-4 h-4" /> {repo.forks?.toLocaleString()}
 </span>
 {repo.language && <span className="badge badge-violet">{repo.language}</span>}
 {repo.difficulty_level && (
 <span className={`badge ${
 repo.difficulty_level ==="beginner" ?"badge-green" :
 repo.difficulty_level ==="intermediate" ?"badge-amber" :"badge-red"
 }`}>
 {repo.difficulty_level}
 </span>
 )}
 <a href={repo.url} target="_blank" rel="noopener noreferrer"
 className="flex items-center gap-1 text-sm text-slate-500 hover:text-white transition-colors">
 <ExternalLink className="w-4 h-4" /> View on GitHub
 </a>
 </div>
 </div>
 </div>
 </motion.div>

 {/* Analysis Progress */}
 {isAnalyzing && (
 <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
 className="glass-strong p-6 mb-8 border-glow animate-pulse-glow">
 <div className="flex items-center gap-3 mb-4">
 <Loader2 className="w-5 h-5 text-violet-400 animate-spin" />
 <span className="font-semibold">AI Analysis in Progress</span>
 <span className="text-violet-400 font-bold ml-auto">{repo.analysis_progress}%</span>
 </div>
 <div className="progress-bar mb-3">
 <div className="progress-fill" style={{ width: `${repo.analysis_progress}%` }} />
 </div>
 <p className="text-sm text-slate-400">
 {STAGE_LABELS[repo.analysis_stage] || repo.analysis_stage ||"Initializing..."}
 </p>
 </motion.div>
 )}

 {/* Tabs */}
 <div className="flex gap-1 mb-6 glass p-1 w-fit">
 {[
 { key:"overview", icon: Brain, label:"Overview" },
 { key:"subsystems", icon: Layers, label:"Subsystems" },
 { key:"architecture", icon: Network, label:"Architecture" },
 { key:"issues", icon: Target, label:"Issues" },
 { key:"mentor", icon: BookOpen, label:"Mentor Chat" },
 ].map((tab) => (
 <button
 key={tab.key}
 onClick={() => {
 if (tab.key ==="architecture") router.push(`/repo/${owner}/${name}/architecture`);
 else if (tab.key ==="issues") router.push(`/repo/${owner}/${name}/issues`);
 else if (tab.key ==="mentor") router.push(`/repo/${owner}/${name}/mentor`);
 else setActiveTab(tab.key as any);
 }}
 className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-all ${
 activeTab === tab.key
 ?"bg-violet-600 text-white"
 :"text-slate-400 hover:text-white hover:bg-white/5"
 }`}
 >
 <tab.icon className="w-4 h-4" />
 {tab.label}
 </button>
 ))}
 </div>

 {/* Overview Tab */}
 {activeTab ==="overview" && (
 <div className="grid grid-cols-3 gap-6">
 {/* Purpose */}
 <div className="col-span-2 card p-6">
 <h2 className="font-bold text-lg mb-3 flex items-center gap-2">
 <Brain className="w-5 h-5 text-violet-400" /> What is this project?
 </h2>
 {repo.purpose ? (
 <p className="text-slate-300 leading-relaxed">{repo.purpose}</p>
 ) : (
 <div className="space-y-2">
 <div className="skeleton h-4 rounded w-full" />
 <div className="skeleton h-4 rounded w-4/5" />
 <div className="skeleton h-4 rounded w-3/4" />
 </div>
 )}
 </div>

 {/* Tech Stack */}
 <div className="card p-6">
 <h2 className="font-bold text-lg mb-3">Tech Stack</h2>
 {repo.tech_stack ? (
 <div className="flex flex-wrap gap-2">
 {repo.tech_stack.map((tech: string) => (
 <span key={tech} className="badge badge-violet">{tech}</span>
 ))}
 </div>
 ) : (
 <div className="space-y-2">
 {[1, 2, 3, 4].map(i => (
 <div key={i} className="skeleton h-6 w-20" />
 ))}
 </div>
 )}
 </div>

 {/* Architecture */}
 <div className="col-span-2 card p-6">
 <h2 className="font-bold text-lg mb-3 flex items-center gap-2">
 <Layers className="w-5 h-5 text-indigo-400" /> Architecture
 </h2>
 {repo.architecture_summary ? (
 <p className="text-slate-300 leading-relaxed">{repo.architecture_summary}</p>
 ) : (
 <div className="space-y-2">
 <div className="skeleton h-4 rounded w-full" />
 <div className="skeleton h-4 rounded w-5/6" />
 </div>
 )}
 </div>

 {/* Prerequisites */}
 <div className="card p-6">
 <h2 className="font-bold text-lg mb-3">Prerequisites</h2>
 {repo.learning_prerequisites ? (
 <ul className="space-y-2">
 {repo.learning_prerequisites.map((prereq: string) => (
 <li key={prereq} className="flex items-center gap-2 text-sm text-slate-300">
 <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
 {prereq}
 </li>
 ))}
 </ul>
 ) : (
 <div className="space-y-2">
 {[1, 2, 3].map(i => <div key={i} className="skeleton h-5 rounded w-full" />)}
 </div>
 )}
 </div>

 {/* Learning CTA */}
 <div className="col-span-3">
 <motion.div whileHover={{ scale: 1.01 }}
 className="glass-strong p-6 flex items-center justify-between">
 <div>
 <h3 className="font-bold text-xl mb-1">Ready to start learning?</h3>
 <p className="text-slate-400">Get a personalized {repo.difficulty_level ==="beginner" ?"5" :"7"}-day learning roadmap for {name}</p>
 </div>
 <a href={`/repo/${owner}/${name}/learn`} className="btn-primary">
 Generate Learning Path <ArrowRight className="w-4 h-4" />
 </a>
 </motion.div>
 </div>
 </div>
 )}

 {/* Subsystems Tab */}
 {activeTab ==="subsystems" && (
 <div>
 <h2 className="font-bold text-2xl mb-6">
 Repository Subsystems
 <span className="text-slate-500 text-base font-normal ml-3">
 {repo.subsystems?.length || 0} systems identified
 </span>
 </h2>
 {repo.subsystems ? (
 <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
 {repo.subsystems.map((sys: any, i: number) => {
 const Icon = getSubsystemIcon(sys.name);
 return (
 <motion.div
 key={i}
 className="card p-5 cursor-pointer group"
 whileHover={{ y: -4 }}
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: i * 0.05 }}
 >
 <div className="flex items-center gap-3 mb-3">
 <div className="w-10 h-10 flex items-center justify-center"
 style={{ background: `${sys.color ||"#8b5cf6"}22`, border: `1px solid ${sys.color ||"#8b5cf6"}44` }}>
 <Icon className="w-5 h-5" style={{ color: sys.color ||"#8b5cf6" }} />
 </div>
 <div>
 <h3 className="font-bold text-sm">{sys.name}</h3>
 <span className={`badge text-xs ${
 sys.complexity ==="high" ?"badge-red" :
 sys.complexity ==="medium" ?"badge-amber" :"badge-green"
 }`}>{sys.complexity}</span>
 </div>
 </div>
 <p className="text-sm text-slate-400 leading-relaxed mb-3">{sys.description}</p>
 {sys.key_concepts && (
 <div className="flex flex-wrap gap-1">
 {sys.key_concepts.slice(0, 3).map((c: string) => (
 <span key={c} className="text-xs text-slate-600 bg-slate-800 px-2 py-0.5">{c}</span>
 ))}
 </div>
 )}
 <div className="mt-3 flex items-center gap-1 text-xs text-slate-600 group-hover:text-violet-400 transition-colors">
 <Code2 className="w-3 h-3" />
 {sys.files?.length || 0} files
 <ArrowRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
 </div>
 </motion.div>
 );
 })}
 </div>
 ) : (
 <div className="grid grid-cols-3 gap-4">
 {[1, 2, 3, 4, 5, 6].map(i => (
 <div key={i} className="card p-5 skeleton h-40" />
 ))}
 </div>
 )}
 </div>
 )}
 </div>
 );
}
