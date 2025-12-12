import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { useF1Store } from '@/store/useF1Store';
import { api } from '@/lib/api';

interface MapSegment {
    sector_index: number;
    x: number[];
    y: number[];
    time_lost: number; // Seconds lost in this sector vs theoretial best
    pct_lost: number;
}

interface TheoreticalData {
    driver: string;
    theoretical_best: number;
    actual_best: number;
    diff: number;
    segments: MapSegment[];
}

export default function TheoreticalBestLapChart() {
    const { session, selectedDriver } = useF1Store();
    const [driverA, setDriverA] = useState<string>('VER');
    const [driverB, setDriverB] = useState<string>(''); // Comparison
    const [dataA, setDataA] = useState<TheoreticalData | null>(null);
    const [dataB, setDataB] = useState<TheoreticalData | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Sync with global selection
    useEffect(() => {
        if (selectedDriver) setDriverA(selectedDriver);
        else if (session?.drivers?.length) setDriverA(session.drivers[0].code);
    }, [selectedDriver, session]);

    // Fetch Data Logic
    useEffect(() => {
        if (!session || !driverA) return;
        setIsLoading(true);

        const p1 = api.get(`/analysis/theoretical_best/${driverA}`).then(res => setDataA(res.data)).catch(console.error);
        const p2 = driverB ? api.get(`/analysis/theoretical_best/${driverB}`).then(res => setDataB(res.data)).catch(console.error) : Promise.resolve(setDataB(null));

        Promise.all([p1, p2]).finally(() => setIsLoading(false));
    }, [session, driverA, driverB]);

    if (isLoading && !dataA) return <div className="h-full flex items-center justify-center text-text-secondary">Calculating...</div>;
    if (!dataA || !dataA.segments) return <div className="h-full flex items-center justify-center text-text-secondary">No Data Available</div>;

    // Helper to format time
    const fmtTime = (s: number) => {
        const m = Math.floor(s / 60);
        const sec = (s % 60).toFixed(3);
        return `${m}:${sec.padStart(6, '0')}`;
    };

    // Color Logic for Map (based on Driver A)
    const getColor = (loss: number) => {
        if (loss <= 0.02) return '#22c55e'; // Green (Good)
        if (loss <= 0.1) return '#eab308'; // Yellow (Minor loss)
        return '#ef4444'; // Red (Major loss)
    };

    const traces: Partial<Plotly.PlotData>[] = dataA.segments.map(seg => ({
        x: seg.x,
        y: seg.y,
        mode: 'lines',
        type: 'scatter',
        line: {
            color: getColor(seg.time_lost),
            width: 4
        },
        hoverinfo: 'text',
        text: `Sector ${seg.sector_index}<br>Loss: +${seg.time_lost.toFixed(3)}s`
    }));

    // Bounding Box Logic? Plotly handles it with scaleanchor

    return (
        <div className="w-full h-full flex flex-col relative group">
            {/* Controls Overlay */}
            <div className="absolute top-2 right-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 rounded p-1 flex gap-2">
                <select
                    className="bg-[#1C1C1E] text-white text-xs p-1 rounded border border-white/10 outline-none"
                    value={driverB}
                    onChange={e => setDriverB(e.target.value)}
                >
                    <option value="">Compare...</option>
                    {session?.drivers.map((d: any) => (
                        <option key={d.code} value={d.code} disabled={d.code === driverA}>
                            {d.code}
                        </option>
                    ))}
                </select>
            </div>

            {/* Stats Overlay */}
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
                {/* Driver A Stats */}
                <div className="bg-black/60 p-2 rounded backdrop-blur-sm border border-white/10 text-xs sm:text-sm shadow-lg">
                    <div className="font-bold text-white mb-1 border-b border-white/20 pb-1 flex justify-between">
                        <span>{dataA.driver} Analysis</span>
                        {/* If B exists, maybe show delta? */}
                    </div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                        <span className="text-text-muted">Actual:</span>
                        <span className="font-mono text-white text-right">{fmtTime(dataA.actual_best)}</span>
                        <span className="text-text-muted">Theoretical:</span>
                        <span className="font-mono text-green-400 text-right">{fmtTime(dataA.theoretical_best)}</span>
                        <span className="text-text-muted">Gain:</span>
                        <span className="font-mono text-red-400 text-right">-{dataA.diff.toFixed(3)}s</span>
                    </div>
                </div>

                {/* Driver B Stats */}
                {dataB && (
                    <div className="bg-black/60 p-2 rounded backdrop-blur-sm border border-white/10 text-xs sm:text-sm shadow-lg">
                        <div className="font-bold text-gray-300 mb-1 border-b border-white/20 pb-1 flex justify-between">
                            <span>{dataB.driver} Analysis</span>
                            <span className={dataB.theoretical_best < dataA.theoretical_best ? "text-green-400" : "text-red-400"}>
                                {dataB.theoretical_best < dataA.theoretical_best ? "-" : "+"}{Math.abs(dataB.theoretical_best - dataA.theoretical_best).toFixed(3)}s
                            </span>
                        </div>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                            <span className="text-text-muted">Actual:</span>
                            <span className="font-mono text-gray-300 text-right">{fmtTime(dataB.actual_best)}</span>
                            <span className="text-text-muted">Theoretical:</span>
                            <span className="font-mono text-green-400/80 text-right">{fmtTime(dataB.theoretical_best)}</span>
                            <span className="text-text-muted">Gain:</span>
                            <span className="font-mono text-red-400/80 text-right">-{dataB.diff.toFixed(3)}s</span>
                        </div>
                    </div>
                )}
            </div>

            <Plot
                data={traces}
                layout={{
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    showlegend: false,
                    margin: { l: 20, r: 20, t: 20, b: 20 },
                    xaxis: { showgrid: false, zeroline: false, showticklabels: false, visible: false },
                    yaxis: { showgrid: false, zeroline: false, showticklabels: false, visible: false, scaleanchor: 'x', scaleratio: 1 },
                    hovermode: 'closest',
                    dragmode: false
                }}
                useResizeHandler
                className="w-full h-full"
                config={{ displayModeBar: false }}
            />

            {/* Legend */}
            <div className="absolute bottom-2 right-4 z-10 flex gap-3 text-xs font-bold bg-black/40 p-1 rounded pointer-events-none">
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500"></span> Optimal</div>
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500"></span> Minor</div>
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"></span> Major</div>
            </div>
        </div>
    );
}
