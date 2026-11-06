import React from 'react';
import { ModalHeader } from '../game-form/ModalHeader';
import { Button } from '../Button';
import { DeathInfo, DemonKillInfo, ExecutionInfo } from '../../types';

interface DeathModalProps {
  player: number;
  deathType: 'execution' | 'demon' | null;
  dayNight: number | null;
  maxDayNight: number;
  playerNames: string[];
  infoDeath: DeathInfo | null;
  onSelectedPlayerChange: (value: number | null) => void;
  onDeathTypeChange: (type: 'execution' | 'demon' | null) => void;
  onDayNightChange: (dayNight: number | null) => void;
  setExecutions: (update: (current: ExecutionInfo[]) => ExecutionInfo[]) => void;
  setDemonKills: (update: (current: DemonKillInfo[]) => DemonKillInfo[]) => void;
}

export function DeathModal({
  player,
  deathType,
  dayNight,
  maxDayNight,
  playerNames,
  infoDeath,
  onDeathTypeChange,
  onDayNightChange,
  onSelectedPlayerChange,
  setExecutions,
  setDemonKills,
}: DeathModalProps): JSX.Element {


  const shownType = infoDeath?.kind ?? deathType;
  const shownDayNight = infoDeath?.night ?? dayNight;
  const isValid = !infoDeath && deathType !== null && dayNight !== null && dayNight > 0;
  const dayNightLabel = shownType === 'execution' || shownType === 'slayer' ? 'Day' : 'Night';

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && isValid) {
      handleDeathConfirm();
    } else if (e.key === 'Escape') {
      handleCloseDeathModal();
    }
  };

  const playerName = playerNames[player] ?? `Player ${player + 1}`;

  const handleDeathConfirm = () => {
    if (!isValid || player === null || deathType === null || dayNight === null) {
      return;
    }

    // Each list drops the player first, so changing the death type can't leave them in both.
    const otherPlayers = <T extends { player: number }>(deaths: T[]) => deaths.filter((d) => d.player !== player);

    if (deathType === 'execution') {
      setDemonKills(otherPlayers);
      setExecutions((current) => [
        ...otherPlayers(current),
        {player: player, night: dayNight, kind: "execution"} as ExecutionInfo
      ]);
    } else {
      setExecutions(otherPlayers);
      setDemonKills((current) => [
        ...otherPlayers(current),
        {player: player, night: dayNight, kind: "demon"} as DemonKillInfo
      ]);
    }

    onSelectedPlayerChange(null);
    onDeathTypeChange(null);
    onDayNightChange(null);
  };

  const handleClearDeath = () => {
    if (player === null) {
      return;
    }

    const otherPlayers = <T extends { player: number }>(deaths: T[]) => deaths.filter((d) => d.player !== player);
    setExecutions(otherPlayers);
    setDemonKills(otherPlayers);

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
          {infoDeath && (
            <p className="text-sm text-amber-300">
              This death comes from the {infoDeath.kind === 'slayer' ? 'Slayer' : 'Virgin'} info. Change it in the Info List.
            </p>
          )}
          {/* Death Type Dropdown */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-white">
              How did they die?
            </label>
            <select
              value={shownType || ''}
              disabled={!!infoDeath}
              onChange={(e) =>
                onDeathTypeChange(
                  (e.target.value || null) as 'execution' | 'demon' | null
                )
              }
              onKeyDown={handleKeyDown}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">Select...</option>
              <option value="execution">Execution</option>
              <option value="demon">Demon Kill</option>
              {shownType === 'slayer' && <option value="slayer">Slayer Shot</option>}
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
              value={shownDayNight ?? ''}
              onChange={(e) => {
                const val = e.target.value ? parseInt(e.target.value, 10) : null;
                if (val !== null && !Number.isNaN(val)) {
                  onDayNightChange(val);
                }
              }}
              onKeyDown={handleKeyDown}
              placeholder={`Enter ${dayNightLabel.toLowerCase()} number`}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!!infoDeath || !deathType}
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="mt-6 flex gap-3 justify-center">
          <Button
            type="button"
            onClick={handleClearDeath}
            disabled={!!infoDeath || (deathType === null && dayNight === null)}
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
