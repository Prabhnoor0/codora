"use client";

import { useState, useRef, useEffect } from"react";
import { useParams } from"next/navigation";
import { motion, AnimatePresence } from"framer-motion";
import { Brain, Send, User2, Loader2, Code2, FileText, X } from"lucide-react";
import { useMentorStore } from"@/lib/store";
import { mentorApi } from"@/lib/api";
import ReactMarkdown from"react-markdown";

const SUGGESTED_QUESTIONS = [
"How does authentication work in this codebase?",
"What files should I study first as a new contributor?",
"Explain the database layer architecture",
"Where would I implement a new API endpoint?",
"How is error handling done across the codebase?",
];

export default function MentorChatPage() {
 const params = useParams();
 const owner = params.owner as string;
 const name = params.name as string;
 const repoFullName = `${owner}/${name}`;

 const { messages, isStreaming, conversationId, addMessage, updateLastMessage, setStreaming, setConversationId } = useMentorStore();
 const [input, setInput] = useState("");
 const messagesEndRef = useRef<HTMLDivElement>(null);
 const textareaRef = useRef<HTMLTextAreaElement>(null);

 useEffect(() => {
 messagesEndRef.current?.scrollIntoView({ behavior:"smooth" });
 }, [messages]);

 const sendMessage = async (question?: string) => {
 const text = question || input.trim();
 if (!text || isStreaming) return;
 setInput("");

 // Create conversation if needed
 let convId = conversationId;
 if (!convId) {
 try {
 const conv = await mentorApi.createConversation(repoFullName);
 convId = conv.conversation_id;
 setConversationId(convId!);
 } catch (e) {
 console.error(e);
 }
 }

 // Add user message
 const userMsg = { id: Date.now().toString(), role:"user" as const, content: text, timestamp: Date.now() };
 addMessage(userMsg);

 // Add placeholder assistant message
 const assistantMsg = { id: (Date.now() + 1).toString(), role:"assistant" as const, content:"", timestamp: Date.now() };
 addMessage(assistantMsg);
 setStreaming(true);

 try {
 const token = typeof window !=="undefined" ? localStorage.getItem("mentor_token") : null;
 const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ||"http://localhost:8000"}/api/mentor/chat`, {
 method:"POST",
 headers: {
"Content-Type":"application/json",
 ...(token ? { Authorization: `Bearer ${token}` } : {}),
 },
 body: JSON.stringify({
 question: text,
 repo_full_name: repoFullName,
 conversation_id: convId,
 history: messages.slice(-6).map(m => ({ role: m.role, content: m.content })),
 }),
 });

 if (!response.ok) throw new Error("Chat request failed");

 const reader = response.body?.getReader();
 const decoder = new TextDecoder();
 let fullResponse ="";

 while (reader) {
 const { done, value } = await reader.read();
 if (done) break;

 const chunk = decoder.decode(value);
 const lines = chunk.split("\n").filter(l => l.startsWith("data:"));

 for (const line of lines) {
 try {
 const data = JSON.parse(line.slice(6));
 if (data.chunk) {
 fullResponse += data.chunk;
 updateLastMessage(fullResponse);
 }
 } catch {}
 }
 }
 } catch (e) {
 updateLastMessage("Sorry, I encountered an error. Please try again.");
 } finally {
 setStreaming(false);
 }
 };

 return (
 <div className="h-screen flex flex-col">
 {/* Header */}
 <div className="glass border-b border-white/5 px-6 py-3 flex items-center gap-3">
 <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center">
 <Brain className="w-4 h-4 text-white" />
 </div>
 <div>
 <h1 className="font-bold text-sm">AI Mentor Chat</h1>
 <p className="text-xs text-slate-500">{repoFullName}</p>
 </div>
 <a href={`/repo/${owner}/${name}`} className="ml-auto text-sm text-slate-400 hover:text-white transition-colors">
 ← Back
 </a>
 </div>

 {/* Messages */}
 <div className="flex-1 overflow-y-auto p-6 space-y-4">
 {messages.length === 0 && (
 <div className="flex flex-col items-center justify-center h-full gap-6">
 <div className="w-20 h-20 bg-gradient-to-br from-violet-500/20 to-indigo-500/20 border border-violet-500/30 flex items-center justify-center">
 <Brain className="w-10 h-10 text-violet-400 animate-float" />
 </div>
 <div className="text-center">
 <h2 className="text-xl font-bold mb-2 gradient-text">Your Repository Mentor</h2>
 <p className="text-slate-400 text-sm max-w-md">
 Ask me anything about <span className="text-violet-400 font-semibold">{name}</span>.
 I have full context of its architecture, code, and documentation.
 </p>
 </div>
 <div className="grid grid-cols-1 gap-2 w-full max-w-lg">
 {SUGGESTED_QUESTIONS.map((q) => (
 <button
 key={q}
 onClick={() => sendMessage(q)}
 className="text-left p-3 card text-sm text-slate-300 hover:text-white hover:border-violet-500/50 transition-all"
 >
 {q}
 </button>
 ))}
 </div>
 </div>
 )}

 <AnimatePresence>
 {messages.map((msg) => (
 <motion.div
 key={msg.id}
 initial={{ opacity: 0, y: 10 }}
 animate={{ opacity: 1, y: 0 }}
 className={`flex gap-3 ${msg.role ==="user" ?"justify-end" :"justify-start"}`}
 >
 {msg.role ==="assistant" && (
 <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center shrink-0 mt-1">
 <Brain className="w-4 h-4 text-white" />
 </div>
 )}

 <div className={msg.role ==="user" ?"chat-user" :"chat-assistant max-w-3xl"}>
 {msg.role ==="assistant" && msg.content ==="" && isStreaming ? (
 <div className="flex items-center gap-2 text-slate-400">
 <Loader2 className="w-4 h-4 animate-spin" />
 <span className="text-sm">Thinking...</span>
 </div>
 ) : (
 <div className="text-sm prose prose-invert prose-sm max-w-none">
 <ReactMarkdown>{msg.content}</ReactMarkdown>
 {msg.role ==="assistant" && msg.content !=="" && isStreaming &&
 messages[messages.length - 1].id === msg.id && (
 <span className="inline-block w-1.5 h-4 bg-violet-400 animate-typing ml-1 align-middle" />
 )}
 </div>
 )}
 </div>

 {msg.role ==="user" && (
 <div className="w-8 h-8 bg-slate-700 flex items-center justify-center shrink-0 mt-1">
 <User2 className="w-4 h-4 text-slate-300" />
 </div>
 )}
 </motion.div>
 ))}
 </AnimatePresence>
 <div ref={messagesEndRef} />
 </div>

 {/* Input */}
 <div className="glass border-t border-white/5 p-4">
 <div className="flex gap-3 max-w-4xl mx-auto">
 <textarea
 ref={textareaRef}
 value={input}
 onChange={(e) => setInput(e.target.value)}
 onKeyDown={(e) => {
 if (e.key ==="Enter" && !e.shiftKey) {
 e.preventDefault();
 sendMessage();
 }
 }}
 placeholder={`Ask about ${name}... (Enter to send, Shift+Enter for newline)`}
 rows={1}
 className="input-dark flex-1 resize-none"
 style={{ minHeight:"44px", maxHeight:"120px" }}
 />
 <button
 onClick={() => sendMessage()}
 disabled={isStreaming || !input.trim()}
 className="btn-primary px-4 disabled:opacity-40 shrink-0"
 >
 {isStreaming ? (
 <Loader2 className="w-4 h-4 animate-spin" />
 ) : (
 <Send className="w-4 h-4" />
 )}
 </button>
 </div>
 <p className="text-xs text-slate-600 text-center mt-2">
 Repository-aware AI • Responses grounded in actual code
 </p>
 </div>
 </div>
 );
}
