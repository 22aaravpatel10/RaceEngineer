import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: `${API_BASE}/api`,
    timeout: 60000, // FastF1 can be slow on first load
});

// Session
export async function initSession(year: number, gp: string, session: string) {
    const { data } = await api.get('/session/init', {
        params: { year, gp, session }
    });
    return data;
}

// Driver Laps
export async function getDriverLaps(driverCode: string) {
    const { data } = await api.get(`/telemetry/driver/${driverCode}`);
    return data;
}

// Lap Telemetry
export async function getLapTelemetry(driverCode: string, lapNumber: number) {
    const { data } = await api.get(`/telemetry/lap/${driverCode}/${lapNumber}`);
    return data;
}

// Race Gaps
export async function getRaceGaps() {
    const { data } = await api.get('/race/gaps');
    return data;
}

// Pit Stops
export async function getPitStops() {
    const { data } = await api.get('/race/pitstops');
    return data;
}

// Compare Drivers
export async function compareDrivers(driver1: string, driver2: string) {
    const { data } = await api.get(`/compare/${driver1}/${driver2}`);
    return data;
}
