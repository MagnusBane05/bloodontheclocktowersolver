import { useEffect } from 'react';
import { PlayerCircleRing } from '../PlayerCircleRing';
import { ModalHeader } from './ModalHeader';

interface PlayerSelectModalProps {
  playerCount: number;
  selectionLabel: string;
  onSelect: (player: number) => void;
  onCancel: () => void;
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
  playerNames?: string[];
}

export function PlayerSelectModal({
  playerCount,
  selectionLabel,
  onSelect,
  onCancel,
  evilRoleNames,
  goodRoleNames,
  playerNames,
}: PlayerSelectModalProps): JSX.Element {
  // Handle Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onCancel]);

  return (
    <div
      className="fixed inset-0 z-30 flex items-center justify-center bg-black/50"
      onClick={onCancel}
    >
      <div
        className="bg-gray-800 border border-gray-600 rounded-lg p-6 max-w-2xl w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <ModalHeader content={selectionLabel} onClose={onCancel} />

        <div className="relative w-full max-w-md mx-auto aspect-square rounded-full border border-gray-600 bg-gray-900/80">
          <PlayerCircleRing
            count={playerCount}
            playerNames={playerNames}
            onPlayerSelect={onSelect}
            evilRoleNames={evilRoleNames}
            goodRoleNames={goodRoleNames}
            size="100%"
            className="h-full w-full"
            innerRingClassName="absolute inset-0 rounded-full border border-white/30"
            playerSize={60}
            centerContent={
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="text-center">
                  <p className="text-sm text-white/70">{selectionLabel}</p>
                </div>
              </div>
            }
          />
        </div>
      </div>
    </div>
  );
}
