"use client";

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useF1Store } from '@/store/useF1Store';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

type Compound = 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET';

export default function TyreHealthChart() {
    const { session } = useF1Store();
    const [data, setData] = useState<any>(null);
    const [activeCompound, setActiveCompound] = useState<Compound>('MEDIUM');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!session) return;
        setLoading(true);
        api.get('/analysis/tyre-deg')
            .then(res => setData(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [session]);

    if (loading) return <div className="flex h-full items-center justify-center text-white/50">Calculating Wear Models...</div>;
    if (!data) return <div className="flex h-full items-center justify-center text-white/50">No Data</div>;

    const currentData = data[activeCompound] || [];

    // Colors for Bars based on degradation severity
    const getBarColor = (deg: number) => {
        if (deg <= 0) return '#3b82f6'; // Blue (Getting Faster/Negative Deg)
        if (deg < 0.06) return '#4ade80'; // Green (Good)
        if (deg < 0.12) return '#facc15'; // Yellow (Avg)
        return '#f87171'; // Red (High Deg)
    };

    const traces = [{
        x: currentData.map((d: any) => d.driver),
        y: currentData.map((d: any) => d.deg_per_lap),
        type: 'bar',
        marker: {
            color: currentData.map((d: any) => getBarColor(d.deg_per_lap)),
            line: { width: 0 }
        },
        text: currentData.map((d: any) => `${d.deg_per_lap.toFixed(3)}s`),
        textposition: 'auto',
        hovertext: currentData.map((d: any) =>
            `<b>${d.driver}</b><br>` +
            `Degradation: ${d.deg_per_lap.toFixed(4)} s/lap<br>` +
            `Laps Analyzed: ${d.laps_analyzed}<br>` +
            `10 Lap Loss: ${(d.deg_per_lap * 10).toFixed(2)}s`
        ),
        hoverinfo: 'text'
    }];

    return (
        <div className="w-full h-full flex flex-col bg-[#0b0b0b] rounded-xl border border-white/10 overflow-hidden">
            {/* Header & Tabs */}
            <div className="flex justify-between items-center p-3 border-b border-white/10 bg-white/5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-white">
                    Tyre Degradation Analysis
                </h3>
                <div className="flex gap-1 bg-black/40 p-1 rounded-lg">
                    {(['SOFT', 'MEDIUM', 'HARD'] as Compound[]).map((c) => (
                        <button
                            key={c}
                            onClick={() => setActiveCompound(c)}
                            className={cn(
                                "px-3 py-1 text-[10px] font-bold rounded-md transition-all",
                                activeCompound === c
                                    ? c === 'SOFT' ? "bg-red-500/20 text-red-500 border border-red-500/50"
                                        : c === 'MEDIUM' ? "bg-yellow-500/20 text-yellow-500 border border-yellow-500/50"
                                            : c === 'HARD' ? "bg-white/20 text-white border border-white/50"
                                                : "bg-blue-500/20 text-blue-500 border border-blue-500/50"
                                    : "text-white/40 hover:text-white hover:bg-white/5"
                            )}
                        >
                            {c}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart */}
            <div className="flex-1 min-h-0 relative">
                {currentData.length === 0 ? (
                    <div className="absolute inset-0 flex items-center justify-center text-white/30 text-xs">
                        No valid long runs found for {activeCompound} tyres.
                    </div>
                ) : (
                    <Plot
                        data={traces as any}
                        layout={{
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            font: { color: '#888' },
                            margin: { t: 20, r: 20, b: 40, l: 50 },
                            showlegend: false,
                            xaxis: {
                                title: { text: 'Driver' },
                                tickfont: { size: 11, color: '#ccc' },
                                gridcolor: '#222'
                            },
                            yaxis: {
                                title: { text: 'Pace Loss (s/lap)' },
                                gridcolor: '#333',
                                zerolinecolor: '#666'
                            },
                            dragmode: false
                        }}
                        style={{ width: '100%', height: '100%' }} // Add explicit style
                        useResizeHandler={true} // Ensure resizing works
                        className="w-full h-full"
                        config={{ displayModeBar: false }}
                    />
                )}
            </div>

            {/* Legend / Guide */}
            <div className="p-2 border-t border-white/10 flex justify-center gap-4 text-[9px] text-white/40 uppercase tracking-widest">
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-blue-500" /> Improving</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-green-400" /> Low (&lt;0.06s)</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-yellow-400" /> Med</span>
                <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-red-400" /> High (&gt;0.12s)</span>
            </div>
        </div>
    );
}
