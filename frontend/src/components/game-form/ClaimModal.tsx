import { SelectField } from './fields';
import { ModalHeader } from './ModalHeader';
import { SelectOption } from './types';

interface ClaimModalProps {
  player: number;
  value: string | null;
  options: SelectOption[];
  onChange: (value: string | null) => void;
  onAddClaim: () => void;
  onAddClaimAndInfo: () => void;
  onClear: () => void;
  onClose: () => void;
  infoKindExists: boolean;
  playerNames: string[];
}

export function ClaimModal({
  player,
  value,
  options,
  onChange,
  onAddClaim,
  onAddClaimAndInfo,
  onClear,
  onClose,
  infoKindExists,
  playerNames,
}: ClaimModalProps): JSX.Element {
  const canAddClaim = value !== null;
  const canAddClaimAndInfo = canAddClaim && infoKindExists;

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
        <ModalHeader content={`${playerName} claim`} onClose={onClose} />

        <div className="space-y-4">
          <SelectField
            id="claim-modal-character"
            label="Character"
            value={value}
            options={options}
            placeholder="Select role..."
            onChange={(val) => onChange(val as string | null)}
            disabled={options.length === 0}
          />
          {value && !infoKindExists && (
            <p className="text-sm text-yellow-300">
              There is no matching info type for this claim.
            </p>
          )}
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onClear}
            disabled={!value}
            className={`px-4 py-2 rounded-md transition ${
              value
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            Clear
          </button>
          <button
            type="button"
            onClick={onAddClaim}
            disabled={!canAddClaim}
            className={`px-4 py-2 rounded-md transition ${
              canAddClaim
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            Add Claim
          </button>
          <button
            type="button"
            onClick={onAddClaimAndInfo}
            disabled={!canAddClaimAndInfo}
            className={`px-4 py-2 rounded-md transition ${
              canAddClaimAndInfo
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            Add Claim and Info
          </button>
        </div>
      </div>
    </div>
  );
}
