import { SelectField, NumberField, CheckboxField } from './fields';
import { PingRow, EmpathRow, UndertakerRow } from './info-rows';
import { SelectOption, EmpathRow as EmpathRowType, UndertakerRow as UndertakerRowType, InfoFormEntry } from './types';

interface InfoFieldsProps {
  info: InfoFormEntry;
  index: number;
  fieldErrors: Record<string, string>;
  playerOptions: SelectOption[];
  roleOptions: SelectOption[];
  minionOptions: SelectOption[];
  townsfolkOptions: SelectOption[];
  updateInfo: (index: number, field: string, value: any) => void;
  computeEmpathNeighbours: (empath: number | null, night: number | null) => { left: number | null; right: number | null };
  getBodyFromPreviousNight: (night: number | null) => number | null;
}

export function InfoFields({
  info,
  index,
  fieldErrors,
  playerOptions,
  roleOptions,
  minionOptions,
  townsfolkOptions,
  updateInfo,
  computeEmpathNeighbours,
  getBodyFromPreviousNight,
}: InfoFieldsProps): JSX.Element | null {
  const infoAny = info as any;

  if (!info.kind) {
    return null;
  }

  switch (info.kind) {
    case 'claim':
      return (
        <div className="space-y-2">
          <SelectField
            id={`info-${index}-claim-player`}
            label="Player:"
            value={infoAny.player ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'player', value)}
            error={fieldErrors.player}
          />
          <SelectField
            id={`info-${index}-claim-character`}
            label="Character:"
            value={infoAny.character ?? null}
            options={roleOptions}
            placeholder="Select character..."
            onChange={(value) => updateInfo(index, 'character', value)}
            error={fieldErrors.character}
            disabled={roleOptions.length === 0}
          />
        </div>
      );
    case 'investigator':
      return (
        <div className="space-y-2">
          <SelectField
            id={`info-${index}-investigator-player`}
            label="Investigator Player:"
            value={infoAny.investigator ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'investigator', value)}
            error={fieldErrors.investigator}
          />
          <SelectField
            id={`info-${index}-first-player`}
            label="First Player:"
            value={infoAny.first_player ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'first_player', value)}
            error={fieldErrors.first_player}
          />
          <SelectField
            id={`info-${index}-second-player`}
            label="Second Player:"
            value={infoAny.second_player ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'second_player', value)}
            error={fieldErrors.second_player}
          />
          <SelectField
            id={`info-${index}-minion-character`}
            label="Minion Character:"
            value={infoAny.minion ?? null}
            options={minionOptions}
            placeholder="Select minion..."
            onChange={(value) => updateInfo(index, 'minion', value)}
            error={fieldErrors.minion}
          />
        </div>
      );
    case 'washerwoman':
      return (
        <div className="space-y-2">
          <SelectField
            id={`info-${index}-washerwoman-player`}
            label="Washerwoman Player:"
            value={infoAny.washerwoman ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'washerwoman', value)}
            error={fieldErrors.washerwoman}
          />
          <SelectField
            id={`info-${index}-washerwoman-first-player`}
            label="First Player:"
            value={infoAny.first_player ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'first_player', value)}
            error={fieldErrors.first_player}
          />
          <SelectField
            id={`info-${index}-washerwoman-second-player`}
            label="Second Player:"
            value={infoAny.second_player ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'second_player', value)}
            error={fieldErrors.second_player}
          />
          <SelectField
            id={`info-${index}-townsfolk-character`}
            label="Townsfolk Character:"
            value={infoAny.townsfolk ?? null}
            options={townsfolkOptions}
            placeholder="Select townsfolk..."
            onChange={(value) => updateInfo(index, 'townsfolk', value)}
            error={fieldErrors.townsfolk}
          />
        </div>
      );
    case 'librarian':
      return (
        <div className="space-y-2">
          <SelectField
            id={`info-${index}-librarian-player`}
            label="Librarian Player:"
            value={infoAny.librarian ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'librarian', value)}
            error={fieldErrors.librarian}
          />
          <SelectField
            id={`info-${index}-librarian-first-player`}
            label="First Player (optional):"
            value={infoAny.first_player ?? null}
            options={[{ value: '', label: 'None' }, ...playerOptions]}
            placeholder="None"
            onChange={(value) => updateInfo(index, 'first_player', value)}
            error={fieldErrors.first_player}
          />
          <SelectField
            id={`info-${index}-librarian-second-player`}
            label="Second Player (optional):"
            value={infoAny.second_player ?? null}
            options={[{ value: '', label: 'None' }, ...playerOptions]}
            placeholder="None"
            onChange={(value) => updateInfo(index, 'second_player', value)}
            error={fieldErrors.second_player}
          />
          <SelectField
            id={`info-${index}-librarian-token`}
            label="Token (optional):"
            value={infoAny.token ?? null}
            options={[{ value: '', label: 'None' }, ...roleOptions]}
            placeholder="None"
            onChange={(value) => updateInfo(index, 'token', value)}
            error={fieldErrors.token}
            disabled={roleOptions.length === 0}
          />
        </div>
      );
    case 'chef':
      return (
        <div className="space-y-2">
          <SelectField
            id={`info-${index}-chef-player`}
            label="Chef Player:"
            value={infoAny.chef ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'chef', value)}
            error={fieldErrors.chef}
          />
          <NumberField
            id={`info-${index}-chef-number`}
            label="Number:"
            value={infoAny.number ?? null}
            min={0}
            onChange={(value) => updateInfo(index, 'number', value)}
            error={fieldErrors.number}
          />
        </div>
      );
    case 'fortune teller':
      return (
        <div className="space-y-2">
          <SelectField
            id={`info-${index}-fortune-teller`}
            label="Fortune Teller Player:"
            value={infoAny.fortune_teller ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'fortune_teller', value)}
            error={fieldErrors.fortune_teller}
          />
          <div className="space-y-3 rounded-md border border-gray-600 bg-gray-800 p-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-white">Pings</h4>
              <button
                type="button"
                className="rounded-md bg-blue-600 px-3 py-2 text-white hover:bg-blue-700"
                onClick={() =>
                  updateInfo(index, 'pings', [
                    ...(infoAny.pings ?? []),
                    [[null, null], null, false],
                  ] as any)
                }
              >
                Add Ping
              </button>
            </div>
            {(infoAny.pings ?? []).map(
              (ping: [[number | null, number | null], number | null, boolean], pingIndex: number) => (
                <PingRow
                  key={pingIndex}
                  index={pingIndex}
                  value={ping}
                  playerOptions={playerOptions}
                  onPlayer1Change={(value) =>
                    updateInfo(
                      index,
                      'pings',
                      (infoAny.pings ?? []).map(
                        (row: [[number | null, number | null], number | null, boolean], rowIndex: number) =>
                          rowIndex === pingIndex ? [[value, row[0][1]], row[1], row[2]] : row,
                      ),
                    )
                  }
                  onPlayer2Change={(value) =>
                    updateInfo(
                      index,
                      'pings',
                      (infoAny.pings ?? []).map(
                        (row: [[number | null, number | null], number | null, boolean], rowIndex: number) =>
                          rowIndex === pingIndex ? [[row[0][0], value], row[1], row[2]] : row,
                      ),
                    )
                  }
                  onNightChange={(value) =>
                    updateInfo(
                      index,
                      'pings',
                      (infoAny.pings ?? []).map(
                        (row: [[number | null, number | null], number | null, boolean], rowIndex: number) =>
                          rowIndex === pingIndex ? [row[0], value, row[2]] : row,
                      ),
                    )
                  }
                  onPingChange={(value) =>
                    updateInfo(
                      index,
                      'pings',
                      (infoAny.pings ?? []).map(
                        (row: [[number | null, number | null], number | null, boolean], rowIndex: number) =>
                          rowIndex === pingIndex ? [row[0], row[1], value] : row,
                      ),
                    )
                  }
                  onRemove={() =>
                    updateInfo(
                      index,
                      'pings',
                      (infoAny.pings ?? []).filter((_: any, rowIndex: number) => rowIndex !== pingIndex),
                    )
                  }
                  error={{
                    player1: fieldErrors[`pings-${pingIndex}-player1`],
                    player2: fieldErrors[`pings-${pingIndex}-player2`],
                    night: fieldErrors[`pings-${pingIndex}-night`],
                    hot: fieldErrors[`pings-${pingIndex}-hot`],
                  }}
                />
              ),
            )}
            {fieldErrors.pings && <p className="text-sm text-red-300">{fieldErrors.pings}</p>}
          </div>
        </div>
      );
    case 'empath': {
      const empathRows: EmpathRowType[] = infoAny.empathRows ?? [[null, null]];
      return (
        <div className="space-y-3 rounded-md border border-gray-600 bg-gray-800 p-4">
          <div className="space-y-2">
            <SelectField
              id={`info-${index}-empath`}
              label="Empath Player:"
              value={infoAny.empath ?? null}
              options={playerOptions}
              placeholder="Select player..."
              onChange={(value) => updateInfo(index, 'empath', value)}
              error={fieldErrors.empath}
            />
          </div>
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-white">Empath Nights</h4>
            <button
              type="button"
              className="rounded-md bg-blue-600 px-3 py-2 text-white hover:bg-blue-700"
              onClick={() =>
                updateInfo(index, 'empathRows', [
                  ...(infoAny.empathRows ?? []),
                  [null, null],
                ] as EmpathRowType[])
              }
            >
              Add Night
            </button>
          </div>
          <div className="space-y-3">
            {empathRows.map((row, rowIndex) => {
              const neighbours = computeEmpathNeighbours(infoAny.empath ?? null, row[0] ?? null);
              return (
                <EmpathRow
                  key={rowIndex}
                  index={rowIndex}
                  value={row}
                  neighbours={neighbours}
                  onNightChange={(value) =>
                    updateInfo(
                      index,
                      'empathRows',
                      (infoAny.empathRows ?? []).map((currentRow: EmpathRowType, currentIndex: number) =>
                        currentIndex === rowIndex ? [value, currentRow[1]] : currentRow,
                      ),
                    )
                  }
                  onNumberChange={(value) =>
                    updateInfo(
                      index,
                      'empathRows',
                      (infoAny.empathRows ?? []).map((currentRow: EmpathRowType, currentIndex: number) =>
                        currentIndex === rowIndex ? [currentRow[0], value] : currentRow,
                      ),
                    )
                  }
                  onRemove={() =>
                    updateInfo(
                      index,
                      'empathRows',
                      (infoAny.empathRows ?? []).filter((_: any, currentIndex: number) => currentIndex !== rowIndex),
                    )
                  }
                  error={{
                    night: fieldErrors[`empathRows-${rowIndex}-night`],
                    number: fieldErrors[`empathRows-${rowIndex}-number`],
                    neighbours: fieldErrors[`empathRows-${rowIndex}-neighbours`],
                  }}
                />
              );
            })}
            {fieldErrors.empathRows && <p className="text-sm text-red-300">{fieldErrors.empathRows}</p>}
          </div>
        </div>
      );
    }
    case 'undertaker': {
      const undertakerRows: UndertakerRowType[] = infoAny.undertakerRows ?? [[null, null]];
      return (
        <div className="space-y-3 rounded-md border border-gray-600 bg-gray-800 p-4">
          <div className="space-y-2">
            <SelectField
              id={`info-${index}-undertaker`}
              label="Undertaker Player:"
              value={infoAny.undertaker ?? null}
              options={playerOptions}
              placeholder="Select player..."
              onChange={(value) => updateInfo(index, 'undertaker', value)}
              error={fieldErrors.undertaker}
            />
          </div>
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-white">Undertaker Nights</h4>
            <button
              type="button"
              className="rounded-md bg-blue-600 px-3 py-2 text-white hover:bg-blue-700"
              onClick={() =>
                updateInfo(index, 'undertakerRows', [
                  ...(infoAny.undertakerRows ?? []),
                  [null, null],
                ] as UndertakerRowType[])
              }
            >
              Add Night
            </button>
          </div>
          <div className="space-y-3">
            {undertakerRows.map((row, rowIndex) => (
              <UndertakerRow
                key={rowIndex}
                index={rowIndex}
                value={row}
                tokenOptions={roleOptions}
                body={getBodyFromPreviousNight(row[0] ?? null)}
                onNightChange={(value) =>
                  updateInfo(
                    index,
                    'undertakerRows',
                    (infoAny.undertakerRows ?? []).map((currentRow: UndertakerRowType, currentIndex: number) =>
                      currentIndex === rowIndex ? [value, currentRow[1]] : currentRow,
                    ),
                  )
                }
                onTokenChange={(value) =>
                  updateInfo(
                    index,
                    'undertakerRows',
                    (infoAny.undertakerRows ?? []).map((currentRow: UndertakerRowType, currentIndex: number) =>
                      currentIndex === rowIndex ? [currentRow[0], value as string | null] : currentRow,
                    ),
                  )
                }
                onRemove={() =>
                  updateInfo(
                    index,
                    'undertakerRows',
                    (infoAny.undertakerRows ?? []).filter((_: any, currentIndex: number) => currentIndex !== rowIndex),
                  )
                }
                error={{
                  night: fieldErrors[`undertakerRows-${rowIndex}-night`],
                  token: fieldErrors[`undertakerRows-${rowIndex}-token`],
                  body: fieldErrors[`undertakerRows-${rowIndex}-body`],
                }}
              />
            ))}
            {fieldErrors.undertakerRows && <p className="text-sm text-red-300">{fieldErrors.undertakerRows}</p>}
          </div>
        </div>
      );
    }
    case 'ravenkeeper':
      return (
        <div className="space-y-2">
          <SelectField
            id={`info-${index}-ravenkeeper`}
            label="Ravenkeeper Player:"
            value={infoAny.ravenkeeper ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'ravenkeeper', value)}
            error={fieldErrors.ravenkeeper}
          />
          <SelectField
            id={`info-${index}-chosen`}
            label="Chosen Player:"
            value={infoAny.chosen ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'chosen', value)}
            error={fieldErrors.chosen}
          />
          <SelectField
            id={`info-${index}-raven-token`}
            label="Token:"
            value={infoAny.token ?? null}
            options={roleOptions}
            placeholder="Select token..."
            onChange={(value) => updateInfo(index, 'token', value)}
            error={fieldErrors.token}
            disabled={roleOptions.length === 0}
          />
          <NumberField
            id={`info-${index}-raven-night`}
            label="Night:"
            value={infoAny.night ?? null}
            min={1}
            onChange={(value) => updateInfo(index, 'night', value)}
            error={fieldErrors.night}
          />
        </div>
      );
    case 'virgin':
      return (
        <div className="space-y-2">
          <SelectField
            id={`info-${index}-virgin`}
            label="Virgin Player:"
            value={infoAny.virgin ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'virgin', value)}
            error={fieldErrors.virgin}
          />
          <SelectField
            id={`info-${index}-nominator`}
            label="Nominator:"
            value={infoAny.nominator ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'nominator', value)}
            error={fieldErrors.nominator}
          />
          <CheckboxField
            id={`info-${index}-virgin-executed`}
            label="Executed"
            checked={infoAny.executed ?? false}
            onChange={(value) => updateInfo(index, 'executed', value)}
            error={fieldErrors.executed}
          />
          <NumberField
            id={`info-${index}-virgin-night`}
            label="Night:"
            value={infoAny.night ?? null}
            min={1}
            onChange={(value) => updateInfo(index, 'night', value)}
            error={fieldErrors.night}
          />
        </div>
      );
    case 'slayer':
      return (
        <div className="space-y-2">
          <SelectField
            id={`info-${index}-slayer`}
            label="Slayer Player:"
            value={infoAny.slayer ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'slayer', value)}
            error={fieldErrors.slayer}
          />
          <SelectField
            id={`info-${index}-target`}
            label="Target Player:"
            value={infoAny.target ?? null}
            options={playerOptions}
            placeholder="Select player..."
            onChange={(value) => updateInfo(index, 'target', value)}
            error={fieldErrors.target}
          />
          <CheckboxField
            id={`info-${index}-slayer-successful`}
            label="Successful"
            checked={infoAny.successful ?? false}
            onChange={(value) => updateInfo(index, 'successful', value)}
            error={fieldErrors.successful}
          />
          <NumberField
            id={`info-${index}-slayer-night`}
            label="Night:"
            value={infoAny.night ?? null}
            min={1}
            onChange={(value) => updateInfo(index, 'night', value)}
            error={fieldErrors.night}
          />
        </div>
      );
    default:
      return null;
  }
}
