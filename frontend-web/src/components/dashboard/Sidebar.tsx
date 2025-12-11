'use client';

import { useF1Store, SessionMode } from '@/store/useF1Store';
import { cn } from '@/lib/utils';

const modes: { id: SessionMode; label: string }[] = [
    { id: 'PRACTICE', label: 'FP' },
    { id: 'QUALI', label: 'QUALI' },
    { id: 'RACE', label: 'RACE' },
];

export function Sidebar() {
    const { session, selectedDriver, selectedMode, selectDriver, setMode } = useF1Store();

    return (
        <aside className="w-64 bg-card rounded-xl p-4 flex flex-col h-full">
            {/* Mode Switcher */}
            <div className="flex gap-1 p-1 bg-background rounded-lg mb-4">
                {modes.map((mode) => (
                    <button
                        key={mode.id}
                        onClick={() => setMode(mode.id)}
                        className={cn(
                            'flex-1 py-2 px-3 rounded-md text-xs font-bold transition-all',
                            selectedMode === mode.id
                                ? 'bg-card-hover text-white shadow'
                                : 'text-text-secondary hover:text-white'
                        )}
                    >
                        {mode.label}
                    </button>
                ))}
            </div>

            {/* Driver List */}
            <h2 className="text-text-secondary text-xs font-bold uppercase tracking-wider mb-3">
                Live Grid
            </h2>

            <div className="flex-1 overflow-y-auto space-y-1">
                {session?.drivers.map((driver) => (
                    <button
                        key={driver.code}
                        onClick={() => selectDriver(driver.code)}
                        className={cn(
                            'w-full flex items-center gap-3 p-3 rounded-lg transition-all text-left',
                            selectedDriver === driver.code
                                ? 'bg-card-hover border-l-[3px]'
                                : 'hover:bg-card-hover/50'
                        )}
                        style={{
                            borderLeftColor: selectedDriver === driver.code ? driver.color : 'transparent',
                        }}
                    >
                        <div
                            className="w-1 h-6 rounded-full"
                            style={{ backgroundColor: driver.color }}
                        />
                        <span className="font-bold text-sm">{driver.code}</span>
                        <span className="text-text-secondary text-xs ml-auto font-mono">
                            {driver.bestLap}
                        </span>
                    </button>
                ))}

                {!session && (
                    <div className="text-text-secondary text-sm text-center py-8">
                        Loading session...
                    </div>
                )}
            </div>

            {/* Session Info */}
            {session && (
                <div className="mt-4 pt-4 border-t border-card-hover">
                    <p className="text-text-secondary text-xs">
                        {session.eventName} • {session.sessionType}
                    </p>
                </div>
            )}
        </aside>
    );
}
