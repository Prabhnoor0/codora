"use client";
import { useEffect } from"react";
import { useRouter } from"next/navigation";
import { useUserStore } from"@/lib/store";

/**
 * /dashboard is kept for backwards compatibility.
 * It redirects to /explore (if skills filled) or /profile/setup (if not).
 */
export default function DashboardPage() {
 const router = useRouter();
 const { user } = useUserStore();

 useEffect(() => {
 if (!user) { router.replace("/"); return; }
 if (!user.profile_analyzed || !user.top_languages?.length) {
 router.replace("/profile/setup");
 } else {
 router.replace("/explore");
 }
 }, [user, router]);

 return (
 <div style={{
 minHeight:"100vh", display:"flex", alignItems:"center", justifyContent:"center",
 background:"#f9fafb", fontFamily:"'Inter', sans-serif",
 }}>
 <div style={{ textAlign:"center" }}>
 <div style={{
 width: 48, height: 48,
 border:"3px solid #f3f4f6", borderTop:"3px solid #ec4899",
 borderRadius:"50%", animation:"spin 0.8s linear infinite", margin:"0 auto 16px",
 }} />
 <p style={{ color:"#6b7280", fontWeight: 600 }}>Loading your workspace…</p>
 </div>
 <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
 </div>
 );
}
