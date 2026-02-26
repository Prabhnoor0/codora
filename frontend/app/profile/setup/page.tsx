"use client";
import { useState, useEffect } from"react";
import { useRouter } from"next/navigation";
import { motion } from"framer-motion";
import { Brain, ChevronRight, Check, Zap, Code2, Star } from"lucide-react";
import { useUserStore } from"@/lib/store";
import { userApi } from"@/lib/api";

const SKILLS = [
 { name:"Python", color:"#3b82f6", icon:"" },
 { name:"JavaScript", color:"#eab308", icon:"" },
 { name:"TypeScript", color:"#3b82f6", icon:"" },
 { name:"Go", color:"#06b6d4", icon:"" },
 { name:"Rust", color:"#f97316", icon:"" },
 { name:"Java", color:"#ec4899", icon:"" },
 { name:"C++", color:"#8b5cf6", icon:"" },
 { name:"Ruby", color:"#ef4444", icon:"" },
 { name:"PHP", color:"#6366f1", icon:"" },
 { name:"Swift", color:"#f97316", icon:"" },
 { name:"Kotlin", color:"#8b5cf6", icon:"" },
 { name:"Dart", color:"#06b6d4", icon:"" },
 { name:"React", color:"#06b6d4", icon:"" },
 { name:"Vue", color:"#10b981", icon:"" },
 { name:"Docker", color:"#3b82f6", icon:"" },
 { name:"Kubernetes", color:"#3b82f6", icon:"" },
 { name:"Machine Learning", color:"#ec4899", icon:"" },
 { name:"DevOps", color:"#10b981", icon:"" },
];

const INTERESTS = [
 { name:"Web Development", icon:"" },
 { name:"Machine Learning", icon:"" },
 { name:"DevOps & Cloud", icon:"" },
 { name:"Mobile Apps", icon:"" },
 { name:"CLI Tools", icon:"⌨" },
 { name:"Systems Programming", icon:"" },
 { name:"Data Science", icon:"" },
 { name:"Security", icon:"" },
 { name:"Game Dev", icon:"" },
 { name:"Databases", icon:"" },
];

const LEVELS = [
 { value:"beginner", label:"Beginner", desc:"< 1 year coding", icon:"" },
 { value:"intermediate", label:"Intermediate", desc:"1–3 years coding", icon:"" },
 { value:"advanced", label:"Advanced", desc:"3+ years, open source experience", icon:"" },
];

const API = process.env.NEXT_PUBLIC_API_URL ||"http://localhost:8000";

