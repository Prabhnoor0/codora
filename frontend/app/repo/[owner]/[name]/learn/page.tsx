"use client";

import { useEffect, useState } from"react";
import { useParams } from"next/navigation";
import { motion } from"framer-motion";
import {
 BookOpen, CheckCircle2, Circle, Lock,
 Target, Clock, Star, Flame, ArrowRight,
 FileText, Code2, ExternalLink
} from"lucide-react";
import { repoApi, userApi } from"@/lib/api";

export default function LearnPage() {
 const params = useParams();
 const owner = params.owner as string;
 const name = params.name as string;

 const [learningPath, setLearningPath] = useState<any>(null);
 const [loading, setLoading] = useState(false);
 const [generating, setGenerating] = useState(false);
 const [completedDays, setCompletedDays] = useState<Set<number>>(new Set());
 const [activeDay, setActiveDay] = useState<number | null>(null);

 const generatePath = async () => {
 setGenerating(true);
 try {
 const res = await repoApi.generateLearningPath(owner, name);
 setLearningPath(res.plan);
 } catch (e) {
 console.error(e);
 } finally {
 setGenerating(false);
 }
 };

 const markComplete = async (day: number, topic: string) => {
 setCompletedDays(prev => new Set([...prev, day]));
 try {
 await userApi.updateProgress(learningPath?.learning_path_id ||"", day, topic);
 } catch (e) {}
 };

 const plan = learningPath?.plan || [];
 const totalXP = plan.reduce((acc: number, d: any) => acc + (d.xp_reward || 100), 0);
 const earnedXP = [...completedDays].reduce((acc, day) => {
 const d = plan.find((p: any) => p.day === day);
 return acc + (d?.xp_reward || 100);
 }, 0);

 return (
 <div className="min-h-screen p-8 max-w-5xl mx-auto">
 <div className="flex items-center gap-3 mb-6">
 <a href={`/repo/${owner}/${name}`} className="text-slate-500 hover:text-white transition-colors text-sm">
 ← {owner}/{name}
 </a>
 <span className="text-slate-700">/</span>
 <h1 className="text-2xl font-black gradient-text">Learning Roadmap</h1>
 </div>

 {!learningPath ? (
 <motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 className="flex flex-col items-center justify-center py-20 gap-6"
 >
 <div className="w-20 h-20 bg-gradient-to-br from-violet-500/20 to-indigo-500/20 border border-violet-500/30 flex items-center justify-center">
 <BookOpen className="w-10 h-10 text-violet-400 animate-float" />
 </div>
 <div className="text-center">
 <h2 className="text-2xl font-black mb-2">Generate Your Learning Path</h2>
 <p className="text-slate-400 max-w-md">
 AI will create a personalized day-by-day roadmap for <span className="text-violet-400">{name}</span>,
 adapted to your skill level.
 </p>
 </div>
 <button onClick={generatePath} disabled={generating} className="btn-primary px-8 py-4 text-base">
 {generating ? (
 <>
 <div className="w-4 h-4 border-2 border-white/30 border-t-white animate-spin" />
 Generating your path...
 </>
 ) : (
 <>
 <Star className="w-5 h-5" />
 Generate Learning Path
 <ArrowRight className="w-4 h-4" />
 </>
 )}
 </button>
 </motion.div>
 ) : (
 <div className="space-y-6">
 {/* Progress Header */}
 <div className="card p-6">
 <div className="flex items-center gap-6">
 <div className="flex-1">
 <h2 className="font-bold text-xl mb-1">{learningPath.title || `Learning ${name}`}</h2>
 <p className="text-slate-400 text-sm">{learningPath.description}</p>
 </div>
 <div className="flex items-center gap-6">
 <div className="text-center">
 <div className="text-2xl font-black text-yellow-400">{earnedXP}</div>
 <div className="text-xs text-slate-500">/ {totalXP} XP</div>
 </div>
 <div className="text-center">
 <div className="text-2xl font-black gradient-text">{completedDays.size}</div>
 <div className="text-xs text-slate-500">/ {plan.length} days</div>
 </div>
 <div className="text-center">
 <div className="text-2xl font-black text-orange-400 flex items-center gap-1">
 <Flame className="w-5 h-5" /> {completedDays.size}
 </div>
 <div className="text-xs text-slate-500">day streak</div>
 </div>
 </div>
 </div>
 <div className="progress-bar mt-4">
 <div className="progress-fill" style={{ width: `${(completedDays.size / plan.length) * 100}%` }} />
 </div>
 </div>

 {/* Roadmap */}
 <div className="pl-4">
 {plan.map((day: any, i: number) => {
 const isCompleted = completedDays.has(day.day);
 const isActive = activeDay === day.day;
 const isLocked = day.day > 1 && !completedDays.has(day.day - 1) && !isCompleted;

 return (
 <motion.div
 key={day.day}
 className={`roadmap-day mb-6 ${isCompleted ?"completed" : isActive ?"active" :""}`}
 initial={{ opacity: 0, x: -10 }}
 animate={{ opacity: 1, x: 0 }}
 transition={{ delay: i * 0.05 }}
 >
 <div className="roadmap-dot" />
 <div
 className={`card p-5 cursor-pointer ml-2 ${isLocked ?"opacity-40" :""}`}
 onClick={() => !isLocked && setActiveDay(isActive ? null : day.day)}
 >
 <div className="flex items-center gap-4">
 <div className={`w-10 h-10 flex items-center justify-center shrink-0 ${
 isCompleted ?"bg-green-500/20 border border-green-500/30" :
 isActive ?"bg-violet-500/20 border border-violet-500/30" :
 isLocked ?"bg-slate-800 border border-slate-700" :
"bg-slate-800/50 border border-slate-700/50"
 }`}>
 {isLocked ? <Lock className="w-4 h-4 text-slate-600" /> :
 isCompleted ? <CheckCircle2 className="w-4 h-4 text-green-400" /> :
 <span className="text-sm font-black gradient-text">{day.day}</span>}
 </div>
 <div className="flex-1">
 <div className="flex items-center gap-2">
 <h3 className="font-bold">{day.title}</h3>
 {isCompleted && <span className="badge badge-green">Completed</span>}
 </div>
 <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
 <span className="flex items-center gap-1">
 <Clock className="w-3 h-3" /> Day {day.day}
 </span>
 <span className="flex items-center gap-1">
 <Star className="w-3 h-3 text-yellow-500" /> +{day.xp_reward || 100} XP
 </span>
 </div>
 </div>
 {!isLocked && !isCompleted && (
 <button
 onClick={(e) => { e.stopPropagation(); markComplete(day.day, day.title); }}
 className="btn-ghost text-sm py-2 px-3 shrink-0"
 >
 Complete
 </button>
 )}
 </div>

 {/* Expanded content */}
 {isActive && (
 <motion.div
 initial={{ opacity: 0, height: 0 }}
 animate={{ opacity: 1, height:"auto" }}
 className="mt-5 pt-4 border-t border-slate-800 space-y-4"
 >
 {/* Objectives */}
 <div>
 <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Objectives</p>
 <ul className="space-y-1.5">
 {(day.objectives || []).map((obj: string) => (
 <li key={obj} className="flex items-start gap-2 text-sm text-slate-300">
 <Target className="w-4 h-4 text-violet-400 mt-0.5 shrink-0" />
 {obj}
 </li>
 ))}
 </ul>
 </div>

 {/* Files to read */}
 {day.files_to_read?.length > 0 && (
 <div>
 <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Files to Read</p>
 <div className="flex flex-wrap gap-2">
 {day.files_to_read.map((f: string) => (
 <span key={f} className="flex items-center gap-1 text-xs font-mono bg-slate-800 text-slate-300 px-3 py-1">
 <Code2 className="w-3 h-3 text-slate-500" />
 {f}
 </span>
 ))}
 </div>
 </div>
 )}

 {/* Resources */}
 {day.resources?.length > 0 && (
 <div>
 <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Resources</p>
 <div className="space-y-2">
 {day.resources.map((r: any) => (
 <a key={r.url} href={r.url} target="_blank" rel="noopener noreferrer"
 className="flex items-center gap-2 text-sm text-slate-300 hover:text-violet-400 transition-colors group">
 <ExternalLink className="w-3 h-3 text-slate-600 group-hover:text-violet-400" />
 {r.title}
 {r.duration && <span className="text-xs text-slate-600 ml-auto">{r.duration}</span>}
 </a>
 ))}
 </div>
 </div>
 )}
 </motion.div>
 )}
 </div>
 </motion.div>
 );
 })}
 </div>
 </div>
 )}
 </div>
 );
}
