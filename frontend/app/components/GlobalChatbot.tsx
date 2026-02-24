"use client";
import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, User as UserIcon, Send, X, MessageCircle } from "lucide-react";
import { useUserStore, useChatbotStore } from "@/lib/store";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function GlobalChatbot() {
  const params = useParams();
  const owner = params?.owner as string;
  const repo = (params?.repo || params?.name) as string;
  const issueNumber = params?.number as string;

  const { token } = useUserStore();
  const { isOpen, setIsOpen } = useChatbotStore();
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Initialize initial message when repo or issue context changes
  useEffect(() => {
    if (owner && repo) {
      if (issueNumber) {
        setMessages([
          { role: "assistant", content: `I'm your AI mentor for issue #${issueNumber} in ${owner}/${repo}.\n\nAsk me how to approach the fix, what files to inspect, or for architectural clarification.` }
        ]);
      } else {
        setMessages([
          { role: "assistant", content: `I'm your AI mentor for ${owner}/${repo}.\n\nAsk me about this codebase's architecture, dependencies, or how to get started.` }
        ]);
      }
    }
  }, [owner, repo, issueNumber]);

  useEffect(() => {
    if (isOpen) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  // Don't render the chatbot FAB if we are not inside a repository context
  if (!owner || !repo) return null;

  const send = async () => {
    if (!input.trim() || streaming) return;
    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }, { role: "assistant", content: "" }]);
    setStreaming(true);
    try {
      const res = await fetch(`${API}/api/mentor/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question: userMsg, repo_full_name: `${owner}/${repo}`, history: messages.slice(-6) }),
      });
      if (!res.ok || !res.body) throw new Error();
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let full = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value).split("\n")) {
          if (!line.startsWith("data:")) continue;
          try {
            const p = JSON.parse(line.slice(6));
            if (p.chunk) { 
              full += p.chunk; 
              setMessages(prev => { 
                const n = [...prev]; 
                n[n.length - 1] = { role: "assistant", content: full }; 
                return n; 
              }); 
            }
          } catch {}
        }
      }
    } catch { 
      setMessages(prev => { 
        const n = [...prev]; 
        n[n.length - 1] = { role: "assistant", content: "Error communicating with intelligence server." }; 
        return n; 
      }); 
    } finally { 
      setStreaming(false); 
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: isOpen ? 0 : 1 }}
        onClick={() => setIsOpen(true)}
        className="fixed bottom-8 right-8 w-14 h-14 bg-slate-900 text-white border-2 border-slate-900 flex items-center justify-center cursor-pointer z-50 hover:bg-white hover:text-slate-900 transition-colors"
      >
        <MessageCircle className="w-6 h-6" />
      </motion.button>

      {/* Sliding Sidebar Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: "100%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "100%", opacity: 0 }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed top-0 right-0 w-[400px] h-screen bg-slate-50 border-l-2 border-slate-200 z-50 flex flex-col shadow-[-10px_0_30px_rgba(15,23,42,0.1)]"
          >
            {/* Header */}
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-white">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 border border-slate-200 bg-slate-900 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="m-0 font-extrabold text-lg text-slate-900 uppercase tracking-tight">AI Mentor</p>
                  <p className="m-0 font-mono text-[10px] text-slate-500 font-bold tracking-widest uppercase"> Online / Repo-Aware</p>
                </div>
              </div>
              <button onClick={() => setIsOpen(false)} className="bg-white border border-slate-200 p-1.5 cursor-pointer text-slate-500 hover:border-slate-400 hover:text-slate-900 transition-all">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-6 bg-slate-50">
              {messages.map((m, i) => (
                <div key={i} className={`flex gap-3 items-start ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                  <div className={`w-8 h-8 border border-slate-200 flex items-center justify-center flex-shrink-0 ${m.role === "user" ? "bg-white" : "bg-slate-900"}`}>
                    {m.role === "user" ? <UserIcon className="w-4 h-4 text-slate-900" /> : <Bot className="w-4 h-4 text-white" />}
                  </div>
                  <div className={`px-4 py-3 text-sm font-medium leading-relaxed max-w-[80%] whitespace-pre-wrap border ${m.role === "user" ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-800 border-slate-200"}`}>
                    {m.content || (streaming && i === messages.length - 1 ? <span className="text-slate-400 font-mono text-sm uppercase">Typing...</span> : "")}
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-slate-200 bg-white flex gap-2">
              <input 
                value={input} 
                onChange={e => setInput(e.target.value)} 
                onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()} 
                placeholder={issueNumber ? `ASK ABOUT ISSUE #${issueNumber}...` : "ASK ABOUT THIS REPOSITORY..."} 
                className="w-full border-2 border-slate-200 bg-slate-50 text-slate-900 font-medium placeholder-slate-400 focus:outline-none focus:border-slate-900 flex-1 p-3 transition-colors text-sm" 
              />
              <button 
                onClick={send} 
                disabled={streaming || !input.trim()} 
                className="px-4 py-3 bg-slate-900 text-white font-bold hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
