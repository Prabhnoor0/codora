"use client";

import { useEffect } from"react";
import { useSearchParams, useRouter } from"next/navigation";
import { useUserStore } from"@/lib/store";
import { authApi } from"@/lib/api";
import { Suspense } from"react";

function AuthCallbackContent() {
 const searchParams = useSearchParams();
 const router = useRouter();
 const { setToken, setUser } = useUserStore();

 useEffect(() => {
 const token = searchParams.get("token");
 if (!token) { router.push("/"); return; }
 setToken(token);
 authApi.getMe()
 .then((user) => {
 setUser(user);
 if (!user.profile_analyzed || !user.top_languages?.length) {
 router.push("/profile/setup");
 } else {
 router.push("/explore");
 }
 })
 .catch(() => router.push("/"));
 }, [searchParams, router, setToken, setUser]);

 return (
 <div style={{
 minHeight:"100vh",
 display:"flex",
 flexDirection:"column",
 alignItems:"center",
 justifyContent:"center",
 gap: 20,
 background:"#ffffff",
 fontFamily:"'Inter', system-ui, sans-serif",
 }}>
 {/* Spinner */}
 <div style={{
 width: 56,
 height: 56,
 borderRadius:"50%",
 border:"3px solid #f3f4f6",
 borderTop:"3px solid #ec4899",
 animation:"spin 0.8s linear infinite",
 }} />
 <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

 <div style={{ textAlign:"center" }}>
 <p style={{ fontSize: 20, fontWeight: 700, color:"#111827", margin:"0 0 8px" }}>
 Setting up your account…
 </p>
 <p style={{ fontSize: 14, color:"#6b7280", margin: 0 }}>
 Importing your GitHub profile and analyzing your skills
 </p>
 </div>

 {/* Progress dots */}
 <div style={{ display:"flex", gap: 8 }}>
 {["#ec4899","#3b82f6","#10b981","#eab308"].map((color, i) => (
 <div key={i} style={{
 width: 8, height: 8, borderRadius:"50%", background: color,
 animation: `pulse 1.4s ease-in-out ${i * 0.2}s infinite`,
 opacity: 0.7,
 }} />
 ))}
 </div>
 <style>{`@keyframes pulse { 0%,80%,100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1); opacity: 1; } }`}</style>
 </div>
 );
}

export default function AuthCallbackPage() {
 return (
 <Suspense>
 <AuthCallbackContent />
 </Suspense>
 );
}
