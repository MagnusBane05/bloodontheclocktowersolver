import { SelectField, NumberField, CheckboxField } from './fields';
import { PlayerSelectButton } from './PlayerSelectButton';
import type { SelectOption, EmpathRow, UndertakerRow } from './types';

export interface PingRowProps {
  index: number;
  infosIndex: number;
  value: [[number | null, number | null], number | null, boolean];
  activePlayerSelectModal: string | null;
  onPlayerSelectClick: (modalId: string, label: string) => void;
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
  onPlayer1Change: (value: number | null) => void;
  onPlayer2Change: (value: number | null) => void;
  onNightChange: (value: number | null) => void;
  onPingChange: (value: boolean) => void;
  onRemove: () => void;
  error?: Record<string, string>;
}

export function PingRow({
  index,
  infosIndex,
  value,
  activePlayerSelectModal: _activePlayerSelectModal,
  onPlayerSelectClick,
  evilRoleNames: _evilRoleNames,
  goodRoleNames: _goodRoleNames,
  onPlayer1Change: _onPlayer1Change,
  onPlayer2Change: _onPlayer2Change,
  onNightChange,
  onPingChange,
  onRemove,
  error,
}: PingRowProps): JSX.Element {
  return (
    <div className="grid gap-3 md:grid-cols-[1fr_auto]">
      <div className="grid gap-3 md:grid-cols-3">
        <PlayerSelectButton
          label="Player 1"
          value={value[0][0] ?? null}
          onClick={() => onPlayerSelectClick(`ping-${infosIndex}-${index}-player1`, 'Select Player 1')}
          error={error?.player1}
        />
        <PlayerSelectButton
          label="Player 2"
          value={value[0][1] ?? null}
          onClick={() => onPlayerSelectClick(`ping-${infosIndex}-${index}-player2`, 'Select Player 2')}
          error={error?.player2}
        />
        <NumberField
          id={`ping-${index}-night`}
          label="Night"
          value={value[1] ?? null}
          min={1}
          onChange={onNightChange}
          error={error?.night}
        />
      </div>
      <div className="flex flex-col items-start gap-3 md:items-start">
        <CheckboxField
          id={`ping-${index}-hot`}
          label="Pinged?"
          checked={value[2] ?? false}
          onChange={onPingChange}
          error={error?.hot}
        />
        <button
          type="button"
          className="rounded-md bg-red-600 px-3 py-2 text-white hover:bg-red-700"
          onClick={onRemove}
        >
          Remove
        </button>
      </div>
    </div>
  );
}

export interface EmpathRowProps {
  index: number;
  value: EmpathRow;
  onNightChange: (value: number | null) => void;
  onNumberChange: (value: number | null) => void;
  onRemove: () => void;
  neighbours: { left: number | null; right: number | null };
  error?: Record<string, string>;
}

export function EmpathRow({ index, value, onNightChange, onNumberChange, onRemove, neighbours, error }: EmpathRowProps): JSX.Element {
  return (
    <div className="grid gap-3 md:grid-cols-[1fr_auto]">
      <div className="grid gap-3 md:grid-cols-3">
        <NumberField
          id={`empath-${index}-night`}
          label="Night"
          value={value[0] ?? null}
          min={1}
          onChange={onNightChange}
          error={error?.night}
        />
        <NumberField
          id={`empath-${index}-number`}
          label="Number"
          value={value[1] ?? null}
          min={0}
          onChange={onNumberChange}
          error={error?.number}
        />
        <div className="space-y-2">
          <label className="block text-sm font-medium">Neighbours</label>
          <div className="grid gap-2 md:grid-cols-2">
            <div className="p-2 bg-gray-700 border border-gray-500 rounded-md text-white">L: {neighbours.left !== null ? neighbours.left : 'N/A'}</div>
            <div className="p-2 bg-gray-700 border border-gray-500 rounded-md text-white">R: {neighbours.right !== null ? neighbours.right : 'N/A'}</div>
          </div>
          {error?.neighbours && <p className="text-sm text-red-300">{error.neighbours}</p>}
        </div>
      </div>
      <div className="flex flex-col items-start gap-3 md:items-start">
        <button
          type="button"
          className="rounded-md bg-red-600 px-3 py-2 text-white hover:bg-red-700"
          onClick={onRemove}
        >
          Remove
        </button>
      </div>
    </div>
  );
}

export interface UndertakerRowProps {
  index: number;
  value: UndertakerRow;
  tokenOptions: SelectOption[];
  body: number | null;
  onNightChange: (value: number | null) => void;
  onTokenChange: (value: string | null) => void;
  onRemove: () => void;
  error?: Record<string, string>;
}

export function UndertakerRow({
  index,
  value,
  tokenOptions,
  body,
  onNightChange,
  onTokenChange,
  onRemove,
  error,
}: UndertakerRowProps): JSX.Element {
  return (
    <div className="grid gap-3 md:grid-cols-[1fr_auto]">
      <div className="grid gap-3 md:grid-cols-3">
        <NumberField
          id={`undertaker-${index}-night`}
          label="Night"
          value={value[0] ?? null}
          min={1}
          onChange={onNightChange}
          error={error?.night}
        />
        <SelectField
          id={`undertaker-${index}-token`}
          label="Token"
          value={value[1] ?? null}
          options={tokenOptions}
          placeholder="Select token..."
          onChange={(value) => onTokenChange(value as string | null)}
          error={error?.token}
          disabled={tokenOptions.length === 0}
        />
        <div className="space-y-2">
          <label className="block text-sm font-medium">Body</label>
          <div className="p-2 bg-gray-700 border border-gray-500 rounded-md text-white">{body !== null ? body : 'N/A'}</div>
          {error?.body && <p className="text-sm text-red-300">{error.body}</p>}
        </div>
      </div>
      <div className="flex flex-col items-start gap-3 md:items-start">
        <button
          type="button"
          className="rounded-md bg-red-600 px-3 py-2 text-white hover:bg-red-700"
          onClick={onRemove}
        >
          Remove
        </button>
      </div>
    </div>
  );
}
