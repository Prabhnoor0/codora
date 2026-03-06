"use client";

import { useState } from"react";
import { motion } from"framer-motion";
import {
 GitPullRequest, Shield, Zap, AlertTriangle,
 CheckCircle, XCircle, Info, Loader2, Star
} from"lucide-react";
import { prApi } from"@/lib/api";

type Severity ="critical" |"major" |"minor";

const SEVERITY_COLOR: Record<Severity, string> = {
 critical:"badge-red",
 major:"badge-amber",
 minor:"badge-slate",
};

const SEVERITY_ICON: Record<Severity, any> = {
 critical: XCircle,
 major: AlertTriangle,
 minor: Info,
};

function IssueList({ title, issues, icon: Icon, color }: { title: string; issues: any[]; icon: any; color: string }) {
 if (!issues?.length) return null;
 return (
 <div>
 <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
 <Icon className={`w-4 h-4 ${color}`} />
 {title} ({issues.length})
 </h3>
 <div className="space-y-3">
 {issues.map((issue, i) => {
 const SevIcon = SEVERITY_ICON[issue.severity as Severity] || Info;
 return (
 <div key={i} className="card p-4">
 <div className="flex items-start gap-3">
 <SevIcon className={`w-4 h-4 mt-0.5 shrink-0 ${
 issue.severity ==="critical" ?"text-red-400" :
 issue.severity ==="major" ?"text-amber-400" :"text-slate-400"
 }`} />
 <div className="flex-1">
 <div className="flex items-center gap-2 mb-1">
 <span className={`badge ${SEVERITY_COLOR[issue.severity as Severity] ||"badge-slate"}`}>
 {issue.severity}
 </span>
 {issue.file && (
 <span className="text-xs font-mono text-slate-500">{issue.file}{issue.line ? `:${issue.line}` :""}</span>
 )}
 </div>
 <p className="text-sm text-slate-200">{issue.description}</p>
 {issue.suggestion && (
 <p className="text-xs text-violet-400 mt-2 leading-relaxed">
  {issue.suggestion}
 </p>
 )}
 </div>
 </div>
 </div>
 );
 })}
 </div>
 </div>
 );
}

