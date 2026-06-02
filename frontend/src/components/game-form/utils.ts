import { Info, SlayerInfo, VirginInfo } from '../../types';
import { InfoFormEntry } from './types';

export const defaultInfoKinds = [
  'claim',
  'investigator',
  'washerwoman',
  'librarian',
  'chef',
  'fortune teller',
  'empath',
  'undertaker',
  'ravenkeeper',
  'virgin',
  'slayer',
] as const;

export const parseDeathList = (input: string): Array<[number, number]> =>
  input
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line)
    .map((line) => {
      const [player, night] = line.split(',').map(Number);
      return [player, night] as [number, number];
    });

export const getAlivePlayersAtNight = (
  players: number,
  night: number | null,
  executed: string,
  demonKills: string,
  slayerShot: [number, number] | null,
): number[] => {
  if (night === undefined || night === null || Number.isNaN(night)) {
    return Array.from({ length: players }, (_, i) => i);
  }

  const deadPlayers = new Set<number>();
  parseDeathList(executed).forEach(([player, deathNight]) => {
    if (deathNight < night) deadPlayers.add(player);
  });
  parseDeathList(demonKills).forEach(([player, deathNight]) => {
    if (deathNight <= night) deadPlayers.add(player);
  });
  if (slayerShot && !Number.isNaN(slayerShot[0]) && slayerShot[1] < night) {
    deadPlayers.add(slayerShot[0]);
  }

  return Array.from({ length: players }, (_, i) => i).filter((player) => !deadPlayers.has(player));
};

export const getBodyFromPreviousNight = (executed: string, night: number | null): number | null => {
  if (night === undefined || night === null || Number.isNaN(night) || night <= 1) {
    return null;
  }

  const previousNight = night - 1;
  const executedRows = parseDeathList(executed).filter(([, deathNight]) => deathNight === previousNight);
  return executedRows.length > 0 ? executedRows[0][0] : null;
};

export const computeEmpathNeighbours = (
  empath: number | null,
  night: number | null,
  players: number,
  executed: string,
  demonKills: string,
  slayerShot: [number, number] | null,
): { left: number | null; right: number | null } => {
  if (
    empath === undefined ||
    empath === null ||
    Number.isNaN(empath) ||
    night === undefined ||
    night === null ||
    Number.isNaN(night)
  ) {
    return { left: null, right: null };
  }

  const alivePlayers = getAlivePlayersAtNight(players, night, executed, demonKills, slayerShot);
  if (alivePlayers.length < 2 || !alivePlayers.includes(empath)) {
    return { left: null, right: null };
  }

  const sortedPlayers = [...alivePlayers].sort((a, b) => a - b);
  const empathIndex = sortedPlayers.indexOf(empath);
  if (empathIndex === -1) {
    return { left: null, right: null };
  }

  const left = sortedPlayers[(empathIndex - 1 + sortedPlayers.length) % sortedPlayers.length];
  const right = sortedPlayers[(empathIndex + 1) % sortedPlayers.length];
  return { left, right };
};

