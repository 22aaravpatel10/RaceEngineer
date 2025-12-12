'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { TelemetryTrace } from '@/components/charts/TelemetryTrace';
import { useF1Store } from '@/store/useF1Store';
import { api } from '@/lib/api';

interface LapOption {
    lapNumber: number;
    lapTime: number;
    compound: string;
    tyreLife: number;
    isPersonalBest: boolean;
}

export default function MultiLapTelemetryChart() {
    const { session, selectedDriver } = useF1Store();
    const [laps, setLaps] = useState<LapOption[]>([]);
    const [selectedLap, setSelectedLap] = useState<number | null>(null);
    const [telemetry, setTelemetry] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Active driver (fallback to first in session)
    const activeDriver = selectedDriver || (session?.drivers[0]?.code || 'VER');

    // 1. Fetch Lap List when Driver changes
    useEffect(() => {
        if (!activeDriver || !session) return;

        const fetchLaps = async () => {
            try {
                const res = await api.get(`/telemetry/driver/${activeDriver}`);
                const allLaps = res.data.laps;

                // Filter valid laps
                const validLaps = allLaps.filter((l: any) => l.lapTime > 0);

                // Sort by Lap Number (chronological) or LapTime? 
                // Chronological is better for "selecting lap X", but we want to highlight fastest.
                validLaps.sort((a: any, b: any) => a.lapNumber - b.lapNumber);

                setLaps(validLaps);

                // Default to fastest lap
                if (validLaps.length > 0) {
                    const fastest = validLaps.reduce((prev: any, curr: any) =>
                        (curr.lapTime < prev.lapTime ? curr : prev), validLaps[0]
                    );
                    setSelectedLap(fastest.lapNumber);
                }
            } catch (err: any) {
                console.error("Failed to load driver laps:", err);
                setError("Failed to load laps");
            }
        };

        fetchLaps();
    }, [activeDriver, session]);

    // 2. Fetch Telemetry when Selected Lap changes
    useEffect(() => {
        if (!activeDriver || !selectedLap) return;

        const fetchTelemetry = async () => {
            setIsLoading(true);
            setTelemetry(null);
            setError(null);
            try {
                const res = await api.get(`/telemetry/lap/${activeDriver}/${selectedLap}`);
                setTelemetry(res.data);
            } catch (err: any) {
                console.error("Telemetry fetch failed:", err);
                setError("Failed to load telemetry for this lap");
            } finally {
                setIsLoading(false);
            }
        };

        fetchTelemetry();
    }, [activeDriver, selectedLap]);

    // Format Lap Time
    const fmtTime = (seconds: number) => {
        const m = Math.floor(seconds / 60);
        const s = (seconds % 60).toFixed(3);
        return `${m}:${s.padStart(6, '0')}`;
    };

    return (
        <div className="w-full h-full p-4 flex flex-col relative group">
            <div className="flex justify-between items-center mb-1 z-20 relative">
                <h3 className="text-white font-bold opacity-0">.</h3>

                {/* Controls */}
                <div className="flex items-center gap-2 bg-black/40 p-1 rounded backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="text-sm text-text-secondary">Lap:</span>
                    <select
                        className="bg-[#1C1C1E] text-white text-sm p-1 rounded border border-white/10 outline-none focus:border-accent max-w-[200px]"
                        value={selectedLap || ''}
                        onChange={(e) => setSelectedLap(Number(e.target.value))}
                        disabled={laps.length === 0}
                    >
                        {laps.map(lap => (
                            <option key={lap.lapNumber} value={lap.lapNumber}>
                                Lap {lap.lapNumber} - {fmtTime(lap.lapTime)} ({lap.compound}) {lap.isPersonalBest ? 'PB 🚀' : ''}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="flex-grow min-h-0 relative">
                {isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10 backdrop-blur-[2px]">
                        <span className="text-accent animate-pulse">Loading Lap {selectedLap}...</span>
                    </div>
                )}

                {error && (
                    <div className="absolute inset-0 flex items-center justify-center text-red-400">
                        {error}
                    </div>
                )}

                {!telemetry && !isLoading && !error && (
                    <div className="absolute inset-0 flex items-center justify-center text-text-secondary">
                        Select a driver/lap to begin
                    </div>
                )}

                {telemetry && (
                    <TelemetryTrace
                        driver={activeDriver}
                        color={telemetry.color || '#30D158'}
                        distance={telemetry.distance}
                        speed={telemetry.speed}
                        throttle={telemetry.throttle}
                        brake={telemetry.brake}
                        corners={telemetry.corners}
                        brakingZones={telemetry.brakingZones}
                    />
                )}
            </div>
        </div>
    );
}
