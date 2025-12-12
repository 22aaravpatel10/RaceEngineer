"use client";
import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useF1Store } from '@/store/useF1Store';
import { api } from '@/lib/api';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export function ConsistencyBoxPlot() {
    const { session } = useF1Store();
    const [data, setData] = useState<any[]>([]);

    useEffect(() => {
        if (!session) return;
        api.get('/analysis/consistency')
            .then(res => setData(res.data?.data || []))
            .catch(err => {
                console.error(err);
                setData([]);
            });
    }, [session]);

    const traces = data.map((d) => ({
        y: d.lapTimes,
        type: 'box',
        name: d.driver,
        marker: { color: d.color },
        boxpoints: 'outliers',
    }));

    return (
        <div className="w-full h-full flex flex-col p-2">
            <h3 className="text-white font-bold mb-2">
                Lap Time Consistency
            </h3>
            <div className="flex-1 min-h-0">
                <Plot
                    data={traces as any}
                    layout={{
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#888', family: 'Inter, sans-serif' },
                        margin: { t: 10, r: 10, b: 40, l: 50 },
                        showlegend: false,
                        xaxis: {
                            title: 'Driver',
                            gridcolor: '#333',
                            tickfont: { size: 10 }
                        },
                        yaxis: {
                            title: 'Lap Time (s)',
                            gridcolor: '#333',
                            autorange: 'reversed' // Faster times (lower) at the top
                        }
                    }}
                    style={{ width: '100%', height: '100%' }}
                    useResizeHandler={true}
                    config={{ displayModeBar: true, modeBarButtons: [['toImage']] }}
                />
            </div>
        </div>
    );
}