export default function PRReviewPage() {
 const [repoFullName, setRepoFullName] = useState("");
 const [prNumber, setPrNumber] = useState("");
 const [loading, setLoading] = useState(false);
 const [review, setReview] = useState<any>(null);

 const handleReview = async () => {
 if (!repoFullName.trim() || !prNumber.trim()) return;
 setLoading(true);
 setReview(null);
 try {
 const res = await prApi.review(repoFullName, parseInt(prNumber));
 setReview(res.review);
 } catch (e) {
 console.error(e);
 } finally {
 setLoading(false);
 }
 };

 const totalIssues = review ? (
 (review.bugs?.length || 0) +
 (review.security_issues?.length || 0) +
 (review.performance_issues?.length || 0) +
 (review.style_issues?.length || 0)
 ) : 0;

 return (
 <div className="min-h-screen p-8 max-w-5xl mx-auto">
 <div className="flex items-center gap-3 mb-8">
 <GitPullRequest className="w-6 h-6 text-violet-400" />
 <h1 className="text-3xl font-black gradient-text">AI PR Reviewer</h1>
 </div>

 {/* Input Form */}
 <motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 className="card-elevated p-6 mb-8"
 >
 <h2 className="font-bold mb-4">Review a Pull Request</h2>
 <div className="flex gap-4">
 <div className="flex-1">
 <label className="text-xs text-slate-400 mb-1.5 block">Repository (owner/name)</label>
 <input
 type="text"
 value={repoFullName}
 onChange={e => setRepoFullName(e.target.value)}
 placeholder="facebook/react"
 className="input-dark"
 />
 </div>
 <div className="w-36">
 <label className="text-xs text-slate-400 mb-1.5 block">PR Number</label>
 <input
 type="number"
 value={prNumber}
 onChange={e => setPrNumber(e.target.value)}
 placeholder="1234"
 className="input-dark"
 />
 </div>
 <div className="flex items-end">
 <button
 onClick={handleReview}
 disabled={loading || !repoFullName || !prNumber}
 className="btn-primary disabled:opacity-40"
 >
 {loading ? (
 <><Loader2 className="w-4 h-4 animate-spin" /> Reviewing...</>
 ) : (
 <><GitPullRequest className="w-4 h-4" /> Review PR</>
 )}
 </button>
 </div>
 </div>
 </motion.div>

 {/* Review Results */}
 {review && (
 <motion.div
 initial={{ opacity: 0, y: 20 }}
 animate={{ opacity: 1, y: 0 }}
 className="space-y-6"
 >
 {/* Overview */}
 <div className="card-elevated p-6">
 <div className="flex items-start gap-6">
 {/* Quality Score */}
 <div className="text-center">
 <div className="relative w-24 h-24">
 <svg width="96" height="96" className="readiness-ring">
 <circle cx="48" cy="48" r="36" fill="none" stroke="#1e293b" strokeWidth="6" />
 <circle
 cx="48" cy="48" r="36"
 fill="none"
 stroke={review.quality_score >= 70 ?"#22c55e" : review.quality_score >= 40 ?"#f59e0b" :"#ef4444"}
 strokeWidth="6"
 strokeLinecap="round"
 strokeDasharray={226}
 strokeDashoffset={226 - (review.quality_score / 100) * 226}
 />
 </svg>
 <div className="absolute inset-0 flex flex-col items-center justify-center">
 <span className="text-xl font-black">{review.quality_score}</span>
 <span className="text-xs text-slate-500">/ 100</span>
 </div>
 </div>
 <p className="text-xs text-slate-400 mt-2">Quality Score</p>
 </div>

 <div className="flex-1">
 <div className="flex items-center gap-2 mb-2">
 <h2 className="font-bold text-xl">Review Summary</h2>
 {review.approved ? (
 <span className="badge badge-green"><CheckCircle className="w-3 h-3" /> Approved</span>
 ) : (
 <span className="badge badge-red"><XCircle className="w-3 h-3" /> Changes Requested</span>
 )}
 </div>
 <p className="text-slate-300 leading-relaxed">{review.overall_assessment}</p>

 <div className="flex gap-4 mt-4">
 <span className="text-sm text-red-400">{review.bugs?.length || 0} bugs</span>
 <span className="text-sm text-orange-400">{review.security_issues?.length || 0} security</span>
 <span className="text-sm text-yellow-400">{review.performance_issues?.length || 0} performance</span>
 <span className="text-sm text-slate-400">{review.style_issues?.length || 0} style</span>
 </div>
 </div>
 </div>
 </div>

 {/* Positive Aspects */}
 {review.positive_aspects?.length > 0 && (
 <div className="card p-5">
 <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
 <CheckCircle className="w-4 h-4 text-green-400" />
 What's Good
 </h3>
 <ul className="space-y-1.5">
 {review.positive_aspects.map((p: string, i: number) => (
 <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
 <span className="text-green-400 mt-0.5"></span>
 {p}
 </li>
 ))}
 </ul>
 </div>
 )}

 <IssueList title="Bugs Found" issues={review.bugs || []} icon={XCircle} color="text-red-400" />
 <IssueList title="Security Issues" issues={review.security_issues || []} icon={Shield} color="text-orange-400" />
 <IssueList title="Performance Issues" issues={review.performance_issues || []} icon={Zap} color="text-yellow-400" />
 <IssueList title="Style Issues" issues={review.style_issues || []} icon={Info} color="text-slate-400" />

 {/* Final message */}
 {review.summary_for_developer && (
 <div className="glass-strong p-5 border-violet-500/20">
 <p className="text-sm text-slate-300 leading-relaxed">
  <span className="text-violet-400 font-semibold">Mentor says: </span>
 {review.summary_for_developer}
 </p>
 </div>
 )}
 </motion.div>
 )}
 </div>
 );
}
