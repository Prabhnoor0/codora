import type { Metadata } from"next";
import"./globals.css";

export const metadata: Metadata = {
 title:"Codora — Your Personal Codebase Guide",
 description:
"An intelligent mentor platform that teaches codebases, recommends issues, predicts contribution success, and guides developers through open source contributions.",
 keywords: ["open source","AI mentor","code learning","GitHub","developer tools"],
 authors: [{ name:"Codora" }],
 openGraph: {
 title:"Codora",
 description:"GitHub + Coursera + Duolingo + Copilot combined.",
 type:"website",
 },
};

import GlobalChatbot from"./components/GlobalChatbot";
import LayoutContentWrapper from"./components/LayoutContentWrapper";

import { Plus_Jakarta_Sans } from"next/font/google";

const plusJakartaSans = Plus_Jakarta_Sans({
 subsets: ["latin"],
 display:"swap",
 variable:"--font-sans",
});

export default function RootLayout({
 children,
}: {
 children: React.ReactNode;
}) {
 return (
 <html lang="en" className={plusJakartaSans.variable}>
 <body className="antialiased">
 <LayoutContentWrapper>
 {children}
 </LayoutContentWrapper>
 <GlobalChatbot />
 </body>
 </html>
 );
}
