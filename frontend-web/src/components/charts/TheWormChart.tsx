"use client";

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useF1Store } from '@/store/useF1Store';
// Import Plotly dynamically to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface GapData {
    lap: number;
    gap: number;
    position: number;
}

interface DriverGaps {
    driver: string;
    color: string;
    data: GapData[];
}

export function TheWormChart() {
    const { session } = useF1Store();
    const [data, setData] = useState<DriverGaps[]>([]);

    useEffect(() => {
        if (!session) return;

        // Reset data when session changes to trigger loading state
        setData([]);

        api.get('/race/gaps')
            .then(res => setData(res.data || []))
            .catch(console.error);
    }, [session]);

    if (!data.length) return <div className="text-white/50 text-sm flex items-center justify-center h-full">Loading Race Gaps...</div>;

    const traces = data.map(d => ({
        x: d.data.map(p => p.lap),
        y: d.data.map(p => p.gap),
        text: d.data.map(p => p.position),
        type: 'scatter',
        mode: 'lines',
        name: d.driver,
        line: { color: d.color, width: 2 },
        hovertemplate: '<b>%{fullData.name}</b> P%{text}   +%{y:.2f}s<extra></extra>'
    }));

    return (
        <div className="w-full h-full p-4 bg-card rounded-xl flex flex-col">
            <h3 className="text-white font-bold mb-4">Race Gaps (The Worm)</h3>
            <div className="flex-1 min-h-0 relative">
                <Plot
                    data={traces as any}
                    layout={{
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        margin: { t: 10, r: 10, l: 40, b: 40 },
                        font: { family: 'Inter, sans-serif', color: '#8E8E93' },
                        xaxis: {
                            title: { text: 'Lap Number' },
                            showgrid: false,
                            zeroline: false,
                            gridcolor: '#333',
                            range: session ? [1, session.totalLaps] : undefined,
                            showspikes: true,
                            spikemode: 'across'
                        },
                        yaxis: {
                            title: { text: 'Gap to Leader (s)' },
                            autorange: 'reversed', // Leader (0) at Top
                            showgrid: true,
                            gridcolor: '#333'
                        },
                        hovermode: 'x unified',
                        showlegend: true,
                        legend: { orientation: 'h', y: -0.2 }
                    }}
                    useResizeHandler={true}
                    style={{ width: '100%', height: '100%', minHeight: '500px' }}
                    config={{ displayModeBar: false }}
                />
            </div>
        </div>
    );
}
