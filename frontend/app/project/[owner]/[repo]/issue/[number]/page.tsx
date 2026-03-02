"use client";
import { useState, useEffect } from"react";
import { useParams, useRouter } from"next/navigation";
import { useUserStore, useChatbotStore } from "@/lib/store";
import { motion } from"framer-motion";
import { ArrowLeft, Clock, MessageSquare, AlertCircle, Play, CheckCircle2, FileText, Bot, Github, Zap } from"lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ||"http://localhost:8000";

export default function IssueDetailPage() {
 const params = useParams();
 const router = useRouter();
  const { user, token } = useUserStore();
  const { setIsOpen } = useChatbotStore();
 const owner = params.owner as string;
 const repo = params.repo as string;
 const issueNumber = params.number as string;

 const [issue, setIssue] = useState<any>(null);
 const [loading, setLoading] = useState(true);
 const [activeTab, setActiveTab] = useState("guide");

 useEffect(() => {
 if (!user) { router.push("/"); return; }
 if (!owner || !repo || !issueNumber) return;

 fetch(`${API}/api/discover/projects/${owner}/${repo}/issues/${issueNumber}`, {
 headers: { Authorization: `Bearer ${token}` }
 })
 .then(res => res.json())
 .then(data => {
 setIssue(data);
 })
 .catch(err => {
 console.error("Failed to fetch issue", err);
 })
 .finally(() => {
 setLoading(false);
 });
 }, [user, token, owner, repo, issueNumber, router]);

 if (loading) return (
 <div className="min-h-screen bg-slate-50 flex items-center justify-center">
 <div className="text-center">
 <div className="w-12 h-12 border-4 border-slate-200 border-t-slate-800 animate-spin mx-auto mb-4" />
 <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Analyzing Issue</p>
 </div>
 </div>
 );

 if (!issue) return (
 <div className="min-h-screen bg-slate-50 flex items-center justify-center text-center">
 <div className="bg-white p-12 border border-slate-100 max-w-md w-full mx-4">
 <div className="w-16 h-16 bg-slate-100 text-slate-600 flex items-center justify-center mx-auto mb-6">
 <AlertCircle className="w-8 h-8" />
 </div>
 <h2 className="font-extrabold text-2xl text-slate-900 mb-3">Issue not found</h2>
 <p className="text-slate-500 font-medium mb-8">We couldn't locate this issue.</p>
 <button onClick={() => router.back()} className="w-full px-6 py-3 bg-slate-900 text-white font-bold hover:bg-slate-800 transition-colors">
 Go Back
 </button>
 </div>
 </div>
 );

 return (
 <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-24 selection:bg-slate-800 selection:text-white relative overflow-hidden">
 
 {/* Background Orbs */}
 <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-slate-200 mix-blend-multiply filter blur-[100px] opacity-40 pointer-events-none" />

 {/* Navbar */}
 <nav className="bg-white/80 backdrop-blur-xl border-b border-slate-200 h-16 flex items-center px-6 sm:px-12 sticky top-0 z-50">
 <button onClick={() => router.back()} className="flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-900 transition-colors bg-white hover:bg-slate-100 px-4 py-2 border border-transparent hover:border-slate-200">
 <ArrowLeft className="w-4 h-4" /> Back to Project
 </button>
 </nav>

 <div className="max-w-6xl mx-auto px-6 sm:px-12 py-10 relative z-10">
 {/* Header */}
 <div className="bg-white border border-slate-100 p-8 sm:p-10 mb-8">
 <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
 <div className="flex items-center gap-3">
 <span className={`px-3 py-1 text-xs font-bold border ${
 issue.difficulty === 'Easy' ? 'bg-slate-100 text-slate-700 border-slate-200' : 
 issue.difficulty === 'Medium' ? 'bg-slate-200 text-slate-800 border-slate-300' : 
 'bg-slate-800 text-slate-100 border-slate-700'
 }`}>
 {issue.difficulty}
 </span>
 <span className="flex items-center gap-1.5 text-sm font-bold text-slate-500 bg-slate-50 px-3 py-1 border border-slate-100">
 <Clock className="w-4 h-4" /> {issue.estimated_time}
 </span>
 </div>
 <span className="px-3 py-1 bg-slate-100 text-slate-700 text-xs font-extrabold uppercase tracking-wider">
 {issue.state}
 </span>
 </div>
 
 <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 mb-6 leading-[1.1] tracking-tight">
 <span className="text-slate-400">#{issue.number}</span> {issue.title}
 </h1>

 <div className="flex flex-wrap items-center gap-2 mb-8">
 {issue.labels?.map((label: string) => (
 <span key={label} className="px-3 py-1.5 bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-600">
 {label}
 </span>
 ))}
 </div>

 <div className="flex flex-col sm:flex-row gap-4 border-t border-slate-100 pt-8">
 <a href={issue.html_url} target="_blank" rel="noopener noreferrer" 
 className="flex items-center justify-center gap-2 px-8 py-3.5 bg-slate-900 text-white font-bold hover:bg-slate-800 transition-colors hover:-translate-y-0.5 hover:-hover">
 <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
 View on GitHub
 </a>
 <button onClick={() => setIsOpen(true)} className="flex items-center justify-center gap-2 px-8 py-3.5 bg-slate-900 text-white font-bold hover:shadow-[0_8px_25px_0_rgba(15,23,42,0.3)] hover:bg-slate-800 hover:-translate-y-0.5 transition-all">
 <Bot className="w-5 h-5" /> Ask AI Mentor
 </button>
 </div>
 </div>

 {/* Content Layout */}
 <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
 <div className="lg:col-span-2 flex flex-col gap-8">
 
 {/* Tabs */}
 <div className="flex gap-8 border-b border-slate-200">
 <button 
 onClick={() => setActiveTab("guide")}
 className={`pb-4 text-sm font-bold border-b-2 transition-all ${activeTab ==="guide" ?"border-slate-900 text-slate-900" :"border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"}`}
 >
 Implementation Guide
 </button>
 <button 
 onClick={() => setActiveTab("description")}
 className={`pb-4 text-sm font-bold border-b-2 transition-all ${activeTab ==="description" ?"border-slate-900 text-slate-900" :"border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"}`}
 >
 Original Issue
 </button>
 </div>

 {/* Tab Content */}
 {activeTab ==="guide" && (
 <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-6">
 
 {/* Prerequisites */}
 {issue.prerequisites?.length > 0 && (
 <div className="bg-white border border-slate-100 p-8">
 <h3 className="text-xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
 <CheckCircle2 className="w-6 h-6 text-slate-700" /> Prerequisites
 </h3>
 <ul className="list-disc list-inside space-y-3 text-sm text-slate-600 font-medium">
 {issue.prerequisites.map((p: string, i: number) => (
 <li key={i}>{p}</li>
 ))}
 </ul>
 </div>
 )}

 {/* Steps */}
 {issue.implementation_steps?.map((step: any, idx: number) => (
 <div key={idx} className="bg-white border border-slate-100 p-8 hover:-hover transition-all flex flex-col sm:flex-row gap-6">
 <div className="w-12 h-12 flex-shrink-0 bg-slate-100 text-slate-700 font-extrabold text-lg flex items-center justify-center">
 {idx + 1}
 </div>
 <div>
 <h4 className="text-lg font-extrabold text-slate-900 mb-3">{step.title}</h4>
 <p className="text-sm text-slate-600 mb-5 leading-relaxed font-medium">{step.description}</p>
 {step.files?.length > 0 && (
 <div className="flex flex-wrap gap-2 mb-5">
 {step.files.map((f: string) => (
 <span key={f} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 border border-slate-200 text-xs font-mono font-semibold text-slate-600">
 <FileText className="w-3.5 h-3.5" /> {f}
 </span>
 ))}
 </div>
 )}
 {step.tip && (
 <div className="bg-slate-100 border border-slate-200 p-4 text-xs text-slate-900 font-medium flex items-start gap-3">
 <Zap className="w-4 h-4 text-slate-600 flex-shrink-0 mt-0.5" />
 <div><span className="font-extrabold text-slate-800 mr-1">TIP:</span> {step.tip}</div>
 </div>
 )}
 </div>
 </div>
 ))}
 </motion.div>
 )}

 {activeTab ==="description" && (
 <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white border border-slate-100 p-10">
 <div className="prose prose-slate max-w-none prose-p:font-medium prose-p:leading-relaxed">
 <p className="whitespace-pre-wrap">{issue.body}</p>
 </div>
 </motion.div>
 )}
 
 </div>

 {/* Right Sidebar */}
 <div className="flex flex-col gap-6">
 <div className="bg-white border border-slate-100 p-8">
 <h3 className="text-xs font-bold text-slate-400 mb-6 uppercase tracking-widest">Required Skills</h3>
 <div className="flex flex-col gap-5">
 {issue.required_skills?.map((skill: any, i: number) => (
 <div key={i} className="flex flex-col gap-2">
 <div className="flex justify-between items-end text-xs font-bold text-slate-700">
 <span>{skill.name}</span>
 <span className="text-slate-400 text-[10px] uppercase">{skill.level}</span>
 </div>
 <div className="h-2 w-full bg-slate-100 border border-slate-200/50 overflow-hidden">
 <div className={`h-full transition-all duration-700 ${
 skill.level === 'Beginner' ? 'w-1/3 bg-slate-600' : 
 skill.level === 'Intermediate' ? 'w-2/3 bg-slate-700' : 'w-full bg-slate-800'
 }`} />
 </div>
 </div>
 ))}
 </div>
 </div>

 {issue.recent_comments?.length > 0 && (
 <div className="bg-white border border-slate-100 p-8">
 <h3 className="text-xs font-bold text-slate-400 mb-6 uppercase tracking-widest">Recent Activity</h3>
 <div className="flex flex-col gap-6">
 {issue.recent_comments.map((comment: any, i: number) => (
 <div key={i} className="flex gap-4 text-sm">
 <div className="w-8 h-8 bg-slate-100 flex items-center justify-center flex-shrink-0 text-slate-600">
 <MessageSquare className="w-4 h-4" />
 </div>
 <div>
 <div className="font-extrabold text-slate-900 mb-1">{comment.author}</div>
 <div className="text-slate-500 font-medium line-clamp-3 leading-relaxed">{comment.body}</div>
 </div>
 </div>
 ))}
 </div>
 </div>
 )}
 </div>
 </div>
 </div>
 </div>
 );
}
