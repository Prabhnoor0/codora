"use client";

import { useEffect, useState } from"react";
import { useParams } from"next/navigation";
import { motion } from"framer-motion";
import {
 Target, GitBranch, Clock, Zap, ChevronRight,
 CheckCircle, AlertCircle, BookOpen, Code2, ArrowRight, Loader2
} from"lucide-react";
import { issuesApi } from"@/lib/api";

function ReadinessCircle({ score }: { score: number }) {
 const radius = 36;
 const circumference = 2 * Math.PI * radius;
 const offset = circumference - (score / 100) * circumference;
 const color = score >= 70 ?"#22c55e" : score >= 40 ?"#f59e0b" :"#ef4444";

 return (
 <div className="relative w-24 h-24 flex items-center justify-center">
 <svg width="96" height="96" className="readiness-ring">
 <circle cx="48" cy="48" r={radius} fill="none" stroke="#1e293b" strokeWidth="6" />
 <circle
 cx="48" cy="48" r={radius}
 fill="none" stroke={color} strokeWidth="6"
 strokeLinecap="round"
 strokeDasharray={circumference}
 strokeDashoffset={offset}
 style={{ transition:"stroke-dashoffset 1s ease" }}
 />
 </svg>
 <div className="absolute flex flex-col items-center">
 <span className="text-xl font-black" style={{ color }}>{score}</span>
 <span className="text-xs text-slate-500">%</span>
 </div>
 </div>
 );
}