export const validateInfo = (
  info: InfoFormEntry,
  computeEmpathNeighboursFn: (
    empath: number | null,
    night: number | null,
  ) => { left: number | null; right: number | null },
  getBodyFromPreviousNightFn: (night: number | null) => number | null,
): Record<string, string> => {
  const errors: Record<string, string> = {};
  const infoAny = info as any;

  if (!info.kind) {
    errors.kind = 'Select an info type.';
    return errors;
  }

  switch (info.kind) {
    case 'claim': {
      if (infoAny.player === undefined || infoAny.player === null || Number.isNaN(infoAny.player)) {
        errors.player = 'Please select a player.';
      }
      if (!infoAny.character || (typeof infoAny.character === 'string' && !infoAny.character.trim())) {
        errors.character = 'Please select a character.';
      }
      break;
    }
    case 'investigator': {
      if (infoAny.investigator === undefined || infoAny.investigator === null || Number.isNaN(infoAny.investigator)) {
        errors.investigator = 'Please select the investigator player.';
      }
      if (infoAny.first_player === undefined || infoAny.first_player === null || Number.isNaN(infoAny.first_player)) {
        errors.first_player = 'Please select the first player.';
      }
      if (infoAny.second_player === undefined || infoAny.second_player === null || Number.isNaN(infoAny.second_player)) {
        errors.second_player = 'Please select the second player.';
      }
      if (!infoAny.minion || (typeof infoAny.minion === 'string' && !infoAny.minion.trim())) {
        errors.minion = 'Please select a minion character.';
      }
      break;
    }
    case 'washerwoman': {
      if (infoAny.washerwoman === undefined || infoAny.washerwoman === null || Number.isNaN(infoAny.washerwoman)) {
        errors.washerwoman = 'Please select the washerwoman player.';
      }
      if (infoAny.first_player === undefined || infoAny.first_player === null || Number.isNaN(infoAny.first_player)) {
        errors.first_player = 'Please select the first player.';
      }
      if (infoAny.second_player === undefined || infoAny.second_player === null || Number.isNaN(infoAny.second_player)) {
        errors.second_player = 'Please select the second player.';
      }
      if (!infoAny.townsfolk || (typeof infoAny.townsfolk === 'string' && !infoAny.townsfolk.trim())) {
        errors.townsfolk = 'Please select a townsfolk character.';
      }
      break;
    }
    case 'librarian': {
      if (infoAny.librarian === undefined || infoAny.librarian === null || Number.isNaN(infoAny.librarian)) {
        errors.librarian = 'Please select the librarian player.';
      }
      break;
    }
    case 'chef': {
      if (infoAny.chef === undefined || infoAny.chef === null || Number.isNaN(infoAny.chef)) {
        errors.chef = 'Please select the chef player.';
      }
      if (infoAny.number === undefined || infoAny.number === null || Number.isNaN(infoAny.number)) {
        errors.number = 'Please enter a number.';
      }
      break;
    }
    case 'fortune teller': {
      if (infoAny.fortune_teller === undefined || infoAny.fortune_teller === null || Number.isNaN(infoAny.fortune_teller)) {
        errors.fortune_teller = 'Please select the fortune teller player.';
      }
      if (!Array.isArray(infoAny.pings) || infoAny.pings.length === 0) {
        errors.pings = 'Add at least one ping row.';
      } else {
        infoAny.pings.forEach((ping: any, pingIndex: number) => {
          if (!Array.isArray(ping[0]) || ping[0][0] === undefined || ping[0][0] === null || Number.isNaN(ping[0][0])) {
            errors[`pings-${pingIndex}-player1`] = `Ping ${pingIndex + 1}: select player 1.`;
          }
          if (!Array.isArray(ping[0]) || ping[0][1] === undefined || ping[0][1] === null || Number.isNaN(ping[0][1])) {
            errors[`pings-${pingIndex}-player2`] = `Ping ${pingIndex + 1}: select player 2.`;
          }
          if (ping[1] === undefined || ping[1] === null || Number.isNaN(ping[1])) {
            errors[`pings-${pingIndex}-night`] = `Ping ${pingIndex + 1}: enter a night.`;
          }
          if (typeof ping[2] !== 'boolean') {
            errors[`pings-${pingIndex}-hot`] = `Ping ${pingIndex + 1}: specify whether they were pinged.`;
          }
        });
      }
      break;
    }
    case 'empath': {
      if (infoAny.empath === undefined || infoAny.empath === null || Number.isNaN(infoAny.empath)) {
        errors.empath = 'Please select the empath player.';
      }
      if (!Array.isArray(infoAny.empathRows) || infoAny.empathRows.length === 0) {
        errors.empathRows = 'Add at least one empath night row.';
      } else {
        infoAny.empathRows.forEach((row: any, rowIndex: number) => {
          const night = row[0];
          const numberValue = row[1];
          if (night === undefined || night === null || Number.isNaN(night)) {
            errors[`empathRows-${rowIndex}-night`] = `Row ${rowIndex + 1}: enter a night.`;
          }
          if (numberValue === undefined || numberValue === null || Number.isNaN(numberValue)) {
            errors[`empathRows-${rowIndex}-number`] = `Row ${rowIndex + 1}: enter a number.`;
          }
          const neighbours = computeEmpathNeighboursFn(infoAny.empath ?? null, night ?? null);
          if (
            night !== undefined &&
            night !== null &&
            !Number.isNaN(night) &&
            (neighbours.left === null || neighbours.right === null)
          ) {
            errors[`empathRows-${rowIndex}-neighbours`] = `Row ${rowIndex + 1}: unable to compute neighbours for this night.`;
          }
        });
      }
      break;
    }
    case 'undertaker': {
      if (infoAny.undertaker === undefined || infoAny.undertaker === null || Number.isNaN(infoAny.undertaker)) {
        errors.undertaker = 'Please select the undertaker player.';
      }
      if (!Array.isArray(infoAny.undertakerRows) || infoAny.undertakerRows.length === 0) {
        errors.undertakerRows = 'Add at least one undertaker night row.';
      } else {
        infoAny.undertakerRows.forEach((row: any, rowIndex: number) => {
          const night = row[0];
          const token = row[1];
          if (night === undefined || night === null || Number.isNaN(night)) {
            errors[`undertakerRows-${rowIndex}-night`] = `Row ${rowIndex + 1}: enter a night.`;
          }
          if (!token || (typeof token === 'string' && !token.trim())) {
            errors[`undertakerRows-${rowIndex}-token`] = `Row ${rowIndex + 1}: select a token.`;
          }
          const body = getBodyFromPreviousNightFn(night ?? null);
          if (night !== undefined && night !== null && !Number.isNaN(night) && body === null) {
            errors[`undertakerRows-${rowIndex}-body`] = `Row ${rowIndex + 1}: cannot determine body from previous night's execution.`;
          }
        });
      }
      break;
    }
    case 'ravenkeeper': {
      if (infoAny.ravenkeeper === undefined || infoAny.ravenkeeper === null || Number.isNaN(infoAny.ravenkeeper)) {
        errors.ravenkeeper = 'Please select the ravenkeeper player.';
      }
      if (infoAny.chosen === undefined || infoAny.chosen === null || Number.isNaN(infoAny.chosen)) {
        errors.chosen = 'Please select the chosen player.';
      }
      if (!infoAny.token || (typeof infoAny.token === 'string' && !infoAny.token.trim())) {
        errors.token = 'Please select a token.';
      }
      if (infoAny.night === undefined || infoAny.night === null || Number.isNaN(infoAny.night)) {
        errors.night = 'Please select the night.';
      }
      break;
    }
    case 'virgin': {
      if (infoAny.virgin === undefined || infoAny.virgin === null || Number.isNaN(infoAny.virgin)) {
        errors.virgin = 'Please select the virgin player.';
      }
      if (infoAny.nominator === undefined || infoAny.nominator === null || Number.isNaN(infoAny.nominator)) {
        errors.nominator = 'Please select the nominator.';
      }
      if (infoAny.executed === undefined || typeof infoAny.executed !== 'boolean') {
        errors.executed = 'Please indicate if the virgin was executed.';
      }
      if (infoAny.night === undefined || infoAny.night === null || Number.isNaN(infoAny.night)) {
        errors.night = 'Please select the night.';
      }
      break;
    }
    case 'slayer': {
      if (infoAny.slayer === undefined || infoAny.slayer === null || Number.isNaN(infoAny.slayer)) {
        errors.slayer = 'Please select the slayer player.';
      }
      if (infoAny.target === undefined || infoAny.target === null || Number.isNaN(infoAny.target)) {
        errors.target = 'Please select the target player.';
      }
      if (infoAny.successful === undefined || typeof infoAny.successful !== 'boolean') {
        errors.successful = 'Please indicate whether the shot was successful.';
      }
      if (infoAny.night === undefined || infoAny.night === null || Number.isNaN(infoAny.night)) {
        errors.night = 'Please select the night.';
      }
      break;
    }
    default:
      break;
  }

  return errors;
};

