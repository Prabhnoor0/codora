"use client";

import { useState } from"react";
import { useRouter } from"next/navigation";
import { motion } from"framer-motion";
import { ArrowRight, Play, Brain, Search, Zap, Code2, Users, Database } from "lucide-react";
import { useUserStore } from"@/lib/store";

const API = process.env.NEXT_PUBLIC_API_URL ||"http://localhost:8000";

export default function LandingPage() {
 const router = useRouter();
 const { user } = useUserStore();
 const [repoUrl, setRepoUrl] = useState("");

 const handleGithubLogin = () => {
 window.location.href = `${API}/api/auth/github`;
 };

 const handleAnalyze = () => {
 if (!repoUrl) return;
 let owner, repo;
 try {
 const parts = repoUrl.replace("https://github.com/","").split("/");
 owner = parts[0];
 repo = parts[1];
 if (!owner || !repo) throw new Error();
 } catch {
 alert("Please enter a valid GitHub repository URL (e.g., https://github.com/facebook/react)");
 return;
 }
 router.push(`/repo/${owner}/${repo}/intel`);
 };

 return (
 <div className="min-h-screen bg-slate-50 font-sans selection:bg-slate-800 selection:text-white flex flex-col relative overflow-hidden">
 
 {/* Background Blur Orbs */}
 <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-slate-300 mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-slow" />
 <div className="absolute top-20 right-1/4 w-[400px] h-[400px] bg-slate-200 mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-slow" style={{ animationDelay: '2s' }} />

 {/* Navbar */}
 <nav className="relative z-50 flex items-center justify-between px-6 sm:px-12 py-6">
 <div className="flex items-center gap-2 font-extrabold text-xl tracking-tight text-slate-900">
 <div className="w-8 h-8 bg-slate-900 flex items-center justify-center text-white">
 <Brain className="w-4 h-4" />
 </div>
 <span>Codora</span>
 </div>
 <div className="flex items-center gap-8">
 <div className="hidden md:flex items-center gap-6">
 <a href="#" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Product</a>
 <a href="#" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Features</a>
 <a href="#" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Pricing</a>
 </div>
 {user ? (
 <button onClick={() => router.push("/explore")} className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold hover:-translate-y-0.5 transition-all duration-200">
 Dashboard
 </button>
 ) : (
 <button onClick={handleGithubLogin} className="px-6 py-2.5 bg-white text-slate-900 text-sm font-semibold border border-slate-200 hover:-hover hover:-translate-y-0.5 transition-all duration-200">
 Sign In
 </button>
 )}
 </div>
 </nav>

 {/* Hero Section */}
 <main className="flex-1 flex flex-col items-center text-center px-4 sm:px-6 pt-20 lg:pt-32 pb-24 relative z-10">
 <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="w-full max-w-5xl flex flex-col items-center">
 
 <div className="mb-8 px-4 py-1.5 bg-slate-100 border border-slate-200 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-700">
 <Zap className="w-3.5 h-3.5 text-slate-500" />
 AI-Powered Open Source Mentorship
 </div>

 <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6 text-slate-900">
 Understand any <br className="hidden sm:block" />
 <span className="text-gradient">codebase instantly</span>
 </h1>

 <p className="text-lg sm:text-xl text-slate-500 max-w-2xl mb-6 leading-relaxed font-medium">
 Stop staring at 500,000 lines of code. AI analyzes repositories, builds your knowledge graph, and guides you to your first contribution.
 </p>

 <p className="text-sm font-medium text-slate-400 mb-12">
 <span className="font-semibold text-slate-700">GitHub</span> + <span className="font-semibold text-slate-700">Coursera</span> + <span className="font-semibold text-slate-700">Duolingo</span> + <span className="font-semibold text-slate-700">Copilot</span> — in one platform.
 </p>

 <div className="flex flex-col sm:flex-row items-center gap-4 mb-20 w-full sm:w-auto">
 <button onClick={handleGithubLogin} className="group flex items-center justify-center gap-2 w-full sm:w-auto px-8 py-4 bg-slate-900 text-white font-bold hover:shadow-[0_8px_25px_0_rgba(15,23,42,0.3)] hover:bg-slate-800 hover:-translate-y-1 transition-all duration-200">
 <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
 <span>Get Started with GitHub</span>
 <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
 </button>
 <button className="flex items-center justify-center gap-2 w-full sm:w-auto px-8 py-4 bg-white text-slate-700 font-bold border border-slate-200 hover:-hover hover:-translate-y-1 transition-all duration-200">
 <span>See how it works</span>
 <Play className="w-4 h-4 text-slate-700" />
 </button>
 </div>

 {/* Search Box - Isometric Depth */}
 <div className="w-full max-w-3xl perspective-[2000px]">
 <div className="bg-white/80 backdrop-blur-xl border border-slate-200 p-8 hover:-hover hover:rotate-x-[2deg] hover:rotate-y-[-2deg] transition-all duration-500 text-left">
 <label className="block text-sm font-semibold text-slate-700 mb-3">Try it with any repository:</label>
 <div className="flex flex-col sm:flex-row gap-3">
 <div className="relative flex-1">
 <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
 <Search className="h-5 w-5 text-slate-400" />
 </div>
 <input
 type="text"
 placeholder="https://github.com/kubernetes/kubernetes"
 value={repoUrl}
 onChange={(e) => setRepoUrl(e.target.value)}
 className="block w-full pl-12 pr-4 py-4 border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-500/20 text-base transition-all"
 />
 </div>
 <button 
 onClick={handleAnalyze} 
 className="px-8 py-4 bg-slate-900 text-white font-bold hover:bg-slate-700 transition-colors flex items-center justify-center gap-2 whitespace-nowrap group"
 >
 Analyze <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
 </button>
 </div>
 </div>
 </div>
 </motion.div>

 {/* Stats Section */}
 <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="w-full max-w-5xl mt-24 grid grid-cols-1 md:grid-cols-3 gap-6">
 <div className="p-8 bg-white border border-slate-100 hover:-hover hover:-translate-y-1 transition-all duration-300">
 <div className="w-12 h-12 bg-slate-100 text-slate-700 flex items-center justify-center mb-6 mx-auto">
 <Code2 className="w-6 h-6" />
 </div>
 <p className="text-4xl font-extrabold text-slate-900 mb-2">500K+</p>
 <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Lines of code explained</p>
 </div>
 <div className="p-8 bg-white border border-slate-100 hover:-hover hover:-translate-y-1 transition-all duration-300 transform md:scale-105 border-t-4 border-t-slate-800">
 <div className="w-12 h-12 bg-slate-100 text-slate-700 flex items-center justify-center mb-6 mx-auto">
 <Users className="w-6 h-6" />
 </div>
 <p className="text-4xl font-extrabold text-slate-900 mb-2">15+</p>
 <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">AI agents working for you</p>
 </div>
 <div className="p-8 bg-white border border-slate-100 hover:-hover hover:-translate-y-1 transition-all duration-300">
 <div className="w-12 h-12 bg-slate-100 text-slate-700 flex items-center justify-center mb-6 mx-auto">
 <Database className="w-6 h-6" />
 </div>
 <p className="text-4xl font-extrabold text-slate-900 mb-2">3 DBs</p>
 <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Postgres + Neo4j + Qdrant</p>
 </div>
 </motion.div>

 </main>
 </div>
 );
}