export default function IssuesPage() {
 const params = useParams();
 const owner = params.owner as string;
 const name = params.name as string;

 const [issues, setIssues] = useState<any[]>([]);
 const [loading, setLoading] = useState(true);
 const [selectedIssue, setSelectedIssue] = useState<any>(null);
 const [tutorData, setTutorData] = useState<any>(null);
 const [tutorLoading, setTutorLoading] = useState(false);
 const [filter, setFilter] = useState<"all" |"easy" |"medium" |"hard">("all");

 useEffect(() => {
 issuesApi.getRecommended(owner, name)
 .then(setIssues)
 .catch(console.error)
 .finally(() => setLoading(false));
 }, [owner, name]);

 const loadTutor = async (issue: any) => {
 setSelectedIssue(issue);
 setTutorData(null);
 setTutorLoading(true);
 try {
 const data = await issuesApi.getTutor(owner, name, issue.number);
 setTutorData(data);
 } catch (e) {
 console.error(e);
 } finally {
 setTutorLoading(false);
 }
 };

 const filtered = filter ==="all" ? issues : issues.filter(i => i.difficulty === filter);

 return (
 <div className="min-h-screen p-8 max-w-7xl mx-auto">
 <div className="flex items-center gap-3 mb-8">
 <a href={`/repo/${owner}/${name}`} className="text-slate-500 hover:text-white transition-colors text-sm">
 ← {owner}/{name}
 </a>
 <span className="text-slate-700">/</span>
 <h1 className="text-2xl font-black gradient-text">Recommended Issues</h1>
 </div>

 <div className="grid grid-cols-3 gap-6">
 {/* Issue List */}
 <div className="col-span-2">
 {/* Filters */}
 <div className="flex gap-2 mb-4">
 {(["all","easy","medium","hard"] as const).map(f => (
 <button key={f} onClick={() => setFilter(f)}
 className={`px-4 py-1.5 text-sm font-medium transition-all ${
 filter === f ?"bg-violet-600 text-white" :"btn-ghost py-1.5"
 }`}>
 {f.charAt(0).toUpperCase() + f.slice(1)}
 {f !=="all" && (
 <span className="ml-2 text-xs opacity-70">
 {issues.filter(i => i.difficulty === f).length}
 </span>
 )}
 </button>
 ))}
 </div>

 {loading ? (
 <div className="space-y-4">
 {[1, 2, 3, 4].map(i => <div key={i} className="skeleton h-32" />)}
 </div>
 ) : (
 <div className="space-y-3">
 {filtered.map((issue, i) => (
 <motion.div
 key={issue.id}
 className={`card p-5 cursor-pointer transition-all ${
 selectedIssue?.id === issue.id ?"border-violet-500/50 bg-violet-500/5" :""
 }`}
 initial={{ opacity: 0, y: 10 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: i * 0.05 }}
 onClick={() => loadTutor(issue)}
 >
 <div className="flex items-start gap-4">
 <ReadinessCircle score={Math.round(issue.readiness_score || 50)} />

 <div className="flex-1 min-w-0">
 <div className="flex items-center gap-2 mb-1">
 <span className="text-slate-500 text-sm">#{issue.number}</span>
 <span className={`badge ${
 issue.difficulty ==="easy" ?"badge-green" :
 issue.difficulty ==="medium" ?"badge-amber" :"badge-red"
 }`}>{issue.difficulty}</span>
 </div>
 <h3 className="font-semibold text-sm leading-snug mb-2 line-clamp-2">
 {issue.title}
 </h3>

 {/* Missing skills */}
 {issue.missing_skills && issue.missing_skills.length > 0 && (
 <div className="flex items-center gap-2 flex-wrap">
 <span className="text-xs text-slate-600">Missing:</span>
 {issue.missing_skills.slice(0, 3).map((s: any) => (
 <span key={s.skill || s} className="badge badge-slate">
 {s.skill || s}
 </span>
 ))}
 </div>
 )}
 </div>

 <ChevronRight className={`w-4 h-4 text-slate-600 shrink-0 mt-2 transition-transform ${
 selectedIssue?.id === issue.id ?"rotate-90 text-violet-400" :""
 }`} />
 </div>
 </motion.div>
 ))}
 </div>
 )}
 </div>

 {/* Issue Tutor Panel */}
 <div className="col-span-1">
 {!selectedIssue ? (
 <div className="card p-8 text-center h-64 flex flex-col items-center justify-center">
 <Target className="w-10 h-10 text-slate-700 mb-3" />
 <p className="text-slate-500 text-sm">Select an issue to see your personalized tutor content</p>
 </div>
 ) : (
 <div className="card p-5 sticky top-4 max-h-screen overflow-y-auto">
 <div className="flex items-center gap-2 mb-4">
 <BookOpen className="w-4 h-4 text-violet-400" />
 <span className="font-bold text-sm">Issue Tutor</span>
 <a href={selectedIssue.github_url} target="_blank" rel="noopener noreferrer"
 className="ml-auto text-xs text-slate-500 hover:text-violet-400">
 Open in GitHub →
 </a>
 </div>
 <h3 className="font-semibold text-sm mb-4 text-slate-200">{selectedIssue.title}</h3>

 {tutorLoading ? (
 <div className="flex items-center gap-2 text-slate-400 text-sm py-8 justify-center">
 <Loader2 className="w-4 h-4 animate-spin" />
 Generating tutor content...
 </div>
 ) : tutorData ? (
 <div className="space-y-4">
 {/* Readiness */}
 <div className="flex items-center gap-3 glass p-3">
 <ReadinessCircle score={Math.round(selectedIssue.readiness_score || 50)} />
 <div>
 <p className="text-sm font-semibold">Contribution Readiness</p>
 <p className="text-xs text-slate-500">
 {(selectedIssue.readiness_score || 0) >= 70 ?"Ready to contribute!" :
 (selectedIssue.readiness_score || 0) >= 40 ?"Almost ready — bridge a few gaps" :
"Build prerequisites first"}
 </p>
 </div>
 </div>

 {/* Time estimate */}
 <div className="flex items-center gap-2 text-sm text-slate-400">
 <Clock className="w-4 h-4" />
 Estimated: {tutorData.tutor?.estimated_time ||"1-3 days"}
 </div>

 {/* Files to study */}
 {tutorData.tutor?.files_to_study?.length > 0 && (
 <div>
 <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Files to Study</p>
 <div className="space-y-1.5">
 {tutorData.tutor.files_to_study.slice(0, 4).map((f: any) => (
 <div key={f.path} className="flex items-center gap-2 p-2 bg-slate-800/50 text-xs">
 <Code2 className="w-3 h-3 text-slate-500 shrink-0" />
 <span className="text-slate-300 truncate font-mono">{f.path}</span>
 <span className={`ml-auto badge shrink-0 ${
 f.priority ==="high" ?"badge-red" :"badge-slate"
 }`}>{f.priority}</span>
 </div>
 ))}
 </div>
 </div>
 )}

 {/* Implementation hints */}
 {tutorData.tutor?.implementation_hints?.length > 0 && (
 <div>
 <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Implementation Steps</p>
 <div className="space-y-2">
 {tutorData.tutor.implementation_hints.slice(0, 4).map((hint: string, i: number) => (
 <div key={i} className="flex gap-2 text-xs text-slate-300">
 <span className="gradient-text font-bold shrink-0">{i + 1}.</span>
 {hint}
 </div>
 ))}
 </div>
 </div>
 )}

 {/* Missing skills */}
 {selectedIssue.missing_skills?.length > 0 && (
 <div>
 <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Skill Gaps</p>
 <div className="space-y-2">
 {selectedIssue.missing_skills.slice(0, 3).map((s: any) => (
 <div key={s.skill || s} className="p-2 bg-red-500/10 border border-red-500/20 text-xs">
 <p className="text-red-400 font-semibold">{s.skill || s}</p>
 {s.resource && (
 <a href={s.resource} target="_blank" className="text-slate-500 hover:text-slate-300 mt-0.5 block truncate">
 Learn: {s.resource}
 </a>
 )}
 </div>
 ))}
 </div>
 </div>
 )}
 </div>
 ) : null}
 </div>
 )}
 </div>
 </div>
 </div>
 );
}
