import { useEffect, useMemo, useState } from 'react';
import { DeathInfo, DemonKillInfo, ExecutionInfo, Info, MetadataResponse, SolveRequest } from '../../types';
import {
  computeEmpathNeighbours,
  defaultInfoKinds,
  deriveSlayerShotFromInfos,
  deriveVirginExecutionFromInfos,
  getBodyFromPreviousNight,
  validateInfo,
} from './utils';
import { InfoErrors, InfoFormEntry } from './types';

interface UseGameFormResult {
  players: number;
  allExecutions: ExecutionInfo[];
  demonKills: DemonKillInfo[];
  infos: InfoFormEntry[];
  roles: string[];
  infoKinds: string[];
  claimRoleOptions: Array<{ value: string; label: string }>;
  characterTypeOptions: Array<{ value: string; label: string }>;
  minionOptions: Array<{ value: string; label: string }>;
  townsfolkOptions: Array<{ value: string; label: string }>;
  allInfoKinds: string[];
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
  infoErrors: InfoErrors;
  activePlayerSelectModal: string | null;
  playerSelectLabel: string;
  playerClaimMap: Record<number, string[]>;
  deadFlags: boolean[];
  setPlayers: (players: number) => void;
  computeEmpathNeighboursLocal: (empath: number | null, night: number | null) => { left: number | null; right: number | null };
  getBodyFromPreviousNightLocal: (night: number | null) => number | null;
  handlePlayerSelectClick: (modalId: string, label: string) => void;
  handleClosePlayerSelectModal: () => void;
  handlePlayerSelectConfirm: (player: number) => void;
  handleSubmit: (event: React.FormEvent) => void;
  addInfo: (info: InfoFormEntry | null) => void;
  clearInfo: () => void;
  updateInfo: (index: number, field: string, value: any) => void;
  removeInfo: (index: number) => void;
  setExecutions: (executions: ExecutionInfo[]) => void;
  setDemonKills: (demonKills: DemonKillInfo[]) => void;
  removeExecutionInfo: (player: number, night: number) => void;
}

const principalPlayerFields = new Set([
  'investigator',
  'washerwoman',
  'librarian',
  'chef',
  'fortune_teller',
  'empath',
  'undertaker',
  'ravenkeeper',
  'virgin',
  'slayer',
]);

const infoRoleLabels: Record<Info['kind'], string> = {
  claim: 'claim',
  investigator: 'Investigator',
  washerwoman: 'Washerwoman',
  librarian: 'Librarian',
  chef: 'Chef',
  'fortune teller': 'Fortune Teller',
  empath: 'Empath',
  undertaker: 'Undertaker',
  ravenkeeper: 'Ravenkeeper',
  virgin: 'Virgin',
  slayer: 'Slayer',
};

const getInfoRoleLabel = (info: InfoFormEntry): string | undefined => {
  const infoAny = info as any;

  if (info.kind === 'claim' && typeof infoAny.player === 'number' && infoAny.character) {
    return infoAny.character;
  }

  if (info.kind === 'investigator') return infoRoleLabels.investigator;
  if (info.kind === 'washerwoman') return infoRoleLabels.washerwoman;
  if (info.kind === 'librarian') return infoRoleLabels.librarian;
  if (info.kind === 'chef') return infoRoleLabels.chef;
  if (info.kind === 'fortune teller') return infoRoleLabels['fortune teller'];
  if (info.kind === 'empath') return infoRoleLabels.empath;
  if (info.kind === 'undertaker') return infoRoleLabels.undertaker;
  if (info.kind === 'ravenkeeper') return infoRoleLabels.ravenkeeper;
  if (info.kind === 'virgin') return infoRoleLabels.virgin;
  if (info.kind === 'slayer') return infoRoleLabels.slayer;

  return undefined;
};

const getInfoPlayerField = (info: InfoFormEntry): number | null | undefined => {
  const infoAny = info as any;

  switch (info.kind) {
    case 'investigator':
      return infoAny.investigator;
    case 'washerwoman':
      return infoAny.washerwoman;
    case 'librarian':
      return infoAny.librarian;
    case 'chef':
      return infoAny.chef;
    case 'fortune teller':
      return infoAny.fortune_teller;
    case 'empath':
      return infoAny.empath;
    case 'undertaker':
      return infoAny.undertaker;
    case 'ravenkeeper':
      return infoAny.ravenkeeper;
    case 'virgin':
      return infoAny.virgin;
    case 'slayer':
      return infoAny.slayer;
    default:
      return undefined;
  }
};

const buildPlayerClaimMap = (infos: InfoFormEntry[]): Record<number, string[]> =>
  infos.reduce<Record<number, string[]>>((acc, info) => {
    const infoAny = info as any;

    if (info.kind === 'claim' && typeof infoAny.player === 'number' && infoAny.character) {
      acc[infoAny.player] = [infoAny.character];
      return acc;
    }

    const roleLabel = getInfoRoleLabel(info);
    const player = getInfoPlayerField(info);

    if (roleLabel && typeof player === 'number') {
      acc[player] = [roleLabel];
    }

    return acc;
  }, {});

