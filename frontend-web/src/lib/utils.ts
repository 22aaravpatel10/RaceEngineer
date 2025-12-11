import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatLapTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(3);
    return `${mins}:${secs.padStart(6, '0')}`;
}

export function getCompoundColor(compound: string): string {
    const colors: Record<string, string> = {
        SOFT: '#FF3B30',
        MEDIUM: '#FFCC00',
        HARD: '#FFFFFF',
        INTERMEDIATE: '#30D158',
        WET: '#0A84FF',
    };
    return colors[compound] || '#888888';
}
