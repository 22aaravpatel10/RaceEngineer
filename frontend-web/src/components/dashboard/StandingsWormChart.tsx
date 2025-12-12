"use client";

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Trophy, Users } from 'lucide-react';

// Import Plotly dynamically
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface PointData {
    round: number;
    points: number;
}

interface StandingEntity {
    name: string;
    color: string;
    total: number;
    data: PointData[];
}

interface StandingsData {
    drivers: StandingEntity[];
    constructors: StandingEntity[];
}

interface StandingsWormChartProps {
    year: number;
    round: number;
}

export function StandingsWormChart({ year, round }: StandingsWormChartProps) {
    const [data, setData] = useState<StandingsData | null>(null);
    const [mode, setMode] = useState<'drivers' | 'constructors'>('drivers');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!year || !round) return;
        setLoading(true);

        api.get(`/weekend/standings/${year}/${round}`)
            .then(res => {
                setData(res.data.data);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [year, round]);

    if (loading) return <div className="p-8 text-center text-white/50 animate-pulse">Loading Championship History...</div>;
    if (!data) return null;

    const entities = mode === 'drivers' ? data.drivers : data.constructors;

    const traces = entities.map(entity => ({
        x: entity.data.map(p => p.round),
        y: entity.data.map(p => p.points),
        type: 'scatter',
        mode: 'lines+markers',
        name: entity.name,
        line: { color: entity.color, width: 2 },
        marker: { size: 4 },
        hovertemplate: `<b>${entity.name}</b><br>Round %{x}<br>Points: %{y}<extra></extra>`
    }));

    return (
        <div className="w-full bg-black rounded-xl p-4 border border-white/5 shadow-lg flex flex-col gap-4">
            <div className="flex items-center justify-between">
                <h3 className="font-bold text-lg text-white flex items-center gap-2">
                    <Trophy className="text-yellow-500" size={18} />
                    Championship Battle
                </h3>

                {/* Toggle */}
                <div className="flex bg-white/10 rounded-lg p-1 gap-1">
                    <button
                        onClick={() => setMode('drivers')}
                        className={`px-3 py-1 rounded text-xs font-bold transition-colors flex items-center gap-2 ${mode === 'drivers' ? 'bg-accent text-white' : 'text-text-secondary hover:text-white'}`}
                    >
                        <Users size={14} /> Drivers
                    </button>
                    <button
                        onClick={() => setMode('constructors')}
                        className={`px-3 py-1 rounded text-xs font-bold transition-colors flex items-center gap-2 ${mode === 'constructors' ? 'bg-accent text-white' : 'text-text-secondary hover:text-white'}`}
                    >
                        <Users size={14} /> Constructors
                    </button>
                </div>
            </div>

            <div className="w-full h-[600px] relative">
                <Plot
                    data={traces as any}
                    layout={{
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        margin: { t: 10, r: 10, l: 40, b: 40 },
                        font: { family: 'Inter, sans-serif', color: '#8E8E93' },
                        xaxis: {
                            title: { text: 'Round' },
                            showgrid: false,
                            zeroline: false,
                            gridcolor: '#333',
                            range: [0.8, round + 0.2], // Pad slightly
                            dtick: 1
                        },
                        yaxis: {
                            title: { text: 'Points' },
                            showgrid: true,
                            gridcolor: '#333',
                            zeroline: true,
                            zerolinecolor: '#333'
                        },
                        hovermode: 'closest',
                        hoverlabel: {
                            bgcolor: 'rgba(0,0,0,0.8)',
                            font: { family: 'Inter, sans-serif', size: 11, color: '#FFFFFF' },
                            bordercolor: 'rgba(255,255,255,0.1)'
                        },
                        showlegend: true,
                        legend: { orientation: 'h', y: -0.15 } // Bottom legend
                    }}
                    useResizeHandler={true}
                    style={{ width: '100%', height: '100%' }}
                    config={{ displayModeBar: false }}
                />
            </div>
        </div>
    );
}
