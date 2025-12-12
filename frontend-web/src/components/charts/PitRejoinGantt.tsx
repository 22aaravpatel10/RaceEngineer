"use client";

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useF1Store } from '@/store/useF1Store';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface Stint {
    compound: string;
    startLap: number;
    endLap: number;
}

interface StrategyData {
    driver: string;
    color: string;
    stints: Stint[];
}

export function PitRejoinGantt() {
    const { session } = useF1Store();
    const [data, setData] = useState<StrategyData[]>([]);

    useEffect(() => {
        if (!session) return;

        api.get('/race/pitstops')
            .then(res => setData(res.data.strategies))
            .catch(console.error);
    }, [session]);

    if (!data.length) return <div className="text-center text-text-secondary">Loading Strategies...</div>;

    // Convert to Plotly traces
    // We want a stacked horizontal bar chart? Or separate bars (Gantt).
    // Better: For each driver, a horizontal line with markers/sections for compounds.
    // Plotly barh.

    // Sort drivers by finishing position? or default order
    // Reverse order so winner is at top
    // Since data comes from analysis, maybe unsorted?
    // Let's assume input is roughly grid order. 

    // Map Compound to Color
    const compoundColors: Record<string, string> = {
        "SOFT": "#FF3B30",
        "MEDIUM": "#FFCC00",
        "HARD": "#FFFFFF",
        "INTERMEDIATE": "#30D158",
        "WET": "#0A84FF",
        "UNKNOWN": "#8E8E93"
    };

    const traces: any[] = [];

    // Create a trace for each compound type to get a legend?
    // Or trace per driver per stint? (Too many traces)
    // Trace per compound type (grouping data).

    // We need to map y=driver to x_start, x_end.
    // Plotly doesn't natively do "Gantt" easily without specific shapes or timeline.
    // Use 'bar' with 'base'.

    const compounds = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"];

    compounds.forEach(comp => {
        const x: number[] = [];
        const y: string[] = [];
        const base: number[] = [];
        const text: string[] = [];

        data.forEach(d => {
            d.stints.forEach(s => {
                if (s.compound === comp) {
                    y.push(d.driver);
                    base.push(s.startLap);
                    x.push(s.endLap - s.startLap + 1);
                    text.push(`L${s.startLap}-${s.endLap}`);
                }
            });
        });

        if (x.length > 0) {
            traces.push({
                type: 'bar',
                orientation: 'h',
                name: comp,
                y: y,
                x: x,
                base: base,
                marker: { color: compoundColors[comp] || '#888', width: 0.8 },
                text: text,
                textposition: 'none',
                hoverinfo: 'x+y+name'
            });
        }
    });

    return (
        <div className="w-full h-full p-4 bg-card rounded-xl">
            <h3 className="text-white font-bold mb-4">Tyre Strategies</h3>
            <div className="w-full h-full min-h-[300px]">
                <Plot
                    data={traces}
                    layout={{
                        barmode: 'stack', // Stack to allow multiple stints per driver (actually we use base, so 'stack' or 'overlay'?)
                        // 'stack' works if we have multiple bars on same Y. 
                        // But we manually set base. 'overlay' might be safer? 
                        // Actually 'relative' (default aka stack) w/ base works.
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        margin: { t: 10, r: 10, l: 100, b: 40 }, // Increased left margin for driver names
                        font: { family: 'Inter, sans-serif', color: '#8E8E93' },
                        xaxis: {
                            title: { text: 'Lap Number' },
                            showgrid: true,
                            gridcolor: '#333',
                            range: session ? [1, session.totalLaps] : undefined
                        },
                        yaxis: {
                            title: { text: '' },
                            automargin: true,
                            type: 'category'
                        },
                        showlegend: true,
                        legend: { orientation: 'h', y: -0.1 }
                    }}
                    useResizeHandler={true}
                    style={{ width: '100%', height: '100%', minHeight: '500px' }}
                    config={{ displayModeBar: false }}
                />
            </div>
        </div>
    );
}
