import React from 'react';
import { ModalHeader } from '../game-form/ModalHeader';
import { Button } from '../Button';
import { DemonKillInfo, ExecutionInfo } from '../../types';

interface DeathModalProps {
  player: number;
  deathType: 'execution' | 'demon' | null;
  dayNight: number | null;
  maxDayNight: number;
  playerNames: string[];
  executions: ExecutionInfo[];
  demonKills: DemonKillInfo[];
  onSelectedPlayerChange: (value: number | null) => void;
  onDeathTypeChange: (type: 'execution' | 'demon' | null) => void;
  onDayNightChange: (dayNight: number | null) => void;
  setExecutions: (executions: ExecutionInfo[]) => void;
  setDemonKills: (demonKills: DemonKillInfo[]) => void;
  removeExecution: (player: number, night: number) => void;
}

export function DeathModal({
  player,
  deathType,
  dayNight,
  maxDayNight,
  playerNames,
  executions,
  demonKills,
  onDeathTypeChange,
  onDayNightChange,
  onSelectedPlayerChange,
  setExecutions,
  setDemonKills,
  removeExecution,
}: DeathModalProps): JSX.Element {


  const isValid = deathType !== null && dayNight !== null && dayNight > 0;
  const isExecution = deathType === 'execution';
  const dayNightLabel = isExecution ? 'Day' : 'Night';

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && isValid) {
      handleDeathConfirm();
    } else if (e.key === 'Escape') {
      handleCloseDeathModal();
    }
  };

  const playerName = playerNames[player] ?? `Player ${player + 1}`;

  const isExistingExecution = () => -1 !== executions.findIndex((e) => 
    e.player === player
  );

  const handleDeathConfirm = () => {
    if (!isValid || player === null || deathType === null || dayNight === null) {
      return;
    }

    if (deathType === 'execution') {
      const newExecutions = [
        ...executions.filter((e) => e.player !== player),
        {player: player, night: dayNight, kind: "execution"} as ExecutionInfo
      ]
      setExecutions(newExecutions);
    } else {
      const newDemonKills = [
        ...demonKills.filter((d) => d.player !== player),
        {player: player, night: dayNight, kind: "demon"} as DemonKillInfo
      ]
      setDemonKills(newDemonKills);
    }

    onSelectedPlayerChange(null);
    onDeathTypeChange(null);
    onDayNightChange(null);
  };

  const handleClearDeath = () => {
    if (player === null) {
      return;
    }

    setDemonKills(demonKills.filter((d) => d.player !== player));
    if (isExistingExecution() && dayNight !== null) {
      removeExecution(player, dayNight);
    }

    onDeathTypeChange(null);
    onDayNightChange(null);
  };

  const handleCloseDeathModal = () => {
    onSelectedPlayerChange(null);
    onDeathTypeChange(null);
    onDayNightChange(null);
  };

  return (
    <div
      className="fixed inset-0 z-30 flex items-center justify-center bg-black/50"
      onClick={handleCloseDeathModal}
    >
      <div
        className="bg-gray-800 border border-gray-600 rounded-lg p-6 max-w-sm w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <ModalHeader content={`${playerName} death`} onClose={handleCloseDeathModal} />
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
                  e.target.value as 'execution' | 'demon'
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
          <Button
            type="button"
            onClick={handleClearDeath}
            disabled={deathType === null && dayNight === null}
            style="remove"
          >
            Clear
          </Button>
          <Button
            type="button"
            onClick={handleDeathConfirm}
            disabled={!isValid}
            style="primary"
          >
            Confirm
          </Button>
        </div>
      </div>
    </div>
  );
}
