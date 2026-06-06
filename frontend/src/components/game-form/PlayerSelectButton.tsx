import { Field } from './fields';

interface PlayerSelectButtonProps {
  label: string;
  value: number | null;
  playerNames?: string[];
  onClick: () => void;
  error?: string;
  disabled?: boolean;
}

export function PlayerSelectButton({
  label,
  value,
  playerNames,
  onClick,
  error,
  disabled = false,
}: PlayerSelectButtonProps): JSX.Element {

  const playerLabel =
    value !== null
      ? playerNames?.[value] ?? `Player ${value + 1}`
      : 'Select player...';

  return (
    <Field label={label} error={error}>
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className={`w-full min-h-[42px] p-2 rounded-md transition text-left font-medium ${
          disabled
            ? 'opacity-50 cursor-not-allowed bg-gray-600 text-gray-400'
            : 'bg-indigo-600 hover:bg-indigo-700 text-white'
        }`}
      >
        {playerLabel}
      </button>
    </Field>
  );
}
