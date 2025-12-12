import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { useF1Store } from '@/store/useF1Store';
import { api } from '@/lib/api';

interface SpeedPoint {
    lap: number;
    speed: number;
}

interface DriverSpeedData {
    driver: string;
    color: string;
    data: SpeedPoint[];
}

export default function TopSpeedChart() {
    const { session, selectedDriver } = useF1Store();
    const [data, setData] = useState<DriverSpeedData[]>([]);
    const [metric, setMetric] = useState<string>('SpeedST');

    useEffect(() => {
        if (!session) return;

        api.get('/race/topspeed')
            .then(res => {
                setData(res.data.data || []);
                setMetric(res.data.metric || 'SpeedST');
            })
            .catch(console.error);
    }, [session]);

    if (!data.length) return <div className="h-full flex items-center justify-center text-text-secondary">Loading Speed Data...</div>;

    // Filter logic: Show selected driver + Top 3 fastest overall? Or just all?
    // "The Worm" shows all. Let's try showing all but highlighting selected.

    // Create Traces
    const traces: Partial<Plotly.PlotData>[] = data.map(d => {
        const isSelected = selectedDriver === d.driver;
        const opacity = selectedDriver ? (isSelected ? 1 : 0.1) : 0.8;
        const width = isSelected ? 3 : 1.5;

        return {
            x: d.data.map(p => p.lap),
            y: d.data.map(p => p.speed),
            type: 'scatter',
            mode: 'lines', // Lines only for cleaner look
            name: d.driver,
            line: {
                color: d.color,
                width: width
            },
            opacity: opacity,
            hovertemplate: `<b>${d.driver}</b><br>Lap %{x}<br>Speed: %{y:.1f} km/h<extra></extra>`
        };
    });

    return (
        <Plot
            data={traces}
            layout={{
                title: {
                    text: `Top Speed Evolution (${metric === 'SpeedST' ? 'Speed Trap' : metric})`,
                    font: { color: '#fff' }
                },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { family: 'Inter, sans-serif' },
                xaxis: {
                    title: 'Lap Number',
                    color: '#888',
                    gridcolor: '#333',
                    zerolinecolor: '#333'
                },
                yaxis: {
                    title: 'Speed (km/h)',
                    color: '#888',
                    gridcolor: '#333',
                    zerolinecolor: '#333'
                },
                hovermode: 'x unified',
                margin: { l: 50, r: 20, t: 40, b: 40 },
                showlegend: false, // Too many drivers
                height: 350
            }}
            useResizeHandler
            className="w-full h-full"
            config={{ responsive: true, displayModeBar: false }}
        />
    );
}
