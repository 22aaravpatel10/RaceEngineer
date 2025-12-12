'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';

// Dynamic import to avoid SSR issues with Plotly
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface Corner {
    number: number;
    distance: number;
}

interface TelemetryTraceProps {
    driver: string;
    color: string;
    distance: number[];
    speed: number[];
    throttle: number[];
    brake: number[];
    corners?: Corner[];
    brakingZones?: number[][];
}

export function TelemetryTrace({
    driver,
    color,
    distance,
    speed,
    throttle,
    brake,
    corners = [],
    brakingZones = [],
}: TelemetryTraceProps) {
    const { data, layout } = useMemo(() => {
        // Speed trace
        const traceSpeed = {
            x: distance,
            y: speed,
            type: 'scatter' as const,
            mode: 'lines' as const,
            name: 'Speed',
            line: { color, width: 2.5 },
        };

        // Throttle trace (secondary axis)
        const traceThrottle = {
            x: distance,
            y: throttle,
            type: 'scatter' as const,
            mode: 'lines' as const,
            name: 'Throttle',
            yaxis: 'y2',
            line: { color: '#30D158', width: 1 },
            fill: 'tozeroy' as const,
            opacity: 0.3,
        };

        // Corner lines (shapes)
        const shapes = [
            ...corners.map((corner) => ({
                type: 'line' as const,
                x0: corner.distance,
                x1: corner.distance,
                y0: 0,
                y1: 1,
                xref: 'x' as const,
                yref: 'paper' as const,
                line: { color: '#444', width: 1, dash: 'dot' as const },
            })),
            ...brakingZones.map((zone) => ({
                type: 'rect' as const,
                x0: zone[0],
                x1: zone[1],
                y0: 0,
                y1: 1,
                xref: 'x' as const,
                yref: 'paper' as const,
                fillcolor: 'rgba(255, 59, 48, 0.1)',
                line: { width: 0 },
            })),
        ];

        // Corner annotations
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
            margin: { t: 40, r: 20, l: 50, b: 50 },
            xaxis: {
                showgrid: false,
                zeroline: false,
                color: '#444',
                title: {
                    text: 'Track Distance (meters)',
                    font: { color: '#CCC', size: 12 }
                },
            },
            yaxis: {
                showgrid: false,
                zeroline: false,
                color: '#444',
                title: {
                    text: 'Speed (km/h)',
                    font: { color: '#CCC', size: 12 }
                },
            },
            yaxis2: {
                overlaying: 'y' as const,
                side: 'right' as const,
                showgrid: false,
                range: [0, 110],
                visible: false,
            },
            showlegend: false,
            hovermode: 'x unified' as const,
            shapes,
            annotations,
            title: {
                text: `${driver} Telemetry Analysis`,
                font: { color: '#FFF', size: 14 },
            },
        };

        return { data: [traceSpeed, traceThrottle], layout: chartLayout };
    }, [driver, color, distance, speed, throttle, corners, brakingZones]);

    return (
        <Plot
            data={data}
            layout={layout}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%', height: '100%' }}
        />
    );
}
