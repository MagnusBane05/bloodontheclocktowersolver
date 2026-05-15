import { Info } from '../../types';

export type SelectOption = {
  value: string | number;
  label: string;
};

export type EmpathRow = [number | null, number | null];
export type UndertakerRow = [number | null, string | null];

export type InfoFormEntry = Omit<Info, 'kind'> & {
  kind: Info['kind'] | '';
  pings?: Array<[[number | null, number | null], number | null, boolean]>;
  empathRows?: EmpathRow[];
  undertakerRows?: UndertakerRow[];
};

export type InfoErrors = Record<number, Record<string, string>>;
