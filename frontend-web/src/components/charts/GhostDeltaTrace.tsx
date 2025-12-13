"use client";

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useF1Store } from '@/store/useF1Store';
import { getTeamColor } from '@/lib/colors';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface GhostData {
    driver1: string;
    driver2: string;
    distance: number[];
    delta: number[];
    corners?: { number: number; distance: number }[];
}

interface Props {
    driverOverride?: string;
    comparisonOverride?: string;
}

export function GhostDeltaTrace({ driverOverride, comparisonOverride }: Props) {
    const { session, selectedDriver } = useF1Store();
    const [data, setData] = useState<GhostData | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Manual reference selection
    const [manualRef, setManualRef] = useState<string | null>(null);

    // Sync comparisonOverride
    useEffect(() => {
        if (comparisonOverride) setManualRef(comparisonOverride);
    }, [comparisonOverride]);

    // Default to a driver if none selected
    const activeDriver = driverOverride || selectedDriver || (session?.drivers[0]?.code || 'VER');

    // Compute effective reference driver
    const effectiveRef = manualRef || (() => {
        let ref = "VER";
        if (session && session.drivers.length > 0) {
            ref = session.drivers[0].code;
        }
        if (ref === activeDriver && session && session.drivers.length > 1) {
            ref = session.drivers[1].code;
        }
        return ref;
    })();

    useEffect(() => {
        if (!activeDriver || !session) return;

        setIsLoading(true);
        setData(null);

        console.log(`Fetching Ghost: ${activeDriver} vs ${effectiveRef}`);

        api.get(`/analysis/ghost/${activeDriver}/${effectiveRef}`)
            .then(res => setData(res.data))
            .catch(err => {
                console.error("Ghost error:", err);
                setData(null);
            })
            .finally(() => setIsLoading(false));
    }, [activeDriver, effectiveRef, session]);

    // Prepare Corner Shapes
    const shapes = data?.corners?.map(c => ({
        type: 'line',
        x0: c.distance,
        x1: c.distance,
        y0: 0,
        y1: 1,
        xref: 'x',
        yref: 'paper',
        line: { color: 'rgba(255, 255, 255, 0.1)', width: 1, dash: 'dot' }
    })) || [];

    const annotations = data?.corners?.map(c => ({
        x: c.distance,
        y: 0.05,
        xref: 'x',
        yref: 'paper',
        text: `T${c.number}`,
        showarrow: false,
        font: { color: 'rgba(255, 255, 255, 0.3)', size: 10 }
    })) || [];

    if (isLoading) return <div className="h-full flex items-center justify-center text-text-secondary">Loading Ghost Data...</div>;

    if (!activeDriver || !data || !data.distance) return <div className="h-full flex items-center justify-center text-text-secondary">No Ghost Data Available</div>;

    return (
        <div className="w-full h-full p-4 flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-white font-bold">Ghost Delta: {activeDriver} vs {effectiveRef}</h3>

                <div className="flex items-center gap-2">
                    <span className="text-sm text-text-secondary">Reference:</span>
                    <select
                        className="bg-[#1C1C1E] text-white text-sm p-1 rounded border border-white/10 outline-none focus:border-accent"
                        value={effectiveRef}
                        onChange={(e) => setManualRef(e.target.value)}
                    >
                        {session?.drivers.map(d => (
                            <option key={d.code} value={d.code}>{d.code}</option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="w-full flex-grow min-h-[0]">
                <Plot
                    data={[
                        {
                            x: data.distance,
                            y: data.delta,
                            type: 'scatter',
                            mode: 'lines',
                            name: `Delta (s)`,
                            line: { color: '#0A84FF', width: 2 },
                            fill: 'tozeroy',
                            fillcolor: 'rgba(10, 132, 255, 0.1)',
                            hovertemplate: `Dist: %{x}m<br>Delta: %{y:.3f}s<extra></extra>`
                        }
                    ]}
                    layout={{
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        margin: { t: 10, r: 10, l: 40, b: 30 },
                        font: { family: 'Inter, sans-serif', color: '#8E8E93' },
                        xaxis: {
                            title: { text: 'Distance (m)' },
                            showgrid: false,
                            zeroline: false
                        },
                        yaxis: {
                            title: { text: `Delta (s)` },
                            showgrid: true,
                            gridcolor: '#333',
                            zeroline: true,
                            zerolinecolor: '#FFF',
                            zerolinewidth: 1
                        },
                        showlegend: false,
                        shapes: shapes as any,
                        annotations: annotations as any
                    }}
                    useResizeHandler={true}
                    style={{ width: '100%', height: '100%' }}
                    config={{ displayModeBar: true, modeBarButtons: [['toImage']] }}
                />
            </div>
        </div>
    );
}
