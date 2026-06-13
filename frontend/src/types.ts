// TypeScript types for the frontend
// export interface DeathInfo {
//   executed: Array<[number, number]>;
//   killed_by_demon: Array<[number, number]>;
//   slayer_shot: [number, number] | null;
// }

export type DeathInfo = 
  | ExecutionInfo
  | DemonKillInfo
  | SlayerKillInfo;

export interface ExecutionInfo {
  kind: 'execution';
  player: number;
  night: number;
}

export interface DemonKillInfo {
  kind: 'demon';
  player: number;
  night: number;
}

export interface SlayerKillInfo {
  kind: 'slayer';
  player: number;
  night: number;
}

export interface DemonKillInfo {
  kind: 'demon';
  player: number;
  night: number;
}

export type Info =
  | Claim
  | InvestigatorInfo
  | WasherwomanInfo
  | LibrarianInfo
  | ChefInfo
  | FortuneTellerInfo
  | EmpathInfo
  | UndertakerInfo
  | RavenkeeperInfo
  | VirginInfo
  | SlayerInfo;

export interface Claim {
  kind: 'claim';
  player: number;
  character: string;
}

export interface InvestigatorInfo {
  kind: 'investigator';
  investigator: number;
  first_player: number;
  second_player: number;
  minion: string;
}

export interface WasherwomanInfo {
  kind: 'washerwoman';
  washerwoman: number;
  first_player: number;
  second_player: number;
  townsfolk: string;
}

export interface LibrarianInfo {
  kind: 'librarian';
  librarian: number;
  first_player: number | null;
  second_player: number | null;
  token: string | null;
}

export interface ChefInfo {
  kind: 'chef';
  chef: number;
  number: number;
}

export interface FortuneTellerInfo {
  kind: 'fortune teller';
  fortune_teller: number;
  night: number;
  pings: [[number, number], boolean];
}

export interface EmpathInfo {
  kind: 'empath';
  empath: number;
  number: number;
  night: number;
  left_neighbour: number;
  right_neighbour: number;
}

export interface UndertakerInfo {
  kind: 'undertaker';
  undertaker: number;
  body: number;
  token: string;
  night: number;
}

export interface RavenkeeperInfo {
  kind: 'ravenkeeper';
  ravenkeeper: number;
  chosen: number;
  token: string;
  night: number;
}

export interface VirginInfo {
  kind: 'virgin';
  virgin: number;
  nominator: number;
  executed: boolean;
  night: number;
}

export interface SlayerInfo {
  kind: 'slayer';
  slayer: number;
  target: number;
  successful: boolean;
  night: number;
}

export interface SolveRequest {
  players: number;
  nights?: number;
  deathInfo: DeathInfo[];
  infos: Info[];
}

export interface GrimoirePage {
  night: number;
  characters: string[];
  dead: boolean[];
  redHerring: boolean[];
  chefNumber: number | null;
  drunkToken: string | null;
  minionTypes: string[];
  noOutsiders: boolean;
  poisoned: boolean[];
}

export interface GrimoireSolution {
  pages: GrimoirePage[];
}

export interface SolveResponse {
  solutionCount: number;
  solutions: GrimoireSolution[];
}

export interface MetadataResponse {
  roles: string[];
  infoKinds: string[];
  minionRoles: string[];
  townsfolkRoles: string[];
  characterTypes: string[];
}

export interface CharacterTypesResponse {
  characterTypes: string[];
}