export const serializeDeathList = (entries: Array<[number, number]>): string =>
  entries.map(([player, night]) => `${player},${night}`).join('\n');

export const getInfoKindForClaimRole = (character: string | null): Info['kind'] | null => {
  if (!character) {
    return null;
  }

  switch (character.trim().toLowerCase()) {
    case 'investigator':
      return 'investigator';
    case 'washerwoman':
      return 'washerwoman';
    case 'librarian':
      return 'librarian';
    case 'chef':
      return 'chef';
    case 'fortune teller':
      return 'fortune teller';
    case 'empath':
      return 'empath';
    case 'undertaker':
      return 'undertaker';
    case 'ravenkeeper':
      return 'ravenkeeper';
    case 'virgin':
      return 'virgin';
    case 'slayer':
      return 'slayer';
    default:
      return null;
  }
};

export const createInfoEntryForClaimRole = (kind: Info['kind'], player: number): InfoFormEntry | null => {
  switch (kind) {
    case 'investigator':
      return {
        kind: 'investigator',
        investigator: player,
        first_player: null,
        second_player: null,
        minion: null,
      } as InfoFormEntry;
    case 'washerwoman':
      return {
        kind: 'washerwoman',
        washerwoman: player,
        first_player: null,
        second_player: null,
        townsfolk: null,
      } as InfoFormEntry;
    case 'librarian':
      return {
        kind: 'librarian',
        librarian: player,
        first_player: null,
        second_player: null,
        token: null,
      } as InfoFormEntry;
    case 'chef':
      return {
        kind: 'chef',
        chef: player,
        number: null,
      } as InfoFormEntry;
    case 'fortune teller':
      return {
        kind: 'fortune teller',
        fortune_teller: player,
        pings: [[[null, null], null, false]],
      } as InfoFormEntry;
    case 'empath':
      return {
        kind: 'empath',
        empath: player,
        empathRows: [[null, null]],
      } as InfoFormEntry;
    case 'undertaker':
      return {
        kind: 'undertaker',
        undertaker: player,
        undertakerRows: [[null, null]],
      } as InfoFormEntry;
    case 'ravenkeeper':
      return {
        kind: 'ravenkeeper',
        ravenkeeper: player,
        chosen: null,
        token: null,
        night: null,
      } as InfoFormEntry;
    case 'virgin':
      return {
        kind: 'virgin',
        virgin: player,
        nominator: null,
        executed: false,
        night: null,
      } as InfoFormEntry;
    case 'slayer':
      return {
        kind: 'slayer',
        slayer: player,
        target: null,
        successful: false,
        night: null,
      } as InfoFormEntry;
    default:
      return null;
  }
};

