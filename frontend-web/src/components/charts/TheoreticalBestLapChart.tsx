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
    const [data, setData] = useState<TheoreticalData | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Default to the first driver in the session if none selected? 
    // Usually user selects a driver. If not, maybe VER or HAM.
    const targetDriver = selectedDriver || 'VER';

    useEffect(() => {
        if (!session) return;
        setIsLoading(true);

        api.get(`/analysis/theoretical_best/${targetDriver}`)
            .then(res => {
                setData(res.data);
            })
            .catch(console.error)
            .finally(() => setIsLoading(false));
    }, [session, targetDriver]);

    if (isLoading) return <div className="h-full flex items-center justify-center text-text-secondary">Calculating Theoretical Best...</div>;
    if (!data || !data.segments) return <div className="h-full flex items-center justify-center text-text-secondary">No Data Available</div>;

    // Helper to format time
    const fmtTime = (s: number) => {
        const m = Math.floor(s / 60);
        const sec = (s % 60).toFixed(3);
        return `${m}:${sec.padStart(6, '0')}`;
    };

    // Color Logic
    // 0 loss -> Green
    // 0.1s loss -> Red
    // We can use a threshold.
    const getColor = (loss: number) => {
        if (loss <= 0.02) return '#22c55e'; // Green (Good)
        if (loss <= 0.1) return '#eab308'; // Yellow (Minor loss)
        return '#ef4444'; // Red (Major loss)
    };

    const traces: Partial<Plotly.PlotData>[] = data.segments.map(seg => ({
        x: seg.x,
        y: seg.y,
        mode: 'lines',
        type: 'scatter',
        line: {
            color: getColor(seg.time_lost),
            width: 4
        },
        name: `Sector ${seg.sector_index}`,
        hoverinfo: 'text',
        // Hover text: Sector X: +0.05s lost
        text: `Sector ${seg.sector_index}<br>Loss: +${seg.time_lost.toFixed(3)}s`
    }));

    // Find bounding box for aspect ratio
    // We want the track to look correct (aspect ratio 1:1)

    return (
        <div className="w-full h-full flex flex-col relative">
            {/* Overlay Stats */}
            <div className="absolute top-2 left-4 z-10 bg-black/60 p-2 rounded backdrop-blur-sm border border-white/10 text-xs sm:text-sm">
                <div className="font-bold text-white mb-1 border-b border-white/20 pb-1">{data.driver} Theoretical Analysis</div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                    <span className="text-text-muted">Actual Best:</span>
                    <span className="font-mono text-white text-right">{fmtTime(data.actual_best)}</span>

                    <span className="text-text-muted">Theoretical:</span>
                    <span className="font-mono text-green-400 text-right">{fmtTime(data.theoretical_best)}</span>

                    <span className="text-text-muted">Potential Gain:</span>
                    <span className="font-mono text-red-400 text-right">-{data.diff.toFixed(3)}s</span>
                </div>
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
                config={{ displayModeBar: true, responsive: true, modeBarButtons: [['toImage']] }}
            />

            {/* Legend */}
            <div className="absolute bottom-2 right-4 z-10 flex gap-3 text-xs font-bold bg-black/40 p-1 rounded">
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500"></span> Optimal</div>
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500"></span> Minor Loss</div>
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"></span> <span className="text-red-400">Major Loss</span></div>
            </div>
        </div>
    );
}
