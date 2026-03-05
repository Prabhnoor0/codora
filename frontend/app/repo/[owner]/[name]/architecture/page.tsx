"use client";

import { useEffect, useState, useCallback } from"react";
import { useParams } from"next/navigation";
import ReactFlow, {
 Background, Controls, MiniMap,
 Node, Edge, BackgroundVariant,
 useNodesState, useEdgesState,
} from"reactflow";
import"reactflow/dist/style.css";
import { repoApi } from"@/lib/api";
import { Network, Info } from"lucide-react";

const NODE_COLORS: Record<string, string> = {
 service:"#8b5cf6",
 database:"#06b6d4",
 api:"#10b981",
 frontend:"#f59e0b",
 queue:"#ef4444",
 cache:"#6366f1",
 default:"#64748b",
};

function ArchNode({ data }: { data: any }) {
 const color = NODE_COLORS[data.type] || NODE_COLORS.default;
 return (
 <div className="arch-node px-4 py-3 min-w-[120px] text-center"
 style={{ borderColor: color +"66", boxShadow: `0 0 20px ${color}22` }}>
 <div className="text-xs font-bold uppercase tracking-wider mb-1" style={{ color }}>
 {data.type ||"module"}
 </div>
 <div className="text-sm font-semibold text-white">{data.label}</div>
 </div>
 );
}

const nodeTypes = { arch: ArchNode };

export default function ArchitecturePage() {
 const params = useParams();
 const owner = params.owner as string;
 const name = params.name as string;

 const [nodes, setNodes, onNodesChange] = useNodesState([]);
 const [edges, setEdges, onEdgesChange] = useEdgesState([]);
 const [loading, setLoading] = useState(true);
 const [selectedNode, setSelectedNode] = useState<any>(null);

 useEffect(() => {
 repoApi.getArchitecture(owner, name).then((data) => {
 const rawNodes = data.nodes || [];
 const rawEdges = data.edges || [];

 // Apply grid layout if no positions provided
 const flowNodes: Node[] = rawNodes.map((n: any, i: number) => ({
 id: n.id || String(i),
 type:"arch",
 position: {
 x: n.x ?? (i % 4) * 220 + 50,
 y: n.y ?? Math.floor(i / 4) * 160 + 50,
 },
 data: { label: n.label, type: n.type },
 }));

 const flowEdges: Edge[] = rawEdges.map((e: any, i: number) => ({
 id: `edge-${i}`,
 source: e.source,
 target: e.target,
 label: e.label,
 type:"smoothstep",
 style: { stroke:"#8b5cf666", strokeWidth: 2 },
 labelStyle: { fill:"#94a3b8", fontSize: 11 },
 labelBgStyle: { fill:"#0f172a" },
 animated: e.animated,
 }));

 setNodes(flowNodes);
 setEdges(flowEdges);
 }).catch(console.error).finally(() => setLoading(false));
 }, [owner, name]);

 if (loading) return (
 <div className="h-screen flex items-center justify-center">
 <div className="text-center">
 <div className="w-12 h-12 border-2 border-violet-500 border-t-transparent animate-spin mx-auto mb-3" />
 <p className="text-slate-400">Loading architecture diagram...</p>
 </div>
 </div>
 );

 return (
 <div className="h-screen flex flex-col">
 <div className="glass border-b border-white/5 px-6 py-3 flex items-center gap-3">
 <Network className="w-5 h-5 text-violet-400" />
 <h1 className="font-bold">{owner}/{name} — Architecture</h1>
 <a href={`/repo/${owner}/${name}`} className="ml-auto text-sm text-slate-400 hover:text-white transition-colors">
 ← Back to Overview
 </a>
 </div>

 <div className="flex-1 relative">
 <ReactFlow
 nodes={nodes}
 edges={edges}
 onNodesChange={onNodesChange}
 onEdgesChange={onEdgesChange}
 nodeTypes={nodeTypes}
 onNodeClick={(_, node) => setSelectedNode(node)}
 fitView
 fitViewOptions={{ padding: 0.2 }}
 proOptions={{ hideAttribution: true }}
 >
 <Background
 variant={BackgroundVariant.Dots}
 color="#1e2d4b"
 gap={24}
 size={1}
 />
 <Controls
 style={{ background:"rgba(15, 23, 42, 0.9)", border:"1px solid rgba(51, 65, 85, 0.5)" }}
 />
 <MiniMap
 style={{ background:"rgba(15, 23, 42, 0.9)", border:"1px solid rgba(51, 65, 85, 0.5)" }}
 nodeColor={(n) => NODE_COLORS[n.data?.type] || NODE_COLORS.default}
 />
 </ReactFlow>

 {/* Node Detail Panel */}
 {selectedNode && (
 <div className="absolute top-4 right-4 glass-strong p-4 w-64 z-10">
 <div className="flex items-center gap-2 mb-3">
 <Info className="w-4 h-4 text-violet-400" />
 <span className="font-semibold text-sm">{selectedNode.data.label}</span>
 <button onClick={() => setSelectedNode(null)} className="ml-auto text-slate-500 hover:text-white text-lg leading-none">×</button>
 </div>
 <div className="space-y-2 text-sm">
 <div className="flex justify-between">
 <span className="text-slate-500">Type</span>
 <span className="badge badge-violet">{selectedNode.data.type ||"module"}</span>
 </div>
 <div className="flex justify-between">
 <span className="text-slate-500">Node ID</span>
 <span className="text-slate-300">{selectedNode.id}</span>
 </div>
 </div>
 </div>
 )}

 {/* Legend */}
 <div className="absolute bottom-20 left-4 glass p-3 z-10">
 <p className="text-xs text-slate-500 mb-2 font-semibold">LEGEND</p>
 <div className="space-y-1.5">
 {Object.entries(NODE_COLORS).filter(([k]) => k !=="default").map(([type, color]) => (
 <div key={type} className="flex items-center gap-2">
 <div className="w-3 h-3" style={{ background: color }} />
 <span className="text-xs text-slate-400 capitalize">{type}</span>
 </div>
 ))}
 </div>
 </div>
 </div>
 </div>
 );
}
