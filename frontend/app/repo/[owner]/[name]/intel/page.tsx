"use client";
import { useState, useEffect, useRef } from"react";
import { useParams, useRouter } from"next/navigation";
import { useUserStore } from"@/lib/store";
import { motion, AnimatePresence } from"framer-motion";
import {
 Brain, Code2, GitFork, GitMerge, FileText,
 MessageSquare, Send, ChevronRight, CheckCircle2,
 AlertTriangle, ArrowLeft, Lightbulb, Zap, Database
} from"lucide-react";
import ReactMarkdown from"react-markdown";

const API = process.env.NEXT_PUBLIC_API_URL ||"http://localhost:8000";

function MermaidDiagram({ diagram }: { diagram: string }) {
 const [svg, setSvg] = useState<string>("");

 useEffect(() => {
 if (!diagram) return;
 import("mermaid").then(({ default: mermaid }) => {
 mermaid.initialize({ startOnLoad: false, theme:"base", themeVariables: {
 primaryColor:"#ffffff", primaryBorderColor:"#e2e8f0",
 lineColor:"#4f46e5", fontSize:"14px", textColor:"#0f172a"
 }});
 const id ="mermaid-" + Math.random().toString(36).slice(2);
 mermaid.render(id, diagram).then(({ svg: rendered }) => setSvg(rendered)).catch(() => {});
 });
 }, [diagram]);

 if (!svg) return <div className="p-12 text-center text-sm font-semibold text-slate-400 bg-slate-50 border border-slate-100">Loading diagram architecture...</div>;
 return <div dangerouslySetInnerHTML={{ __html: svg }} className="text-center overflow-x-auto bg-white p-8 border border-slate-100" />;
}

