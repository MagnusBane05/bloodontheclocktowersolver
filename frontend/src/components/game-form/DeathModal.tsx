import React from 'react';
import { ModalHeader } from './ModalHeader';

interface DeathModalProps {
  player: number;
  deathType: 'execution' | 'demon_kill' | null;
  dayNight: number | null;
  maxDayNight: number;
  onDeathTypeChange: (type: 'execution' | 'demon_kill') => void;
  onDayNightChange: (dayNight: number) => void;
  onConfirm: () => void;
  onClear: () => void;
  onClose: () => void;
  playerNames: string[];
}

export function DeathModal({
  player,
  deathType,
  dayNight,
  maxDayNight,
  onDeathTypeChange,
  onDayNightChange,
  onConfirm,
  onClear,
  onClose,
  playerNames,
}: DeathModalProps): JSX.Element {
  const isValid = deathType !== null && dayNight !== null && dayNight > 0;
  const isExecution = deathType === 'execution';
  const dayNightLabel = isExecution ? 'Day' : 'Night';

  const handleConfirm = () => {
    if (isValid) {
      onConfirm();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && isValid) {
      handleConfirm();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  const playerName = playerNames[player] ?? `Player ${player + 1}`;

  return (
    <div
      className="fixed inset-0 z-30 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 border border-gray-600 rounded-lg p-6 max-w-sm w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <ModalHeader content={`${playerName} death`} onClose={onClose} />
        <div className="space-y-4">
          {/* Death Type Dropdown */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-white">
              How did they die?
            </label>
            <select
              value={deathType || ''}
              onChange={(e) =>
                onDeathTypeChange(
                  e.target.value as 'execution' | 'demon_kill'
                )
              }
              onKeyDown={handleKeyDown}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select...</option>
              <option value="execution">Execution</option>
              <option value="demon_kill">Demon Kill</option>
            </select>
          </div>

          {/* Day/Night Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-white">
              {dayNightLabel} Number:
            </label>
            <input
              type="number"
              min="1"
              max={maxDayNight}
              value={dayNight ?? ''}
              onChange={(e) => {
                const val = e.target.value ? parseInt(e.target.value, 10) : null;
                if (val !== null && !Number.isNaN(val)) {
                  onDayNightChange(val);
                }
              }}
              onKeyDown={handleKeyDown}
              placeholder={`Enter ${dayNightLabel.toLowerCase()} number`}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!deathType}
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="mt-6 flex gap-3 justify-center">
          <button
            type="button"
            onClick={onClear}
            disabled={deathType === null && dayNight === null}
            className={`px-4 py-2 rounded-md transition ${
              deathType !== null || dayNight !== null
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            Clear
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!isValid}
            className={`px-4 py-2 rounded-md transition ${
              isValid
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
