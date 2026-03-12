"use client";
import { useState, useEffect } from"react";
import { useParams, useRouter } from"next/navigation";
import { motion } from"framer-motion";
import {
 Brain, Star, GitFork, AlertCircle, ExternalLink,
 ChevronRight, ArrowLeft, Shield, Code2, Database,
 BookOpen, Target, MessageCircle, Zap, CheckCircle2, ArrowRight
} from"lucide-react";
import { useUserStore } from"@/lib/store";

const API = process.env.NEXT_PUBLIC_API_URL ||"http://localhost:8000";

function MermaidDiagram({ diagram }: { diagram: string }) {
 const [svg, setSvg] = useState<string>("");
 const [error, setError] = useState(false);

 useEffect(() => {
 if (!diagram) return;
 import("mermaid").then(({ default: mermaid }) => {
 mermaid.initialize({ startOnLoad: false, theme:"base", themeVariables: {
 primaryColor:"#ffffff", primaryBorderColor:"#e2e8f0",
 lineColor:"#475569", fontSize:"14px", textColor:"#0f172a"
 }});
 const id ="mermaid-" + Math.random().toString(36).slice(2);
 mermaid.render(id, diagram).then(({ svg: rendered }: any) => setSvg(rendered)).catch(() => {
 setError(true);
 });
 }).catch(() => setError(true));
 }, [diagram]);

 if (error) return (
 <div className="p-6 bg-slate-50 border border-slate-200 text-sm font-medium text-slate-500">
 Could not render architectural diagram.
 </div>
 );
 if (!svg) return <div className="p-12 text-center text-sm font-semibold text-slate-400 bg-slate-50 border border-slate-100">Loading diagram architecture...</div>;
 return <div dangerouslySetInnerHTML={{ __html: svg }} className="text-center overflow-x-auto bg-white p-8 border border-slate-100" />;
}

function SkillBar({ lang, repoPct, userHas }: { lang: string; repoPct: number; userHas: boolean }) {
 return (
 <div className="mb-5">
 <div className="flex justify-between items-end mb-2">
 <span className="text-sm font-bold text-slate-700 flex items-center gap-2">
 {userHas ? <CheckCircle2 className="w-4 h-4 text-slate-900" /> : <div className="w-4 h-4 border-2 border-slate-200" />} {lang}
 </span>
 <span className="text-xs font-bold text-slate-500">{repoPct}%</span>
 </div>
 <div className="h-2 bg-slate-100 w-full overflow-hidden border border-slate-200/50">
 <div className={`h-full ${userHas ?"bg-slate-800" :"bg-slate-300"} transition-all duration-700 ease-out`} style={{ width: `${repoPct}%` }} />
 </div>
 </div>
 );
}

