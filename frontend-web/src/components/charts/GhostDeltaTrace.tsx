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
}

export function GhostDeltaTrace() {
    const { session, selectedDriver } = useF1Store();
    const [data, setData] = useState<GhostData | null>(null);
    const [referenceDriver, setReferenceDriver] = useState<string>("VER"); // Default ref to Pole/VER

    useEffect(() => {
        if (!selectedDriver) return;
        // In Quali, often compare to Pole. 
        // For now, let's try to find Pole position driver or default to VER.
        let ref = "VER";
        if (session && session.drivers.length > 0) {
            ref = session.drivers[0].code; // Pole sitter
        }
        if (ref === selectedDriver && session && session.drivers.length > 1) {
            ref = session.drivers[1].code; // Compare to P2 if selected is P1
        }
        setReferenceDriver(ref);

        api.get(`/analysis/ghost/${selectedDriver}/${ref}`)
            .then(res => setData(res.data))
            .catch(console.error);
    }, [selectedDriver, session]);

    if (!selectedDriver || !data) return null;

    return (
        <div className="w-full h-full p-4 bg-card rounded-xl">
            <h3 className="text-white font-bold mb-4">Ghost Delta: {selectedDriver} vs {referenceDriver}</h3>
            <div className="w-full h-[300px]">
                <Plot
                    data={[
                        {
                            x: data.distance,
                            y: data.delta,
                            type: 'scatter',
                            mode: 'lines',
                            name: `Delta (s)`,
                            line: { color: '#0A84FF', width: 2 },
                            fill: 'tozeroy', // Optional: fill to zero
                            fillcolor: 'rgba(10, 132, 255, 0.1)'
                        }
                    ]}
                    layout={{
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        margin: { t: 10, r: 10, l: 50, b: 40 },
                        font: { family: 'Inter, sans-serif', color: '#8E8E93' },
                        xaxis: {
                            title: { text: 'Distance (m)' },
                            showgrid: false
                        },
                        yaxis: {
                            title: { text: `Delta to ${referenceDriver} (s)` },
                            showgrid: true,
                            gridcolor: '#333',
                            zeroline: true,
                            zerolinecolor: '#FFF',
                            zerolinewidth: 1
                        },
                        showlegend: false
                    }}
                    useResizeHandler={true}
                    style={{ width: '100%', height: '100%' }}
                    config={{ displayModeBar: false }}
                />
            </div>
        </div>
    );
}