export default function ProfileSetupPage() {
 const router = useRouter();
 const { user, token } = useUserStore();
 const [step, setStep] = useState(1);
 const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
 const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
 const [level, setLevel] = useState("beginner");
 const [saving, setSaving] = useState(false);
 const [githubScan, setGithubScan] = useState<any>(null);

 useEffect(() => {
 if (!user) { router.push("/"); return; }
 // Auto-scan GitHub on load
 fetch(`${API}/api/users/me/github-scan`, {
 headers: { Authorization: `Bearer ${token}` }
 }).then(r => r.json()).then(data => {
 setGithubScan(data);
 if (data.top_languages?.length) {
 setSelectedSkills(data.top_languages.slice(0, 5));
 }
 if (data.expertise_level) setLevel(data.expertise_level);
 }).catch(() => {});
 }, [user, token, router]);

 const toggle = (arr: string[], setArr: any, val: string) => {
 setArr((prev: string[]) => prev.includes(val) ? prev.filter(v => v !== val) : [...prev, val]);
 };

 const handleFinish = async () => {
 setSaving(true);
 try {
 await fetch(`${API}/api/users/me/skills`, {
 method:"POST",
 headers: {"Content-Type":"application/json", Authorization: `Bearer ${token}` },
 body: JSON.stringify({ skills: selectedSkills, experience_level: level, interests: selectedInterests }),
 });
 router.push("/explore");
 } catch (e) {
 setSaving(false);
 }
 };

 const TOTAL_STEPS = 3;

 return (
 <div style={{ fontFamily:"'Inter', sans-serif", background:"#f9fafb", minHeight:"100vh" }}>
 {/* Header */}
 <nav style={{
 background:"#fff", borderBottom:"1px solid #f3f4f6", padding:"0 48px",
 height: 64, display:"flex", alignItems:"center", justifyContent:"space-between",
 }}>
 <div style={{ display:"flex", alignItems:"center", gap: 10 }}>
 <div style={{ width: 36, height: 36, borderRadius: 10, background:"linear-gradient(135deg,#ec4899,#3b82f6)", display:"flex", alignItems:"center", justifyContent:"center" }}>
 <Brain style={{ width: 20, height: 20, color:"#fff" }} />
 </div>
 <span style={{ fontWeight: 800, fontSize: 17, color:"#111827" }}>
 Mentor<span style={{ background:"linear-gradient(135deg,#ec4899,#3b82f6)", WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent" }}>AI</span>
 </span>
 </div>
 <div style={{ display:"flex", gap: 8 }}>
 {[1,2,3].map(s => (
 <div key={s} style={{ width: 32, height: 4, borderRadius: 2, background: s <= step ?"linear-gradient(90deg,#ec4899,#3b82f6)" :"#e5e7eb" }} />
 ))}
 </div>
 </nav>

 <div style={{ maxWidth: 700, margin:"0 auto", padding:"60px 24px" }}>
 {githubScan?.success && (
 <div style={{
 background:"rgba(16,185,129,0.08)", border:"1px solid rgba(16,185,129,0.2)",
 borderRadius: 12, padding:"12px 20px", marginBottom: 32,
 display:"flex", alignItems:"center", gap: 10, fontSize: 14, color:"#059669",
 }}>
 <Check style={{ width: 16, height: 16 }} />
 <span> GitHub profile scanned! We auto-detected your top languages.</span>
 </div>
 )}

 {step === 1 && (
 <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
 <h1 style={{ fontSize: 32, fontWeight: 900, color:"#111827", marginBottom: 8 }}>What's your experience level? </h1>
 <p style={{ color:"#6b7280", marginBottom: 36, fontSize: 16 }}>This helps us recommend the right projects and issues for you.</p>
 <div style={{ display:"flex", flexDirection:"column", gap: 16 }}>
 {LEVELS.map(l => (
 <button key={l.value} onClick={() => setLevel(l.value)} style={{
 background: level === l.value ?"linear-gradient(135deg, rgba(236,72,153,0.08), rgba(59,130,246,0.08))" :"#fff",
 border: level === l.value ?"2px solid #ec4899" :"2px solid #e5e7eb",
 borderRadius: 16, padding:"20px 24px", cursor:"pointer",
 display:"flex", alignItems:"center", gap: 20, textAlign:"left",
 transition:"all 0.15s",
 }}>
 <span style={{ fontSize: 36 }}>{l.icon}</span>
 <div style={{ flex: 1 }}>
 <p style={{ fontSize: 17, fontWeight: 700, color:"#111827", margin: 0 }}>{l.label}</p>
 <p style={{ fontSize: 14, color:"#6b7280", margin: 0 }}>{l.desc}</p>
 </div>
 {level === l.value && <Check style={{ width: 20, height: 20, color:"#ec4899" }} />}
 </button>
 ))}
 </div>
 <button onClick={() => setStep(2)} style={{
 marginTop: 32, background:"linear-gradient(135deg,#ec4899,#3b82f6)", color:"#fff",
 border:"none", borderRadius: 12, padding:"14px 32px", fontSize: 15, fontWeight: 700,
 cursor:"pointer", display:"flex", alignItems:"center", gap: 8,
 }}>Next: Pick your skills <ChevronRight style={{ width: 18, height: 18 }} /></button>
 </motion.div>
 )}

 {step === 2 && (
 <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
 <h1 style={{ fontSize: 32, fontWeight: 900, color:"#111827", marginBottom: 8 }}>What do you know? </h1>
 <p style={{ color:"#6b7280", marginBottom: 36, fontSize: 16 }}>Select all the languages and technologies you're comfortable with.</p>
 <div style={{ display:"flex", flexWrap:"wrap", gap: 12, marginBottom: 36 }}>
 {SKILLS.map(s => {
 const selected = selectedSkills.includes(s.name);
 return (
 <button key={s.name} onClick={() => toggle(selectedSkills, setSelectedSkills, s.name)} style={{
 display:"flex", alignItems:"center", gap: 8, padding:"10px 18px",
 borderRadius: 999, border: `2px solid ${selected ? s.color :"#e5e7eb"}`,
 background: selected ? `${s.color}15` :"#fff",
 color: selected ? s.color :"#374151", fontWeight: 600, fontSize: 14,
 cursor:"pointer", transition:"all 0.15s",
 }}>
 <span>{s.icon}</span> {s.name}
 {selected && <Check style={{ width: 14, height: 14 }} />}
 </button>
 );
 })}
 </div>
 <div style={{ display:"flex", gap: 12 }}>
 <button onClick={() => setStep(1)} style={{
 background:"#fff", border:"1.5px solid #e5e7eb", color:"#6b7280",
 borderRadius: 12, padding:"14px 24px", fontSize: 15, fontWeight: 600, cursor:"pointer",
 }}>Back</button>
 <button onClick={() => setStep(3)} disabled={selectedSkills.length === 0} style={{
 background: selectedSkills.length === 0 ?"#e5e7eb" :"linear-gradient(135deg,#ec4899,#3b82f6)",
 color: selectedSkills.length === 0 ?"#9ca3af" :"#fff",
 border:"none", borderRadius: 12, padding:"14px 32px", fontSize: 15, fontWeight: 700,
 cursor: selectedSkills.length === 0 ?"not-allowed" :"pointer",
 display:"flex", alignItems:"center", gap: 8,
 }}>Next: Your Interests <ChevronRight style={{ width: 18, height: 18 }} /></button>
 </div>
 </motion.div>
 )}

 {step === 3 && (
 <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
 <h1 style={{ fontSize: 32, fontWeight: 900, color:"#111827", marginBottom: 8 }}>What excites you? </h1>
 <p style={{ color:"#6b7280", marginBottom: 36, fontSize: 16 }}>Pick your areas of interest — we'll find the best matching open source projects.</p>
 <div style={{ display:"flex", flexWrap:"wrap", gap: 12, marginBottom: 36 }}>
 {INTERESTS.map(i => {
 const selected = selectedInterests.includes(i.name);
 return (
 <button key={i.name} onClick={() => toggle(selectedInterests, setSelectedInterests, i.name)} style={{
 display:"flex", alignItems:"center", gap: 8, padding:"12px 20px",
 borderRadius: 16, border: `2px solid ${selected ?"#ec4899" :"#e5e7eb"}`,
 background: selected ?"rgba(236,72,153,0.08)" :"#fff",
 color: selected ?"#ec4899" :"#374151", fontWeight: 600, fontSize: 14,
 cursor:"pointer", transition:"all 0.15s",
 }}>
 <span style={{ fontSize: 20 }}>{i.icon}</span> {i.name}
 {selected && <Check style={{ width: 14, height: 14 }} />}
 </button>
 );
 })}
 </div>
 <div style={{ display:"flex", gap: 12 }}>
 <button onClick={() => setStep(2)} style={{
 background:"#fff", border:"1.5px solid #e5e7eb", color:"#6b7280",
 borderRadius: 12, padding:"14px 24px", fontSize: 15, fontWeight: 600, cursor:"pointer",
 }}>Back</button>
 <button onClick={handleFinish} disabled={saving} style={{
 background: saving ?"#e5e7eb" :"linear-gradient(135deg,#ec4899,#3b82f6)",
 color: saving ?"#9ca3af" :"#fff",
 border:"none", borderRadius: 12, padding:"14px 36px", fontSize: 15, fontWeight: 700,
 cursor: saving ?"not-allowed" :"pointer", display:"flex", alignItems:"center", gap: 8,
 }}>
 {saving ?"Setting up..." : <><Zap style={{ width: 18, height: 18 }} /> Find my projects!</>}
 </button>
 </div>
 </motion.div>
 )}
 </div>
 </div>
 );
}
