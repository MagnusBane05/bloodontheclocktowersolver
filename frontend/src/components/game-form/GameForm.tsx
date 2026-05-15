import React, { useEffect, useState } from 'react';
import { DeathInfo, Info, MetadataResponse, SolveRequest } from '../../types';
import { SelectField } from './fields';
import { InfoFields } from './info-sections';
import {
  computeEmpathNeighbours,
  defaultInfoKinds,
  getBodyFromPreviousNight,
  parseDeathList,
  parseSlayerShot,
  validateInfo,
} from './utils';
import { SelectOption, InfoFormEntry, InfoErrors } from './types';

export function GameForm({ onSubmit, loading }: { onSubmit: (request: SolveRequest) => void; loading: boolean }): JSX.Element {
  const [players, setPlayers] = useState<number>(5);
  const [nights, setNights] = useState<string>('');
  const [executed, setExecuted] = useState<string>('');
  const [demonKills, setDemonKills] = useState<string>('');
  const [slayerShot, setSlayerShot] = useState<string>('');
  const [infos, setInfos] = useState<InfoFormEntry[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [infoKinds, setInfoKinds] = useState<string[]>([]);
  const [minionRoles, setMinionRoles] = useState<string[]>([]);
  const [townsfolkRoles, setTownsfolkRoles] = useState<string[]>([]);
  const [infoErrors, setInfoErrors] = useState<InfoErrors>({});

  useEffect(() => {
    fetch('/api/metadata')
      .then((response) => response.json())
      .then((data: MetadataResponse) => {
        setRoles(data.roles);
        setInfoKinds(data.infoKinds);
        setMinionRoles(data.minionRoles);
        setTownsfolkRoles(data.townsfolkRoles);
      })
      .catch((fetchError) => console.error('Failed to fetch metadata:', fetchError));
  }, []);

  const playerOptions: SelectOption[] = Array.from({ length: players }, (_, i) => ({ value: i, label: `${i}` }));
  const roleOptions = roles.map((role) => ({ value: role, label: role }));
  const minionOptions = minionRoles.map((role) => ({ value: role, label: role }));
  const townsfolkOptions = townsfolkRoles.map((role) => ({ value: role, label: role }));
  const allInfoKinds = infoKinds.length > 0 ? infoKinds : defaultInfoKinds;

  const computeEmpathNeighboursLocal = (empath: number | null, night: number | null) =>
    computeEmpathNeighbours(empath, night, players, executed, demonKills, slayerShot);

  const getBodyFromPreviousNightLocal = (night: number | null) => getBodyFromPreviousNight(executed, night);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const nextErrors: InfoErrors = {};

    infos.forEach((info, index) => {
      const errors = validateInfo(info, computeEmpathNeighboursLocal, getBodyFromPreviousNightLocal);
      if (Object.keys(errors).length > 0) {
        nextErrors[index] = errors;
      }
    });

    if (Object.keys(nextErrors).length > 0) {
      setInfoErrors(nextErrors);
      return;
    }

    setInfoErrors({});

    const deathInfo: DeathInfo = {
      executed: parseDeathList(executed),
      killed_by_demon: parseDeathList(demonKills),
      slayer_shot: parseSlayerShot(slayerShot),
    };

    const requestInfos: Info[] = infos.flatMap((info) => {
      if (info.kind === 'fortune teller') {
        const fortuneAny = info as any;
        return (fortuneAny.pings ?? []).map((ping: [[number, number], number, boolean]) => ({
          kind: 'fortune teller' as const,
          fortune_teller: fortuneAny.fortune_teller,
          night: ping[1],
          pings: [ping[0], ping[2]] as [[number, number], boolean],
        }));
      }

      if (info.kind === 'empath') {
        const empathAny = info as any;
        return (empathAny.empathRows ?? []).map((row: [number, number]) => {
          const [night, numberValue] = row;
          const neighbours = computeEmpathNeighboursLocal(empathAny.empath ?? null, night ?? null);
          return {
            kind: 'empath' as const,
            empath: empathAny.empath,
            number: numberValue,
            night,
            left_neighbour: neighbours.left,
            right_neighbour: neighbours.right,
          };
        });
      }

      if (info.kind === 'undertaker') {
        const undertakerAny = info as any;
        return (undertakerAny.undertakerRows ?? []).map((row: [number, string]) => {
          const [night, token] = row;
          return {
            kind: 'undertaker' as const,
            undertaker: undertakerAny.undertaker,
            body: getBodyFromPreviousNightLocal(night ?? null) as number,
            token,
            night,
          };
        });
      }

      return [info as Info];
    });

    const request: SolveRequest = {
      players,
      deathInfo,
      infos: requestInfos,
      ...(nights && { nights: parseInt(nights, 10) }),
    };

    onSubmit(request);
  };

  const addInfo = () => {
    setInfos([...infos, { kind: '' }] as InfoFormEntry[]);
  };

  const updateInfo = (index: number, field: string, value: any) => {
    setInfos((currentInfos) => {
      const nextInfos = [...currentInfos];
      if (field === 'kind') {
        const nextKind = value as Info['kind'] | '';
        nextInfos[index] = {
          ...nextInfos[index],
          kind: nextKind,
          ...(nextKind === 'fortune teller' ? { pings: [[[null, null], null, false]] } : {}),
          ...(nextKind === 'empath' ? { empathRows: [[null, null]] } : {}),
          ...(nextKind === 'undertaker' ? { undertakerRows: [[null, null]] } : {}),
        } as InfoFormEntry;
      } else {
        nextInfos[index] = { ...nextInfos[index], [field]: value };
      }

      return nextInfos;
    });

    setInfoErrors((currentErrors) => {
      const nextErrors = { ...currentErrors };
      if (nextErrors[index]?.[field]) {
        const fieldErrors = { ...nextErrors[index] };
        delete fieldErrors[field];

        if (Object.keys(fieldErrors).length > 0) {
          nextErrors[index] = fieldErrors;
        } else {
          delete nextErrors[index];
        }
      }
      return nextErrors;
    });
  };

  const removeInfo = (index: number) => {
    setInfos((currentInfos) => currentInfos.filter((_, i) => i !== index));
    setInfoErrors((currentErrors) => {
      const nextErrors = { ...currentErrors };
      delete nextErrors[index];
      return nextErrors;
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <label htmlFor="playerCount" className="block text-sm font-medium">
          Number of Players:
        </label>
        <select
          id="playerCount"
          value={players}
          onChange={(e) => setPlayers(parseInt(e.target.value, 10))}
          required
          className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white"
        >
          <option value="">Select...</option>
          <option value="5">5 Players</option>
          <option value="6">6 Players</option>
          <option value="13">13 Players</option>
        </select>
      </div>

      <div className="space-y-2">
        <label htmlFor="nights" className="block text-sm font-medium">
          Number of Nights (optional):
        </label>
        <input
          type="number"
          id="nights"
          value={nights}
          onChange={(e) => setNights(e.target.value)}
          min="1"
          placeholder="Auto-detect if empty"
          className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white"
        />
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Death Information</h3>
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium">Executed Players (player,night):</label>
            <textarea
              value={executed}
              onChange={(e) => setExecuted(e.target.value)}
              placeholder="Example: 0,1 or 3,2"
              rows={3}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">Demon Kills (player,night):</label>
            <textarea
              value={demonKills}
              onChange={(e) => setDemonKills(e.target.value)}
              placeholder="Example: 1,1 or 4,2"
              rows={3}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">Slayer Shot (player,night) - optional:</label>
            <input
              type="text"
              value={slayerShot}
              onChange={(e) => setSlayerShot(e.target.value)}
              placeholder="Example: 2,1"
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white"
            />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Info List</h3>
        <div className="space-y-4">
          {infos.map((info, index) => (
            <div key={index} className="flex items-start space-x-4 p-4 bg-gray-700 rounded-md">
              <div className="flex-1 space-y-4">
                <SelectField
                  id={`info-${index}-kind`}
                  label="Info Type:"
                  value={info.kind || null}
                  options={allInfoKinds.map((kind) => ({ value: kind, label: kind }))}
                  placeholder="Select..."
                  onChange={(value) => updateInfo(index, 'kind', value)}
                  error={infoErrors[index]?.kind}
                />
                <InfoFields
                  info={info}
                  index={index}
                  fieldErrors={infoErrors[index] || {}}
                  playerOptions={playerOptions}
                  roleOptions={roleOptions}
                  minionOptions={minionOptions}
                  townsfolkOptions={townsfolkOptions}
                  updateInfo={updateInfo}
                  computeEmpathNeighbours={computeEmpathNeighboursLocal}
                  getBodyFromPreviousNight={getBodyFromPreviousNightLocal}
                />
              </div>
              <button
                type="button"
                className="mt-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md"
                onClick={() => removeInfo(index)}
              >
                Remove
              </button>
            </div>
          ))}
          <button
            type="button"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
            onClick={addInfo}
          >
            Add Info
          </button>
        </div>
      </div>

      <button
        type="submit"
        className="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-md disabled:opacity-50"
        disabled={loading}
      >
        {loading ? 'Solving...' : 'Solve'}
      </button>
    </form>
  );
}
