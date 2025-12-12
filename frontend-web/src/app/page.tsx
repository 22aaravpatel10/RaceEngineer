'use client';

import { useEffect, useState } from 'react';
import { useF1Store } from '@/store/useF1Store';
import { initSession, getDriverLaps, getLapTelemetry } from '@/lib/api';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { CHART_REGISTRY } from '@/lib/chartRegistry';
import { cn } from '@/lib/utils';

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
    const { session, setSession, setLoading, isLoading, selectedDriver, activeCharts, setDriverLaps, driverLaps, selectedYear, selectedGP, selectedSessionType } = useF1Store();
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
                <div className="flex-1 overflow-y-auto p-2">
                    {!selectedDriver ? (
                        <div className="h-full flex flex-col items-center justify-center text-text-secondary bg-card/50 rounded-xl border-2 border-dashed border-white/5 gap-4">
                            <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center">
                                <span className="text-3xl">🏎️</span>
                            </div>
                            <p>Select a driver from the sidebar to start analysis</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pb-20">
                            {activeCharts.length === 0 && (
                                <div className="col-span-full h-64 flex items-center justify-center text-text-secondary">
                                    No charts selected. Open the sidebar menu to enable charts.
                                </div>
                            )}

                            {activeCharts.map(chartId => {
                                const chartDef = CHART_REGISTRY.find(c => c.id === chartId);
                                if (!chartDef) return null;

                                const ChartComponent = chartDef.component;

                                // Special props for some charts if needed
                                const props: any = {};
                                if (chartId === 'telemetry_trace' || chartId === 'quali_telemetry') {
                                    if (!telemetry) return <div key={chartId} className="h-[400px] flex items-center justify-center bg-card rounded-xl">Loading Telemetry...</div>;
                                    props.driver = telemetry.driver;
                                    props.color = telemetry.color;
                                    props.distance = telemetry.distance;
                                    props.speed = telemetry.speed;
                                    props.throttle = telemetry.throttle;
                                    props.brake = telemetry.brake;
                                    props.corners = telemetry.corners;
                                    props.brakingZones = telemetry.brakingZones;
                                }
                                if (chartId === 'race_pace_sim') {
                                    if (driverLaps.length === 0) return null;
                                    props.laps = driverLaps;
                                    props.driver = selectedDriver;
                                    props.color = driverColor;
                                }

                                return (
                                    <div
                                        key={chartId}
                                        className={cn(
                                            chartDef.gridCols || "col-span-1",
                                            chartDef.height || "h-[350px]"
                                        )}
                                    >
                                        <ChartComponent {...props} />
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </main>
    );
}