export default function DeepIntelPage() {
 const params = useParams();
 const router = useRouter();
 const { user, token } = useUserStore();
 const owner = params.owner as string;
 const name = params.name as string;

 const [project, setProject] = useState<any>(null);
 const [walkthrough, setWalkthrough] = useState<any>(null);
 const [activeTab, setActiveTab] = useState("overview");
 const [loading, setLoading] = useState(true);
 
 // Chat State
 const [messages, setMessages] = useState<{role: string, content: string}[]>([
 { role:"assistant", content: `I'm your **AI Mentor** for \`${owner}/${name}\`. I've deeply analyzed the architecture, dependencies, and subsystems. What would you like to explore?` }
 ]);
 const [input, setInput] = useState("");
 const [chatLoading, setChatLoading] = useState(false);
 const chatRef = useRef<HTMLDivElement>(null);

 useEffect(() => {
 if (!user) { router.push("/"); return; }
 if (!owner || !name) return;

 Promise.all([
 fetch(`${API}/api/discover/projects/${owner}/${name}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
 fetch(`${API}/api/discover/projects/${owner}/${name}/walkthrough`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()).catch(() => null)
 ]).then(([projData, walkData]) => {
 setProject(projData);
 setWalkthrough(walkData);
 setLoading(false);
 });
 }, [user, token, owner, name, router]);

 useEffect(() => {
 if (chatRef.current) {
 chatRef.current.scrollTop = chatRef.current.scrollHeight;
 }
 }, [messages]);

 const sendMessage = async () => {
 if (!input.trim() || chatLoading) return;
 const userMsg = input.trim();
 setInput("");
 setMessages(prev => [...prev, { role:"user", content: userMsg }]);
 setChatLoading(true);

 try {
 const res = await fetch(`${API}/api/discover/projects/${owner}/${name}/chat`, {
 method:"POST",
 headers: {"Content-Type":"application/json", Authorization: `Bearer ${token}` },
 body: JSON.stringify({ message: userMsg, history: messages })
 });
 const data = await res.json();
 setMessages(prev => [...prev, { role:"assistant", content: data.reply ||"I encountered an error analyzing the codebase." }]);
 } catch (e) {
 setMessages(prev => [...prev, { role:"assistant", content:"Sorry, I couldn't connect to the AI engine." }]);
 } finally {
 setChatLoading(false);
 }
 };

 if (loading) return (
 <div className="min-h-screen bg-slate-50 flex items-center justify-center">
 <div className="text-center">
 <div className="w-16 h-16 bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-6 animate-pulse-slow">
 <Brain className="w-8 h-8" />
 </div>
 <p className="text-sm font-extrabold text-indigo-600 uppercase tracking-widest">Compiling Intelligence...</p>
 </div>
 </div>
 );

 const TABS = [
 { id:"overview", label:"System Map", icon: Database },
 { id:"walkthrough", label:"Walkthrough", icon: GitMerge },
 { id:"subsystems", label:"Subsystems", icon: Code2 },
 ];

 return (
 <div className="h-screen bg-slate-50 text-slate-900 font-sans flex flex-col overflow-hidden selection:bg-indigo-500 selection:text-white">
 {/* Navbar */}
 <nav className="bg-white/80 backdrop-blur-xl border-b border-slate-200 h-16 flex items-center justify-between px-6 sm:px-12 flex-shrink-0 z-50">
 <div className="flex items-center gap-4">
 <button onClick={() => router.push(`/project/${owner}/${name}`)} className="flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-indigo-600 transition-colors bg-white hover:bg-indigo-50 px-3 py-1.5 border border-transparent hover:border-indigo-100">
 <ArrowLeft className="w-4 h-4" /> Exit Intel
 </button>
 <div className="w-px h-4 bg-slate-200" />
 <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white">
 <Brain className="w-4 h-4" />
 </div>
 <span className="font-extrabold text-sm text-slate-800 tracking-tight">Deep AI Intel</span>
 <span className="text-slate-400 font-medium text-sm">— {owner}/{name}</span>
 </div>
 </nav>

 {/* Main Layout */}
 <div className="flex-1 flex overflow-hidden relative">
 
 {/* Background Orbs inside main area */}
 <div className="absolute top-20 left-20 w-[400px] h-[400px] bg-indigo-100 mix-blend-multiply filter blur-[80px] opacity-40 pointer-events-none" />

 {/* Left Content Area */}
 <div className="flex-1 flex flex-col overflow-y-auto border-r border-slate-200 relative z-10">
 
 {/* Header */}
 <div className="p-8 sm:p-12 pb-6 relative z-20">
 <div className="max-w-4xl mx-auto">
 <div className="flex items-center gap-3 mb-4">
 <span className="px-3 py-1 bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-xs font-extrabold uppercase tracking-wider flex items-center gap-1.5">
 <Zap className="w-3.5 h-3.5" /> AI GENERATED
 </span>
 </div>
 <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">Codebase Intelligence</h1>
 <p className="text-lg text-slate-500 font-medium">Deep analysis of the architecture, design patterns, and hidden dependencies.</p>
 </div>
 </div>

 {/* Tabs */}
 <div className="sticky top-0 z-40 bg-slate-50/90 backdrop-blur-md px-8 sm:px-12 border-b border-slate-200">
 <div className="max-w-4xl mx-auto flex gap-8">
 {TABS.map(tab => {
 const Icon = tab.icon;
 return (
 <button key={tab.id} onClick={() => setActiveTab(tab.id)} 
 className={`py-4 flex items-center gap-2 text-sm font-bold border-b-2 transition-all ${activeTab === tab.id ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'}`}>
 <Icon className="w-4 h-4" />
 {tab.label}
 </button>
 )
 })}
 </div>
 </div>

 {/* Tab Content */}
 <div className="flex-1 p-8 sm:p-12 pt-8">
 <div className="max-w-4xl mx-auto">
 
 {activeTab ==="overview" && (
 <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-8">
 <div className="bg-white border border-slate-100 p-8 sm:p-10">
 <h2 className="text-xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
 <Database className="w-5 h-5 text-indigo-500" /> Architecture Overview
 </h2>
 {project?.mermaid_diagram ? (
 <MermaidDiagram diagram={project.mermaid_diagram} />
 ) : (
 <div className="text-center py-16 bg-slate-50 border border-slate-100">
 <Code2 className="w-12 h-12 mx-auto mb-4 text-slate-300" />
 <p className="text-sm font-bold text-slate-500">Diagram not available</p>
 </div>
 )}
 </div>

 <div className="bg-white border border-slate-100 p-8 sm:p-10">
 <h2 className="text-xl font-extrabold text-slate-900 mb-6 flex items-center gap-2">
 <FileText className="w-5 h-5 text-indigo-500" /> Executive Summary
 </h2>
 <p className="text-slate-600 leading-relaxed font-medium">{project?.ai_summary || project?.description}</p>
 </div>
 </motion.div>
 )}

 {activeTab ==="walkthrough" && (
 <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
 {!walkthrough ? (
 <div className="text-center py-20 bg-white border border-slate-100">
 <GitMerge className="w-12 h-12 text-slate-300 mx-auto mb-4" />
 <p className="text-sm font-bold text-slate-500">Walkthrough not available for this repository yet.</p>
 </div>
 ) : (
 <div className="flex flex-col gap-8">
 {walkthrough.steps?.map((step: any, i: number) => (
 <div key={i} className="bg-white border border-slate-100 p-8 hover:-hover transition-all flex flex-col md:flex-row gap-6">
 <div className="w-12 h-12 flex-shrink-0 bg-indigo-50 border border-indigo-100 text-indigo-600 font-extrabold text-lg flex items-center justify-center">
 {i + 1}
 </div>
 <div className="flex-1 min-w-0">
 <h3 className="text-xl font-extrabold text-slate-900 mb-3">{step.title}</h3>
 <p className="text-base text-slate-600 mb-5 leading-relaxed font-medium">{step.description}</p>
 {step.files?.length > 0 && (
 <div className="flex flex-wrap gap-2 mb-5">
 {step.files.map((f: string) => (
 <span key={f} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 border border-slate-200 text-xs font-mono font-semibold text-slate-600">
 <FileText className="w-3.5 h-3.5" /> {f}
 </span>
 ))}
 </div>
 )}
 {step.code_snippet && (
 <pre className="bg-slate-900 border border-slate-800 p-5 overflow-x-auto text-xs font-mono text-slate-300">
 <code>{step.code_snippet}</code>
 </pre>
 )}
 </div>
 </div>
 ))}
 </div>
 )}
 </motion.div>
 )}

 {activeTab ==="subsystems" && (
 <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-6">
 {project?.tech_breakdown?.length > 0 ? (
 <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
 {project.tech_breakdown.map((tech: any, i: number) => (
 <div key={i} className="bg-white border border-slate-100 p-8 hover:-hover transition-all border-t-4 border-t-indigo-500">
 <h3 className="text-lg font-extrabold text-slate-900 mb-3">{tech.name}</h3>
 <p className="text-sm text-slate-600 leading-relaxed font-medium">{tech.role}</p>
 </div>
 ))}
 </div>
 ) : (
 <div className="text-center py-20 bg-white border border-slate-100">
 <Code2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
 <p className="text-sm font-bold text-slate-500">Subsystem details not available.</p>
 </div>
 )}
 </motion.div>
 )}

 </div>
 </div>
 </div>

 {/* Right Sidebar - AI Chat */}
 <div className="w-[450px] flex flex-col bg-white border-l border-slate-200 flex-shrink-0 relative z-20">
 <div className="p-5 border-b border-slate-200 bg-white/50 backdrop-blur-md flex items-center justify-between">
 <div className="flex items-center gap-3">
 <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white">
 <Brain className="w-5 h-5" />
 </div>
 <div>
 <div className="font-extrabold text-sm text-slate-900">AI Mentor</div>
 <div className="text-xs font-semibold text-emerald-500 flex items-center gap-1">
 <div className="w-2 h-2 bg-emerald-500 animate-pulse" /> Online
 </div>
 </div>
 </div>
 </div>
 
 <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 bg-slate-50/50" ref={chatRef}>
 {messages.map((msg, i) => (
 <div key={i} className={`flex ${msg.role ==="user" ?"justify-end" :"justify-start"}`}>
 {msg.role ==="assistant" && (
 <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-violet-600 flex-shrink-0 flex items-center justify-center text-white mr-3 mt-1">
 <Brain className="w-4 h-4" />
 </div>
 )}
 <div className={`max-w-[80%] p-4 text-sm leading-relaxed ${
 msg.role ==="user" 
 ?"bg-slate-900 text-white rounded-tr-sm" 
 :"bg-white border border-slate-100 text-slate-700 rounded-tl-sm font-medium"
 }`}>
 <ReactMarkdown 
 components={{
 code({inline, children}) {
 return inline ? 
 <code className="bg-slate-100 text-indigo-600 px-1.5 py-0.5 font-mono text-xs">{children}</code> :
 <pre className="bg-slate-900 text-slate-300 p-4 my-3 overflow-x-auto text-xs"><code className="font-mono">{children}</code></pre>
 },
 p({children}) { return <p className="mb-3 last:mb-0">{children}</p> },
 a({href, children}) { return <a href={href} className="text-indigo-500 font-bold hover:underline">{children}</a> }
 }}
 >
 {msg.content}
 </ReactMarkdown>
 </div>
 </div>
 ))}
 {chatLoading && (
 <div className="flex justify-start">
 <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-violet-600 flex-shrink-0 flex items-center justify-center text-white mr-3 mt-1">
 <Brain className="w-4 h-4" />
 </div>
 <div className="max-w-[80%] p-5 bg-white border border-slate-100 rounded-tl-sm">
 <div className="flex gap-1.5">
 <div className="w-2 h-2 bg-indigo-400 animate-bounce" />
 <div className="w-2 h-2 bg-indigo-400 animate-bounce" style={{ animationDelay:"0.15s" }} />
 <div className="w-2 h-2 bg-indigo-400 animate-bounce" style={{ animationDelay:"0.3s" }} />
 </div>
 </div>
 </div>
 )}
 </div>

 <div className="p-5 border-t border-slate-200 bg-white">
 <form onSubmit={e => { e.preventDefault(); sendMessage(); }} className="flex gap-3 relative">
 <input 
 type="text" 
 value={input} 
 onChange={e => setInput(e.target.value)}
 placeholder="Ask about the architecture..."
 className="flex-1 bg-slate-50 border border-slate-200 pl-4 pr-12 py-3.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder-slate-400"
 disabled={chatLoading}
 />
 <button 
 type="submit" 
 disabled={chatLoading || !input.trim()}
 className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-gradient-to-r from-indigo-600 to-violet-600 text-white hover: disabled:opacity-50 transition-all"
 >
 <Send className="w-4 h-4" />
 </button>
 </form>
 </div>
 </div>

 </div>
 </div>
 );
}
