"use client";
import { useChatbotStore } from"@/lib/store";

export default function LayoutContentWrapper({ children }: { children: React.ReactNode }) {
  const { isOpen } = useChatbotStore();

  return (
    <div
      className="transition-all duration-300 ease-in-out origin-left"
      style={{
        width: isOpen ? "calc(100vw - 400px)" : "100vw",
        minHeight: "100vh",
        overflowX: "hidden",
      }}
    >
      {children}
    </div>
  );
}
