"use client";

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useF1Store } from '@/store/useF1Store';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface FuelData {
    lap: number;
    actual: number;
    corrected: number;
    fuelLoad: number;
}

export function FuelCorrectedScatter() {
    const { selectedDriver, session } = useF1Store();
    const [data, setData] = useState<FuelData[]>([]);

    useEffect(() => {
        if (!selectedDriver) return;

        api.get(`/analysis/fuel/${selectedDriver}`)
            .then(res => setData(res.data))
            .catch(console.error);
    }, [selectedDriver]);

    if (!selectedDriver) return null;
    if (!data.length) return <div className="text-center text-text-secondary">Loading Fuel Analysis...</div>;

    return (
        <div className="w-full h-full p-4 bg-card rounded-xl">
            <h3 className="text-white font-bold mb-4">Fuel Adjusted Pace ({selectedDriver})</h3>
            <div className="w-full h-[300px]">
                <Plot
                    data={[
                        {
                            x: data.map(d => d.lap),
                            y: data.map(d => d.actual),
                            type: 'scatter',
                            mode: 'markers',
                            name: 'Actual Time',
                            marker: { color: '#8E8E93', opacity: 0.5, size: 6 }
                        },
                        {
                            x: data.map(d => d.lap),
                            y: data.map(d => d.corrected),
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Fuel Corrected (Tyre Deg)',
                            line: { color: '#30D158', width: 2 },
                            marker: { color: '#30D158', size: 4 }
                        }
                    ]}
                    layout={{
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        margin: { t: 10, r: 10, l: 50, b: 40 },
                        font: { family: 'Inter, sans-serif', color: '#8E8E93' },
                        xaxis: {
                            title: { text: 'Lap Number' },
                            showgrid: false,
                            range: session ? [1, session.totalLaps] : undefined
                        },
                        yaxis: {
                            title: { text: 'Lap Time (s)' },
                            showgrid: true,
                            gridcolor: '#333'
                        },
                        showlegend: true,
                        legend: { x: 0, y: 1 }
                    }}
                    useResizeHandler={true}
                    style={{ width: '100%', height: '100%' }}
                    config={{ displayModeBar: false }}
                />
            </div>
        </div>
    );
}
