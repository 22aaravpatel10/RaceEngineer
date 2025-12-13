"use client";

import React, { useEffect, useState } from 'react';
import { useF1Store } from '@/store/useF1Store';
import { api } from '@/lib/api';

interface DriverSpeedHeatmap {
    driver: string;
    team: string;
    color: string;
    top_speeds: number[];
    average: number;
    max_speed: number;
}

interface Props {
    page?: number;
    limit?: number;
}

export default function TopSpeedChart({ page, limit }: Props) {
    const { session } = useF1Store();
    const [data, setData] = useState<DriverSpeedHeatmap[]>([]);
    const [metric, setMetric] = useState<string>('SpeedST');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if (!session) return;
        setIsLoading(true);

        api.get('/race/topspeed')
            .then(res => {
                setData(res.data.data || []);
                setMetric(res.data.metric || 'SpeedST');
            })
            .catch(console.error)
            .finally(() => setIsLoading(false));
    }, [session]);

    if (isLoading) return <div className="h-full flex items-center justify-center text-text-secondary">Loading Speed Data...</div>;
    if (!data.length) return <div className="h-full flex items-center justify-center text-text-secondary">No Speed Data Available for this Session</div>;

    // Calculate Global Min/Max for Color Scale
    let globalMax = 0;
    let globalMin = Infinity;

    data.forEach(d => {
        if (d.max_speed > globalMax) globalMax = d.max_speed;
        d.top_speeds.forEach(s => {
            if (s < globalMin) globalMin = s;
        });
    });

    if (globalMin === globalMax) globalMin = globalMax - 10;

    const getCellColor = (speed: number) => {
        const ratio = (speed - globalMin) / (globalMax - globalMin);
        let r, g, b;

        if (ratio < 0.5) {
            const t = ratio * 2;
            r = Math.round(76 + (234 - 76) * t);
            g = Math.round(29 + (88 - 29) * t);
            b = Math.round(149 + (12 - 149) * t);
        } else {
            const t = (ratio - 0.5) * 2;
            r = Math.round(234 + (250 - 234) * t);
            g = Math.round(88 + (204 - 88) * t);
            b = Math.round(12 + (21 - 12) * t);
        }
        return `rgb(${r}, ${g}, ${b})`;
    };

    // Pagination Logic
    const displayData = (page && limit)
        ? data.slice((page - 1) * limit, (page - 1) * limit + limit)
        : data;

    return (
        <div className="w-full h-full flex flex-col p-4 overflow-hidden chart-loaded">
            <h3 className="text-white text-md mb-4 font-bold">
                Top 15 Speeds ({metric === 'SpeedST' ? 'Speed Trap' : metric})
            </h3>

            <div className="w-full flex-1 min-h-[0] overflow-hidden">
                <table className="w-full text-xs border-collapse h-full">
                    <thead>
                        <tr className="h-8">
                            <th className="p-1 text-left text-text-muted">Driver</th>
                            {Array.from({ length: 15 }).map((_, i) => (
                                <th key={i} className="p-1 text-center text-text-muted">{i + 1}</th>
                            ))}
                            <th className="p-1 text-center text-text-muted font-bold border-l border-white/20">Avg</th>
                        </tr>
                    </thead>
                    <tbody>
                        {displayData.map(driver => (
                            <tr key={driver.driver} className="border-b border-white/5 last:border-0 hover:bg-white/5 h-[10%]">
                                {/* Driver Name */}
                                <td className="p-1 font-bold">
                                    <div className="flex items-center gap-2">
                                        <span className="w-1 h-4 rounded-full" style={{ backgroundColor: driver.color }}></span>
                                        {driver.driver}
                                    </div>
                                </td>

                                {/* Top 15 Speed Cells */}
                                {Array.from({ length: 15 }).map((_, i) => {
                                    const speed = driver.top_speeds[i];
                                    if (!speed) return <td key={i} className="p-0.5 bg-card/20 text-center">-</td>;

                                    const bgColor = getCellColor(speed);
                                    const textColor = speed > (globalMax - 5) ? '#000' : '#fff';

                                    return (
                                        <td key={i} className="p-0.5">
                                            <div
                                                className="w-full h-full flex items-center justify-center rounded text-[10px] sm:text-xs font-medium"
                                                style={{ backgroundColor: bgColor, color: textColor }}
                                            >
                                                {Math.round(speed)}
                                            </div>
                                        </td>
                                    );
                                })}

                                {/* Average Column */}
                                <td className="p-1 border-l border-white/20">
                                    <div className="text-center font-bold text-yellow-400">
                                        {Math.round(driver.average)}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Legend / Info */}
            <div className="mt-4 flex flex-row items-center justify-between text-xs text-text-muted/60 h-8">
                <span>Fastest 15 Laps (Sorted Descending)</span>
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-[#4c1d95] rounded"></span> Slow
                    <span className="w-3 h-3 bg-[#ea580c] rounded"></span> Mid
                    <span className="w-3 h-3 bg-[#facc15] rounded"></span> Fast
                </div>
            </div>
        </div>
    );
}
