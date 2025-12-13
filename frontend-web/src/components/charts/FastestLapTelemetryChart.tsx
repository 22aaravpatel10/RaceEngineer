'use client';

import React, { useEffect, useState } from 'react';
import { TelemetryTrace } from '@/components/charts/TelemetryTrace';
import { useF1Store } from '@/store/useF1Store';
import { api } from '@/lib/api';

// Helper to find fastest lap telemetry for a specific driver
const fetchDriverFastestLap = async (driverCode: string) => {
    // 1. Get List of Laps
    const lapsRes = await api.get(`/telemetry/driver/${driverCode}`);
    const laps = lapsRes.data.laps;
    if (!laps || laps.length === 0) throw new Error(`No laps for ${driverCode}`);

    // 2. Sort by LapTime
    const validLaps = laps.filter((l: any) => l.lapTime > 0);
    validLaps.sort((a: any, b: any) => a.lapTime - b.lapTime);
    if (validLaps.length === 0) throw new Error(`No valid laps for ${driverCode}`);

    const fastestLap = validLaps[0];
    const lapNum = fastestLap.lapNumber;

    // 3. Get Telemetry
    const telRes = await api.get(`/telemetry/lap/${driverCode}/${lapNum}`);
    return telRes.data;
};

interface Props {
    driverOverride?: string;
    comparisonOverride?: string;
}

export default function FastestLapTelemetryChart({ driverOverride, comparisonOverride }: Props) {
    const { session, selectedDriver } = useF1Store();
    const [telemetry1, setTelemetry1] = useState<any>(null);
    const [telemetry2, setTelemetry2] = useState<any>(null); // Secondary
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Primary Driver
    const activeDriver = driverOverride || selectedDriver || (session?.drivers[0]?.code || 'VER');

    // Secondary Driver (Manual or None)
    const [manualRef, setManualRef] = useState<string>("None");

    // Sync manualRef with comparisonOverride if provided
    useEffect(() => {
        if (comparisonOverride) {
            setManualRef(comparisonOverride);
        }
    }, [comparisonOverride]);

    console.log("[FastestLapTelemetry] Render. Driver:", activeDriver, "Ref:", manualRef);

    useEffect(() => {
        if (!activeDriver || !session) return;

        const fetchData = async () => {
            setIsLoading(true);
            setError(null);
            setTelemetry1(null);
            setTelemetry2(null);

            try {
                // Fetch Primary
                const data1 = await fetchDriverFastestLap(activeDriver);
                setTelemetry1(data1);

                // Fetch Secondary if selected and different
                if (manualRef !== "None" && manualRef !== activeDriver) {
                    try {
                        const data2 = await fetchDriverFastestLap(manualRef);
                        setTelemetry2(data2);
                    } catch (e) {
                        console.warn("Failed to load secondary driver data", e);
                    }
                }

            } catch (err: any) {
                console.error("Telemetry fetch failed:", err);
                setError(err.message || "Failed to load telemetry");
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [activeDriver, manualRef, session]);

    if (isLoading) {
        return <div className="h-full flex items-center justify-center text-text-secondary">Loading Telemetry...</div>;
    }

    if (error || !telemetry1) {
        return <div className="h-full flex items-center justify-center text-text-secondary">{error || "No Telemetry Data Available"}</div>;
    }

    return (
        <div className="w-full h-full p-4 flex flex-col chart-loaded">
            <div className="flex justify-between items-center mb-1">
                <h3 className="text-white font-bold opacity-0">.</h3> {/* Spacer, title in chart */}
                <div className="flex items-center gap-2 z-10 relative">
                    <span className="text-sm text-text-secondary">Compare:</span>
                    <select
                        className="bg-[#1C1C1E] text-white text-sm p-1 rounded border border-white/10 outline-none focus:border-accent"
                        value={manualRef}
                        onChange={(e) => setManualRef(e.target.value)}
                    >
                        <option value="None">None</option>
                        {session?.drivers.map(d => (
                            <option key={d.code} value={d.code}>{d.code}</option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="flex-grow min-h-0">
                <TelemetryTrace
                    driver={activeDriver}
                    color={telemetry1.color || '#30D158'}
                    distance={telemetry1.distance}
                    speed={telemetry1.speed}
                    throttle={telemetry1.throttle}
                    brake={telemetry1.brake}
                    corners={telemetry1.corners}
                    brakingZones={[]} // Optional
                    secondaryTelemetry={telemetry2 ? {
                        driver: manualRef,
                        color: telemetry2.color || '#FFD60A',
                        distance: telemetry2.distance,
                        speed: telemetry2.speed,
                        throttle: telemetry2.throttle,
                        brake: telemetry2.brake
                    } : null}
                />
            </div>
        </div>
    );
}
