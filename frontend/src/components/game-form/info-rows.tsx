import { CloseButton } from '../CloseButton';
import { SelectField, NumberField, ToggleField, ButtonField, ReadOnlyField } from './fields';
import type { SelectOption, EmpathRow, UndertakerRow } from './types';

export interface PingRowProps {
  index: number;
  infosIndex: number;
  value: [[number | null, number | null], number | null, boolean];
  playerNames?: string[];
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
  playerNames,
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
    <div className="grid gap-3 md:grid-cols-[1fr_auto] border-b border-gray-600 pb-2 items-center relative">
      <div className="grid gap-3 md:grid-cols-3">
        <ButtonField
          label="Player 1"
          value={value[0][0] ?? null}
          playerNames={playerNames}
          onClick={() => onPlayerSelectClick(`ping-${infosIndex}-${index}-player1`, 'Select Player 1')}
          error={error?.player1}
        />
        <ButtonField
          label="Player 2"
          value={value[0][1] ?? null}
          playerNames={playerNames}
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
      <div className="md:mt-8">
        <ToggleField
          id={`ping-${index}-hot`}
          label="Demon?"
          checked={value[2] ?? false}
          onChange={onPingChange}
          error={error?.hot}
        />
      </div>
      <div className='absolute right-0 -top-1'>
        <CloseButton onClose={onRemove} />
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
  neighbours: { left: string | null; right: string | null };
  error?: Record<string, string>;
}

export function EmpathRow({ index, value, onNightChange, onNumberChange, onRemove, neighbours, error }: EmpathRowProps): JSX.Element {
  return (
    <div className="grid grid-cols-3 gap-3 border-b border-gray-600 pb-2">
      <div className='flex gap-3'>
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
      </div>
      <div className="flex-2 space-y-2 col-span-2">
        <div className="flex justify-between items-start gap-4">
          <ReadOnlyField
            label="Left Neighbour"
            error={error?.neighbours}
            value={neighbours.left !== null ? neighbours.left : 'N/A'}
          />
          <ReadOnlyField
            label="Right Neighbour"
            error={error?.neighbours}
            value={neighbours.right !== null ? neighbours.right : 'N/A'}
          />
          <div className='-my-1'>
            <CloseButton onClose={onRemove} />
          </div>
        </div>
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
  playerNames?: string[];
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
  playerNames,
}: UndertakerRowProps): JSX.Element {
  return (
    <div className="grid grid-cols-5 gap-3 border-b border-gray-600 pb-2">
      <div className='flex-none'>
        <NumberField
          id={`undertaker-${index}-night`}
          label="Night"
          value={value[0] ?? null}
          min={1}
          onChange={onNightChange}
          error={error?.night}
        />
      </div>
      <div className='flex-1 col-span-2'>
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
      </div>
      <div className="space-y-2 flex-1 col-span-2">
        <div className="flex justify-between items-start">
          <ReadOnlyField 
            label="Body"
            error={error?.body}
            value={body !== null ? (playerNames ? playerNames[body] : `Player ${body + 1}`) : 'N/A'}
          />
          <div className='-my-1'>
            <CloseButton onClose={onRemove} />
          </div>
        </div>
      </div>
    </div>
  );
}
