'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface ComparisonChartProps {
    driver1: { code: string; color: string; speed: number[] };
    driver2: { code: string; color: string; speed: number[] };
    distance: number[];
    corners?: { number: number; distance: number }[];
}

export function ComparisonChart({ driver1, driver2, distance, corners = [] }: ComparisonChartProps) {
    const { data, layout } = useMemo(() => {
        const trace1 = {
            x: distance,
            y: driver1.speed,
            type: 'scatter' as const,
            mode: 'lines' as const,
            name: driver1.code,
            line: { color: driver1.color, width: 2.5 },
        };

        const trace2 = {
            x: distance,
            y: driver2.speed,
            type: 'scatter' as const,
            mode: 'lines' as const,
            name: driver2.code,
            line: { color: driver2.color, width: 2 },
            opacity: 0.8,
        };

        const shapes = corners.map((corner) => ({
            type: 'line' as const,
            x0: corner.distance,
            x1: corner.distance,
            y0: 0,
            y1: 1,
            xref: 'x' as const,
            yref: 'paper' as const,
            line: { color: '#444', width: 1, dash: 'dot' as const },
        }));

        const annotations = corners.map((corner) => ({
            x: corner.distance,
            y: 1.05,
            xref: 'x' as const,
            yref: 'paper' as const,
            text: `T${corner.number}`,
            showarrow: false,
            font: { color: '#8E8E93', size: 10 },
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
                title: { text: 'Distance (m)', font: { color: '#8E8E93' } },
            },
            yaxis: {
                showgrid: false,
                zeroline: false,
                color: '#444',
                title: { text: 'Speed (km/h)', font: { color: '#8E8E93' } },
            },
            showlegend: true,
            legend: { x: 0, y: 1, font: { color: 'white' }, bgcolor: 'rgba(0,0,0,0)' },
            hovermode: 'x unified' as const,
            shapes,
            annotations,
            title: {
                text: `${driver1.code} vs ${driver2.code}`,
                font: { color: '#FFF', size: 14 },
            },
        };

        return { data: [trace1, trace2], layout: chartLayout };
    }, [driver1, driver2, distance, corners]);

    return (
        <Plot
            data={data}
            layout={layout}
            config={{ displayModeBar: true, modeBarButtons: [['toImage']], responsive: true }}
            style={{ width: '100%', height: '100%' }}
        />
    );
}