export function useGameForm(onSubmit: (request: SolveRequest) => void): UseGameFormResult {
  const [players, setPlayers] = useState<number>(5);
  const [executions, setExecutions] = useState<ExecutionInfo[]>([]);
  const [demonKills, setDemonKills] = useState<DemonKillInfo[]>([]);
  const [infos, setInfos] = useState<InfoFormEntry[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [characterTypes, setCharacterTypes] = useState<string[]>([]);
  const [infoKinds, setInfoKinds] = useState<string[]>([]);
  const [minionRoles, setMinionRoles] = useState<string[]>([]);
  const [townsfolkRoles, setTownsfolkRoles] = useState<string[]>([]);
  const [evilRoleNames, setEvilRoleNames] = useState<Set<string>>(new Set());
  const [goodRoleNames, setGoodRoleNames] = useState<Set<string>>(new Set());
  const [infoErrors, setInfoErrors] = useState<InfoErrors>({});
  const [activePlayerSelectModal, setActivePlayerSelectModal] = useState<string | null>(null);
  const [playerSelectLabel, setPlayerSelectLabel] = useState<string>('Select player');

  useEffect(() => {
    fetch('/api/metadata')
      .then((response) => response.json())
      .then((data: MetadataResponse & { evilRoles?: string[]; goodRoles?: string[] }) => {
        setRoles(data.roles);
        setInfoKinds(data.infoKinds);
        setMinionRoles(data.minionRoles);
        setTownsfolkRoles(data.townsfolkRoles);
        setCharacterTypes(data.characterTypes);
        setEvilRoleNames(new Set(data.evilRoles ?? []));
        setGoodRoleNames(new Set(data.goodRoles ?? []));
      })
      .catch((fetchError) => console.error('Failed to fetch metadata:', fetchError));
  }, []);

  const claimRoleOptions = useMemo(
    () =>
      roles
        .filter((role) => !/unknown/i.test(role) && !/^non\s*demon$/i.test(role))
        .map((role) => ({ value: role, label: role })),
    [roles],
  );

  const characterTypeOptions = useMemo(
    () =>
      characterTypes.map((characterType) => ({
        value: characterType, 
        label: characterType.replace("Unknown", "").replace("Imp", "Demon").trim()
      })),
    [characterTypes]
  );

  const minionOptions = useMemo(
    () => minionRoles.map((role) => ({ value: role, label: role })),
    [minionRoles],
  );

  const townsfolkOptions = useMemo(
    () => townsfolkRoles.map((role) => ({ value: role, label: role })),
    [townsfolkRoles],
  );

  const allInfoKinds = useMemo(
    () => (infoKinds.length > 0 ? infoKinds : defaultInfoKinds).filter((kind) => kind !== 'claim'),
    [infoKinds],
  );

  const playerClaimMap = useMemo(() => buildPlayerClaimMap(infos), [infos]);

  const slayerShot = useMemo(() => deriveSlayerShotFromInfos(infos), [infos]);
  const virginExecution = useMemo(() => deriveVirginExecutionFromInfos(infos), [infos]);

  const allExecutions: ExecutionInfo[] = useMemo(() => 
    virginExecution ? [...executions, virginExecution] : executions
  , [virginExecution, executions]);

  const allDeaths: DeathInfo[] = useMemo(() => 
    slayerShot ? [...allExecutions, ...demonKills, slayerShot] : 
      [...allExecutions, ...demonKills]
  , [allExecutions, demonKills, slayerShot]);

  const deadFlags = useMemo(() => {
    const deadPlayers = allDeaths
      .filter((d) => typeof d.player === 'number' && !Number.isNaN(d.player))
      .map((d) => d.player);

    return Array.from({ length: players }, (_, i) => deadPlayers.indexOf(i) !== -1);
  }, [allExecutions, demonKills, players, slayerShot]);

  const computeEmpathNeighboursLocal = (empath: number | null, night: number | null) =>
    computeEmpathNeighbours(empath, night, players, allDeaths);

  const getBodyFromPreviousNightLocal = (night: number | null) => getBodyFromPreviousNight(allExecutions, night);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

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

    const deathInfo = allDeaths;

    const requestInfos: Info[] = infos.flatMap((info) => {
      if (info.kind === 'fortune teller') {
        const fortuneAny = info as any;
        return (fortuneAny.pings ?? []).map((ping: [[number | null, number | null], number | null, boolean]) => ({
          kind: 'fortune teller',
          fortune_teller: fortuneAny.fortune_teller,
          night: ping[1] as number,
          pings: [ping[0] as [number, number], ping[2]] as [[number, number], boolean],
        }));
      }

      if (info.kind === 'empath') {
        const empathAny = info as any;
        return (empathAny.empathRows ?? []).map(([night, numberValue]: [number, number]) => {
          const neighbours = computeEmpathNeighboursLocal(empathAny.empath ?? null, night ?? null);
          return {
            kind: 'empath',
            empath: empathAny.empath,
            number: numberValue,
            night: night,
            left_neighbour: neighbours.left as number,
            right_neighbour: neighbours.right as number,
          };
        });
      }

      if (info.kind === 'undertaker') {
        const undertakerAny = info as any;
        return (undertakerAny.undertakerRows ?? []).map(([night, token]: [number, string]) => ({
          kind: 'undertaker',
          undertaker: undertakerAny.undertaker,
          body: getBodyFromPreviousNightLocal(night ?? null) as number,
          token,
          night,
        }));
      }

      return [info as Info];
    });

    const request: SolveRequest = {
      players,
      deathInfo,
      infos: requestInfos,
    };

    onSubmit(request);
  };

  const handlePlayerSelectClick = (modalId: string, label: string) => {
    setActivePlayerSelectModal(modalId);
    setPlayerSelectLabel(label);
  };

  const handleClosePlayerSelectModal = () => {
    setActivePlayerSelectModal(null);
    setPlayerSelectLabel('Select player');
  };

  const handlePlayerSelectConfirm = (player: number) => {
    if (!activePlayerSelectModal) return;

    const parts = activePlayerSelectModal.split('-');

    if (activePlayerSelectModal.startsWith('ping-')) {
      const infosIndex = parseInt(parts[1], 10);
      const pingIndex = parseInt(parts[2], 10);
      const playerNum = parts[3];

      if (infosIndex < 0 || infosIndex >= infos.length) {
        handleClosePlayerSelectModal();
        return;
      }

      if (playerNum === 'player1') {
        updateInfo(
          infosIndex,
          'pings',
          (infos[infosIndex] as any).pings.map((row: any, idx: number) =>
            idx === pingIndex ? [[player, row[0][1]], row[1], row[2]] : row,
          ),
        );
      } else if (playerNum === 'player2') {
        updateInfo(
          infosIndex,
          'pings',
          (infos[infosIndex] as any).pings.map((row: any, idx: number) =>
            idx === pingIndex ? [[row[0][0], player], row[1], row[2]] : row,
          ),
        );
      }
    } else if (activePlayerSelectModal.startsWith('info-')) {
      const infoIndex = parseInt(parts[1], 10);
      const fieldName = parts.slice(2).join('-');
      const actualFieldName =
        fieldName === 'librarian-first_player'
          ? 'first_player'
          : fieldName === 'librarian-second_player'
          ? 'second_player'
          : fieldName;

      updateInfo(infoIndex, actualFieldName, player);
    }

    handleClosePlayerSelectModal();
  };

  const addInfo = (newInfo: InfoFormEntry | null) => {
    if (!newInfo) {
      setInfos((currentInfos) => [...currentInfos, { kind: '' }] as InfoFormEntry[]);
    } else {
      setInfos((currentInfos) => [...currentInfos, newInfo]);
    }
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
          ...(nextKind === 'librarian' ? { first_player: null, second_player: null, token: null } : {}),
        } as InfoFormEntry;
      } else {
        nextInfos[index] = { ...nextInfos[index], [field]: value };
      }

      if (typeof value === 'number' && principalPlayerFields.has(field) && nextInfos[index]?.kind !== 'claim') {
        return nextInfos.filter((info) => {
          const infoAny = info as any;
          return !(infoAny.kind === 'claim' && infoAny.player === value);
        });
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

  const clearInfo = () => {
    setInfos([]);
    setInfoErrors({});
    setExecutions([]);
    setDemonKills([]);
  };

  const removeExecutionInfo = (player: number, night: number) => {
    setExecutions((currentExecution) => currentExecution.filter((e) => 
      e.player !== player && e.night !== night
    ));

    if (virginExecution && 
        virginExecution.player === player && 
        virginExecution.night === night) {
        const virginInfoIndex = infos.findIndex((info) => info.kind === 'virgin'
          && (info as any).nominator === virginExecution.player
          && (info as any).night === virginExecution.night
        );
        if (virginInfoIndex) {
          updateInfo(virginInfoIndex, 'executed', false);
        }
    }
  }

  return {
    players,
    allExecutions,
    demonKills,
    infos,
    roles,
    infoKinds,
    claimRoleOptions,
    characterTypeOptions,
    minionOptions,
    townsfolkOptions,
    allInfoKinds,
    evilRoleNames,
    goodRoleNames,
    infoErrors,
    activePlayerSelectModal,
    playerSelectLabel,
    playerClaimMap,
    deadFlags,
    setPlayers,
    computeEmpathNeighboursLocal,
    getBodyFromPreviousNightLocal,
    handlePlayerSelectClick,
    handleClosePlayerSelectModal,
    handlePlayerSelectConfirm,
    handleSubmit,
    addInfo,
    clearInfo,
    updateInfo,
    removeInfo,
    setExecutions,
    setDemonKills,
    removeExecutionInfo,
  };
}
