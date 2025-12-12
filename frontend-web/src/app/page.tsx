'use client';

import { useEffect, useState } from 'react';
import { useF1Store } from '@/store/useF1Store';
import { initSession, getDriverLaps, getLapTelemetry } from '@/lib/api';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { TelemetryTrace } from '@/components/charts/TelemetryTrace';
import { RacePaceChart } from '@/components/charts/RacePaceChart';
import { TheWormChart } from '@/components/charts/TheWormChart';
import { FuelCorrectedScatter } from '@/components/charts/FuelCorrectedScatter';
import { GhostDeltaTrace } from '@/components/charts/GhostDeltaTrace';
import { PitRejoinGantt } from '@/components/charts/PitRejoinGantt';

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
    const { session, setSession, setLoading, isLoading, selectedDriver, selectedMode, setDriverLaps, driverLaps, selectedYear, selectedGP, selectedSessionType } = useF1Store();
    const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Load session on mount and when selection changes
    useEffect(() => {
        async function loadSession() {
            if (!selectedGP) return;
            setLoading(true);
            setSession(null); // Clear previous session to force update UI
            try {
                const data = await initSession(selectedYear, selectedGP, selectedSessionType);
                setSession(data);
            } catch (err) {
                setError('Failed to load session. Make sure the backend is running on port 8000.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        loadSession();
    }, [selectedYear, selectedGP, selectedSessionType, setSession, setLoading]);

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
            <div className="flex-1 flex flex-col gap-4 overflow-hidden">
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
                <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                    {!selectedDriver ? (
                        <div className="h-64 flex items-center justify-center text-text-secondary bg-card rounded-xl">
                            Select a driver from the sidebar to view telemetry
                        </div>
                    ) : (
                        <>
                            {selectedMode === 'QUALI' && (
                                <div className="grid grid-cols-1 gap-4">
                                    <div className="h-[400px]">
                                        {telemetry ? (
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
                                        ) : <div>Loading Telemetry...</div>}
                                    </div>
                                    <div className="h-[350px]">
                                        <GhostDeltaTrace />
                                    </div>
                                </div>
                            )}

                            {selectedMode === 'RACE' && (
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                    <div className="h-[350px] col-span-1 lg:col-span-2">
                                        <TheWormChart />
                                    </div>
                                    <div className="h-[350px]">
                                        <FuelCorrectedScatter />
                                    </div>
                                    <div className="h-[350px] col-span-1 lg:col-span-2">
                                        <PitRejoinGantt />
                                    </div>
                                </div>
                            )}

                            {selectedMode === 'PRACTICE' && (
                                <div className="h-[400px]">
                                    {driverLaps.length > 0 ? (
                                        <RacePaceChart
                                            driver={selectedDriver}
                                            laps={driverLaps}
                                            color={driverColor}
                                        />
                                    ) : <div>No Practice Data</div>}
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </main>
    );
}