export const deriveSlayerShotFromInfos = (infos: InfoFormEntry[]): [number, number] | null => {
  const successfulSlayerInfo = infos.find((info) => info.kind === 'slayer' && (info as any).successful) as SlayerInfo;

  if (
    !successfulSlayerInfo ||
    successfulSlayerInfo.target === undefined ||
    successfulSlayerInfo.target === null ||
    Number.isNaN(successfulSlayerInfo.target) ||
    successfulSlayerInfo.night === undefined ||
    successfulSlayerInfo.night === null ||
    Number.isNaN(successfulSlayerInfo.night)
  ) {
    return null;
  }

  return [successfulSlayerInfo.target, successfulSlayerInfo.night];
};

export const deriveVirginExecutionFromInfos = (infos: InfoFormEntry[]): [number, number] | null => {
  const successfulVirginNomination = infos.find((info) => info.kind === 'virgin' && (info as any).executed) as VirginInfo;

  if (
    !successfulVirginNomination ||
    successfulVirginNomination.nominator === undefined ||
    successfulVirginNomination.nominator === null ||
    Number.isNaN(successfulVirginNomination.nominator) ||
    successfulVirginNomination.night === undefined ||
    successfulVirginNomination.night === null ||
    Number.isNaN(successfulVirginNomination.night)
  ) {
    return null;
  }

  return [successfulVirginNomination.nominator, successfulVirginNomination.night];
}
