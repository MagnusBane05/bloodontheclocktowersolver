import { Field } from './fields';

interface PlayerSelectButtonProps {
  label: string;
  value: number | null;
  onClick: () => void;
  error?: string;
  disabled?: boolean;
}

export function PlayerSelectButton({
  label,
  value,
  onClick,
  error,
  disabled = false,
}: PlayerSelectButtonProps): JSX.Element {
  return (
    <Field label={label} error={error}>
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className={`w-full p-2 rounded-md transition text-left font-medium ${
          disabled
            ? 'opacity-50 cursor-not-allowed bg-gray-600 text-gray-400'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
      >
        {value !== null ? `Player ${value}` : 'Select player...'}
      </button>
    </Field>
  );
}
