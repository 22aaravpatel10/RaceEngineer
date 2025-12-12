'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface GapToLeaderProps {
    drivers: Record<string, { gaps: { lap: number; gapToLeader: number | null }[]; color: string }>;
    maxLap: number;
}

export function GapToLeader({ drivers, maxLap }: GapToLeaderProps) {
    const { data, layout } = useMemo(() => {
        const traces = Object.entries(drivers).map(([code, driverData]) => ({
            x: driverData.gaps.map((g) => g.lap),
            y: driverData.gaps.map((g) => g.gapToLeader ?? 0),
            type: 'scatter' as const,
            mode: 'lines' as const,
            name: code,
            line: { color: driverData.color, width: 2 },
        }));

        const chartLayout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: '-apple-system', color: '#8E8E93' },
            margin: { t: 50, r: 20, l: 50, b: 40 },
            xaxis: {
                showgrid: false,
                zeroline: false,
                color: '#444',
                title: { text: 'Lap', font: { color: '#8E8E93' } },
                range: [1, maxLap],
            },
            yaxis: {
                showgrid: false,
                zeroline: false,
                color: '#444',
                title: { text: 'Gap to Leader (s)', font: { color: '#8E8E93' } },
            },
            showlegend: true,
            legend: { x: 0, y: 1, font: { color: 'white' }, bgcolor: 'rgba(0,0,0,0)' },
            hovermode: 'x unified' as const,
            title: {
                text: 'Gap to Leader Evolution',
                font: { color: '#FFF', size: 14 },
            },
        };

        return { data: traces, layout: chartLayout };
    }, [drivers, maxLap]);

    return (
        <Plot
            data={data}
            layout={layout}
            config={{ displayModeBar: true, modeBarButtons: [['toImage']], responsive: true }}
            style={{ width: '100%', height: '100%' }}
        />
    );
}