export default function ProjectDetailPage() {
 const params = useParams();
 const router = useRouter();
 const { user, token } = useUserStore();
 const owner = params.owner as string;
 const repo = params.repo as string;

 const [project, setProject] = useState<any>(null);
 const [loading, setLoading] = useState(true);
 const [activeTab, setActiveTab] = useState<"overview"|"issues"|"diagram">("overview");

 useEffect(() => {
 if (!user) { router.push("/"); return; }
 if (!owner || !repo) return;
 fetch(`${API}/api/discover/projects/${owner}/${repo}`, {
 headers: { Authorization: `Bearer ${token}` },
 }).then(r => r.json()).then(setProject).catch(() => setProject(null)).finally(() => setLoading(false));
 }, [user, token, owner, repo, router]);

 if (loading) return (
 <div className="min-h-screen flex items-center justify-center bg-slate-50">
 <div className="text-center">
 <div className="w-12 h-12 border-4 border-slate-200 border-t-slate-800 animate-spin mx-auto mb-4" />
 <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Analyzing Repository</p>
 </div>
 </div>
 );

 if (!project) return (
 <div className="min-h-screen flex items-center justify-center bg-slate-50 text-center">
 <div className="bg-white p-12 border border-slate-100 max-w-md w-full mx-4">
 <div className="w-16 h-16 bg-slate-100 text-slate-600 flex items-center justify-center mx-auto mb-6">
 <AlertCircle className="w-8 h-8" />
 </div>
 <h2 className="font-extrabold text-2xl text-slate-900 mb-3">Project not found</h2>
 <p className="text-slate-500 font-medium mb-8">We couldn't locate this repository. It may have been moved or deleted.</p>
 <button onClick={() => router.push("/explore")} className="w-full px-6 py-3 bg-slate-900 text-white font-bold hover:bg-slate-800 transition-colors">
 Return to Explore
 </button>
 </div>
 </div>
 );

 const TABS = [
 { key:"overview", label:"Overview", icon: BookOpen },
 { key:"diagram", label:"Architecture", icon: Code2 },
 { key:"issues", label: `Issues (${project.good_first_issues?.length || 0})`, icon: Target },
 ];

 return (
 <div className="bg-slate-50 min-h-screen text-slate-900 pb-24 font-sans selection:bg-slate-800 selection:text-white relative overflow-hidden">
 
 {/* Background Orbs */}
 <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-slate-300 mix-blend-multiply filter blur-3xl opacity-50 pointer-events-none animate-pulse-slow" />
 <div className="absolute top-40 left-0 w-[500px] h-[500px] bg-slate-200 mix-blend-multiply filter blur-3xl opacity-50 pointer-events-none animate-pulse-slow" style={{ animationDelay: '2s' }} />

 {/* Navbar */}
 <nav className="bg-white/80 backdrop-blur-xl border-b border-slate-200 h-16 flex items-center justify-between px-6 sm:px-12 sticky top-0 z-50">
 <div className="flex items-center gap-4">
 <button onClick={() => router.push("/explore")} className="flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-900 transition-colors bg-white hover:bg-slate-100 px-3 py-1.5 border border-transparent hover:border-slate-200">
 <ArrowLeft className="w-4 h-4" /> Explore
 </button>
 <div className="w-px h-4 bg-slate-200 hidden sm:block" />
 <span className="font-extrabold text-sm text-slate-800 hidden sm:block tracking-tight">{owner}/<span className="text-slate-500 font-medium">{repo}</span></span>
 </div>
 <div className="flex items-center gap-4">
 <button
 onClick={() => router.push(`/repo/${owner}/${repo}/intel`)}
 className="px-5 py-2 bg-slate-900 text-white text-xs font-bold flex items-center gap-2 hover:bg-slate-800 hover:-translate-y-0.5 transition-all"
 >
 <Brain className="w-4 h-4" /> Deep AI Analysis
 </button>
 {user && <img src={user.github_avatar_url} alt="" className="w-8 h-8 border border-slate-200" />}
 </div>
 </nav>

 {/* Hero */}
 <header className="relative z-10 pt-16 pb-12 px-6 sm:px-12">
 <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-8 items-start">
 <img src={`https://github.com/${owner}.png`} alt={owner} className="w-24 h-24 border border-slate-200 flex-shrink-0 bg-white p-1"
 onError={(e: any) => { e.target.src ="https://github.com/github.png"; }} />
 
 <div className="flex-1">
 <div className="flex flex-wrap items-center gap-3 mb-3">
 <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
 <a href={project.html_url} target="_blank" rel="noopener noreferrer" className="hover:text-slate-600 transition-colors">
 {owner}/<span className="text-slate-500">{repo}</span>
 </a>
 </h1>
 <span className={`px-3 py-1 text-xs font-bold border ${
 project.difficulty === 'Easy' ? 'bg-slate-100 text-slate-700 border-slate-200' : 
 project.difficulty === 'Medium' ? 'bg-slate-200 text-slate-800 border-slate-300' : 
 'bg-slate-800 text-slate-100 border-slate-700'
 }`}>
 {project.difficulty}
 </span>
 </div>
 
 <p className="text-lg text-slate-600 mb-8 max-w-3xl leading-relaxed font-medium">
 {project.ai_summary || project.description}
 </p>

 {/* Stats */}
 <div className="flex gap-6 sm:gap-10 flex-wrap">
 {[
 { icon: Star, value: (project.stars || 0).toLocaleString(), label:"Stars", color:"text-slate-700" },
 { icon: GitFork, value: (project.forks || 0).toLocaleString(), label:"Forks", color:"text-slate-500" },
 { icon: AlertCircle, value: project.open_issues || 0, label:"Issues", color:"text-slate-600" },
 ].map(({ icon: Icon, value, label, color }) => (
 <div key={label} className="flex items-center gap-3 bg-white px-4 py-2 border border-slate-100">
 <Icon className={`w-5 h-5 ${color}`} />
 <div>
 <div className="font-extrabold text-slate-900 leading-none mb-0.5">{value}</div>
 <div className="text-xs font-semibold text-slate-500">{label}</div>
 </div>
 </div>
 ))}
 </div>
 </div>
 </div>
 </header>

 {/* Tabs */}
 <div className="sticky top-16 z-40 bg-slate-50/90 backdrop-blur-md pt-4 border-b border-slate-200">
 <div className="max-w-6xl mx-auto px-6 sm:px-12 flex gap-8">
 {TABS.map(tab => {
 const Icon = tab.icon;
 return (
 <button key={tab.key} onClick={() => setActiveTab(tab.key as any)} 
 className={`pb-4 flex items-center gap-2 text-sm font-bold border-b-2 transition-all ${activeTab === tab.key ? 'border-slate-900 text-slate-900' : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'}`}>
 <Icon className="w-4 h-4" />
 {tab.label}
 </button>
 )
 })}
 </div>
 </div>

 {/* Content */}
 <div className="max-w-6xl mx-auto px-6 sm:px-12 py-10 relative z-10">

 {activeTab ==="overview" && (
 <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
 <div className="lg:col-span-2 flex flex-col gap-6">
 
 {/* AI Intelligence CTA */}
 <div onClick={() => router.push(`/repo/${owner}/${repo}/intel`)} className="bg-slate-900 p-8 hover:-hover hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col md:flex-row items-center justify-between gap-6 overflow-hidden relative group">
 <div className="absolute top-0 right-0 w-64 h-64 bg-slate-700 filter blur-[80px] opacity-40 group-hover:opacity-60 transition-opacity" />
 <div className="relative z-10">
 <p className="text-2xl font-extrabold text-white mb-2">Want a deeper understanding?</p>
 <p className="text-sm text-slate-400 font-medium">Subsystem map • Walkthrough • Learning path • Explainer</p>
 </div>
 <div className="relative z-10 bg-white text-slate-900 px-6 py-3 font-bold text-sm whitespace-nowrap flex items-center gap-2 group-hover:bg-slate-100 transition-colors">
 Open AI Intelligence <ArrowRight className="w-4 h-4" />
 </div>
 </div>

 {/* Getting Started */}
 {project.getting_started?.length > 0 && (
 <div className="bg-white border border-slate-100 p-8">
 <h2 className="text-xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
 <Zap className="w-5 h-5 text-slate-600" /> Getting Started
 </h2>
 <div className="flex flex-col gap-5">
 {project.getting_started.map((step: string, i: number) => (
 <div key={i} className="flex gap-4">
 <div className="w-8 h-8 bg-slate-100 text-slate-700 text-sm font-extrabold flex items-center justify-center flex-shrink-0">
 {i + 1}
 </div>
 <p className="text-base text-slate-600 pt-1 leading-relaxed font-medium">{step}</p>
 </div>
 ))}
 </div>
 </div>
 )}

 {/* Tech Stack */}
 {project.tech_breakdown?.length > 0 && (
 <div className="bg-white border border-slate-100 p-8">
 <h2 className="text-xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
 <Code2 className="w-5 h-5 text-slate-600" /> Tech Stack
 </h2>
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
 {project.tech_breakdown.map((t: any, i: number) => (
 <div key={i} className="flex flex-col p-4 bg-slate-50 border border-slate-100">
 <span className="text-sm font-extrabold text-slate-900 mb-1">{t.name}</span>
 <span className="text-xs font-medium text-slate-500">{t.role}</span>
 </div>
 ))}
 </div>
 </div>
 )}
 </div>

 {/* Sidebar Panels */}
 <div className="flex flex-col gap-6">
 <div className="bg-white border border-slate-100 p-8">
 <h2 className="text-xs font-bold text-slate-400 mb-6 uppercase tracking-widest">Skill Match</h2>
 <div className="mb-8 flex items-baseline gap-2">
 <span className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-500">{project.skill_match}%</span>
 <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Overall</span>
 </div>
 {project.skill_match_detail?.map((s: any, i: number) => (
 <SkillBar key={i} lang={s.lang} repoPct={s.repo_pct} userHas={s.user_has} />
 ))}
 </div>

 <div className="bg-white border border-slate-100 p-8 text-center">
 <div className="w-12 h-12 bg-slate-100 text-slate-700 flex items-center justify-center mx-auto mb-4">
 <Target className="w-6 h-6" />
 </div>
 <h2 className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-widest">Difficulty</h2>
 <span className="text-2xl font-extrabold text-slate-900 block mb-2">{project.difficulty}</span>
 <span className="text-sm font-medium text-slate-500">
 {project.difficulty ==="Easy" ?"Perfect for beginners" : project.difficulty ==="Medium" ?"Some experience needed" :"Advanced contributors"}
 </span>
 </div>
 </div>
 </motion.div>
 )}

 {activeTab ==="diagram" && (
 <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
 <div className="bg-white border border-slate-100 p-8 hover:-hover transition-all">
 <h2 className="text-2xl font-extrabold text-slate-900 mb-8 flex items-center gap-3">
 <Database className="w-6 h-6 text-slate-600" /> Architecture Overview
 </h2>
 {project.mermaid_diagram ? (
 <MermaidDiagram diagram={project.mermaid_diagram} />
 ) : (
 <div className="text-center py-16 bg-slate-50 border border-slate-100">
 <Code2 className="w-12 h-12 mx-auto mb-4 text-slate-300" />
 <p className="text-sm font-bold text-slate-500">Diagram not available</p>
 </div>
 )}
 </div>
 </motion.div>
 )}

 {activeTab ==="issues" && (
 <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
 {(!project.recent_issues || project.recent_issues.length === 0) ? (
 <div className="text-center py-20 bg-white border border-slate-100">
 <div className="w-16 h-16 bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-4">
 <Target className="w-8 h-8" />
 </div>
 <h3 className="text-xl font-extrabold text-slate-900 mb-2">No active issues found</h3>
 <p className="text-slate-500 font-medium">Check GitHub for more issues.</p>
 </div>
 ) : (
 <div className="flex flex-col gap-4">
 {project.recent_issues.map((issue: any) => (
 <motion.div key={issue.number} whileHover={{ y: -4 }}
 onClick={() => router.push(`/project/${owner}/${repo}/issue/${issue.number}`)}
 className="bg-white border border-slate-100 p-6 cursor-pointer hover:-hover transition-all flex flex-col md:flex-row gap-6 items-start group">
 <div className={`flex-shrink-0 w-12 h-12 flex items-center justify-center font-extrabold text-lg border
 ${issue.difficulty === 'Easy' ? 'bg-slate-100 text-slate-700 border-slate-200' : 
 issue.difficulty === 'Medium' ? 'bg-slate-200 text-slate-800 border-slate-300' : 
 'bg-slate-800 text-slate-100 border-slate-700'}`}>
 {issue.difficulty ==="Easy" ?"E" : issue.difficulty ==="Medium" ?"M" :"H"}
 </div>
 <div className="flex-1 min-w-0">
 <div className="flex justify-between items-start mb-2">
 <h4 className="text-lg font-extrabold text-slate-900 group-hover:text-slate-600 transition-colors leading-tight">#{issue.number} {issue.title}</h4>
 </div>
 <p className="text-sm text-slate-500 mb-4 line-clamp-2 leading-relaxed font-medium">{issue.body}</p>
 <div className="flex gap-2 flex-wrap items-center">
 {issue.labels.map((l: string) => (
 <span key={l} className="px-2.5 py-1 bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-600">
 {l}
 </span>
 ))}
 <span className="ml-auto text-xs font-bold text-slate-500 flex items-center gap-1.5 bg-slate-50 px-2.5 py-1 border border-slate-100 group-hover:text-slate-700 group-hover:border-slate-300 transition-colors">
 <MessageCircle className="w-3.5 h-3.5" /> {issue.comments}
 </span>
 </div>
 </div>
 </motion.div>
 ))}
 </div>
 )}
 </motion.div>
 )}
 </div>
 </div>
 );
}
