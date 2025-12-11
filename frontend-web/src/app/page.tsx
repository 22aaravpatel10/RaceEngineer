'use client';

import { useEffect, useState } from 'react';
import { useF1Store } from '@/store/useF1Store';
import { initSession, getDriverLaps, getLapTelemetry } from '@/lib/api';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { TelemetryTrace } from '@/components/charts/TelemetryTrace';
import { RacePaceChart } from '@/components/charts/RacePaceChart';

interface Telemetry {
    driver: string;
    color: string;
    distance: number[];
    speed: number[];
    throttle: number[];
    brake: number[];
    corners: { number: number; distance: number }[];
    brakingZones: number[][];
}

export default function Dashboard() {
    const { session, setSession, setLoading, isLoading, selectedDriver, selectedMode, setDriverLaps, driverLaps } = useF1Store();
    const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Load session on mount
    useEffect(() => {
        async function loadSession() {
            setLoading(true);
            try {
                // Default to 2024 Bahrain Qualifying
                const data = await initSession(2024, 'Bahrain', 'Q');
                setSession(data);
            } catch (err) {
                setError('Failed to load session. Make sure the backend is running on port 5000.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        loadSession();
    }, [setSession, setLoading]);

    // Load driver data when selected
    useEffect(() => {
        async function loadDriverData() {
            if (!selectedDriver) return;

            try {
                // Get laps
                const lapsData = await getDriverLaps(selectedDriver);
                setDriverLaps(lapsData.laps);

                // Get fastest lap telemetry
                const fastestLap = lapsData.laps.reduce(
                    (min: any, lap: any) => (lap.lapTime < min.lapTime ? lap : min),
                    lapsData.laps[0]
                );

                if (fastestLap) {
                    const telemData = await getLapTelemetry(selectedDriver, fastestLap.lapNumber);
                    setTelemetry(telemData);
                }
            } catch (err) {
                console.error('Failed to load driver data:', err);
            }
        }
        loadDriverData();
    }, [selectedDriver, setDriverLaps]);

    // Get driver color
    const driverColor = session?.drivers.find((d) => d.code === selectedDriver)?.color || '#0A84FF';

    return (
        <main className="flex h-screen p-4 gap-4">
            {/* Sidebar */}
            <Sidebar />

            {/* Main Content */}
            <div className="flex-1 flex flex-col gap-4">
                {/* Header */}
                <header className="bg-card rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <h1 className="text-xl font-bold">
                            {session?.eventName || 'Loading...'}
                        </h1>
                        <span className="text-text-secondary text-sm">
                            {session?.sessionType || ''}
                        </span>
                    </div>

                    {isLoading && (
                        <div className="flex items-center gap-2 text-accent">
                            <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                            <span className="text-sm">Loading...</span>
                        </div>
                    )}

                    {error && (
                        <div className="text-accent-red text-sm">{error}</div>
                    )}
                </header>

                {/* Charts Area */}
                <div className="flex-1 bg-card rounded-xl p-4 overflow-hidden">
                    {!selectedDriver ? (
                        <div className="h-full flex items-center justify-center text-text-secondary">
                            Select a driver from the sidebar to view telemetry
                        </div>
                    ) : selectedMode === 'QUALI' && telemetry ? (
                        <TelemetryTrace
                            driver={telemetry.driver}
                            color={telemetry.color}
                            distance={telemetry.distance}
                            speed={telemetry.speed}
                            throttle={telemetry.throttle}
                            brake={telemetry.brake}
                            corners={telemetry.corners}
                            brakingZones={telemetry.brakingZones}
                        />
                    ) : selectedMode === 'PRACTICE' && driverLaps.length > 0 ? (
                        <RacePaceChart
                            driver={selectedDriver}
                            laps={driverLaps}
                            color={driverColor}
                        />
                    ) : selectedMode === 'RACE' && driverLaps.length > 0 ? (
                        <RacePaceChart
                            driver={selectedDriver}
                            laps={driverLaps}
                            color={driverColor}
                        />
                    ) : (
                        <div className="h-full flex items-center justify-center text-text-secondary">
                            Loading data...
                        </div>
                    )}
                </div>
            </div>
        </main>
    );
}
