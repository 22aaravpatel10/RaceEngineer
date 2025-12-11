'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { getCompoundColor } from '@/lib/utils';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface LapData {
    lapNumber: number;
    lapTime: number;
    compound: string;
}

interface RacePaceChartProps {
    driver: string;
    laps: LapData[];
    color: string;
}

export function RacePaceChart({ driver, laps, color }: RacePaceChartProps) {
    const { data, layout } = useMemo(() => {
        // Filter valid laps
        const validLaps = laps.filter((lap) => lap.lapTime > 0 && !lap.lapTime.toString().includes('NaN'));

        const trace = {
            x: validLaps.map((l) => l.lapNumber),
            y: validLaps.map((l) => l.lapTime),
            type: 'scatter' as const,
            mode: 'markers+lines' as const,
            marker: {
                size: 10,
                color: validLaps.map((l) => getCompoundColor(l.compound)),
                line: { color: '#FFF', width: 1 },
            },
            line: { color: '#333', width: 1, dash: 'dot' as const },
            text: validLaps.map((l) => l.compound),
            hovertemplate: 'Lap %{x}<br>%{y:.2f}s<br>%{text}<extra></extra>',
        };

        const chartLayout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: '-apple-system', color: '#8E8E93' },
            margin: { t: 50, r: 20, l: 50, b: 40 },
            xaxis: {
                showgrid: false,
                zeroline: false,
                color: '#444',
                title: { text: 'Lap Number', font: { color: '#8E8E93' } },
            },
            yaxis: {
                showgrid: false,
                zeroline: false,
                color: '#444',
                title: { text: 'Lap Time (s)', font: { color: '#8E8E93' } },
            },
            showlegend: false,
            title: {
                text: `${driver} Race Pace`,
                font: { color: '#FFF', size: 14 },
            },
        };

        return { data: [trace], layout: chartLayout };
    }, [driver, laps]);

    return (
        <Plot
            data={data}
            layout={layout}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%', height: '100%' }}
        />
    );
}
