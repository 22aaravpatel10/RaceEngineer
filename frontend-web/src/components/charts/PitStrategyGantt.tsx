'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { getCompoundColor } from '@/lib/utils';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface Stint {
    compound: string;
    startLap: number;
    endLap: number;
}

interface PitStrategyGanttProps {
    strategies: { driver: string; color: string; stints: Stint[] }[];
}

export function PitStrategyGantt({ strategies }: PitStrategyGanttProps) {
    const { data, layout } = useMemo(() => {
        const traces = strategies.flatMap((strategy) =>
            strategy.stints.map((stint) => ({
                x: [stint.endLap - stint.startLap + 1],
                y: [strategy.driver],
                type: 'bar' as const,
                orientation: 'h' as const,
                base: stint.startLap - 1,
                marker: { color: getCompoundColor(stint.compound) },
                name: stint.compound,
                showlegend: false,
                hovertemplate: `${strategy.driver}<br>${stint.compound}<br>Laps ${stint.startLap}-${stint.endLap}<extra></extra>`,
            }))
        );

        const chartLayout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { family: '-apple-system', color: '#8E8E93' },
            margin: { t: 50, r: 20, l: 60, b: 40 },
            xaxis: {
                showgrid: false,
                zeroline: false,
                color: '#444',
                title: { text: 'Lap', font: { color: '#8E8E93' } },
            },
            yaxis: {
                showgrid: false,
                zeroline: false,
                color: '#444',
                automargin: true,
            },
            barmode: 'stack' as const,
            showlegend: false,
            title: {
                text: 'Pit Strategy Timeline',
                font: { color: '#FFF', size: 14 },
            },
        };

        return { data: traces, layout: chartLayout };
    }, [strategies]);

    return (
        <Plot
            data={data}
            layout={layout}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%', height: '100%' }}
        />
    );
}
