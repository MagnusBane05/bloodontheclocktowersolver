import { useState } from 'react';
import { SelectField } from './fields';
import { InfoFields } from './info-sections';
import { InfoErrors, InfoFormEntry, SelectOption } from './types';
import { CloseButton } from './CloseButton';

interface InfoEntryProps {
  info: InfoFormEntry;
  index: number;
  allInfoKinds: string[];
  infoErrors: InfoErrors;
  claimRoleOptions: SelectOption[];
  minionOptions: SelectOption[];
  townsfolkOptions: SelectOption[];
  updateInfo: (index: number, field: string, value: any) => void;
  removeInfo: (index: number) => void;
  computeEmpathNeighbours: (empath: number | null, night: number | null) => {
    left: number | null;
    right: number | null;
  };
  getBodyFromPreviousNight: (night: number | null) => number | null;
  activePlayerSelectModal: string | null;
  onPlayerSelectClick: (modalId: string, label: string) => void;
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
  playerNames?: string[];
}

export function InfoEntry({
  info,
  index,
  allInfoKinds,
  infoErrors,
  claimRoleOptions,
  minionOptions,
  townsfolkOptions,
  updateInfo,
  removeInfo,
  computeEmpathNeighbours,
  getBodyFromPreviousNight,
  activePlayerSelectModal,
  onPlayerSelectClick,
  evilRoleNames,
  goodRoleNames,
  playerNames,
}: InfoEntryProps): JSX.Element | null {
  const [collapsed, setCollapsed] = useState<boolean>(false);

  const kindLabel = info.kind ? info.kind : 'New info';
  const entryErrors = infoErrors[index] || {};
  const errorKeys = Object.keys(entryErrors);
  const hasErrors = errorKeys.length > 0;
  const firstError = hasErrors ? entryErrors[errorKeys[0]] : '';
  const summaryText = hasErrors
    ? firstError
    : info.kind
    ? 'Tap the chevron to collapse or expand details'
    : 'Select an info type to configure';

  return info.kind === 'claim' ? null : (
    <div
      className={`overflow-hidden rounded-xl border bg-gray-800 shadow-sm transition-shadow duration-200 hover:shadow-md ${
        hasErrors ? 'border-red-500' : 'border-gray-600'
      }`}
    >
      <div className="flex items-center justify-between gap-4 px-4 py-3">
        <button
          type="button"
          className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-gray-600 bg-gray-700 text-gray-200 transition-colors duration-200 hover:border-gray-500 hover:bg-gray-600"
          aria-expanded={!collapsed}
          aria-label={collapsed ? `Expand ${kindLabel}` : `Collapse ${kindLabel}`}
          onClick={() => setCollapsed((prev) => !prev)}
        >
          <span className={`inline-block text-base transition-transform duration-200 pi ${collapsed ? 'pi-angle-right' : 'pi-angle-down'}`}></span>
        </button>

        <div className="min-w-0 flex-1 overflow-hidden">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-semibold text-white capitalize">{kindLabel}</p>
          </div>
          <p className={`truncate text-xs ${hasErrors ? 'text-red-300' : 'text-gray-400'}`}>{summaryText}</p>
        </div>
        <CloseButton onClose={() => removeInfo(index)} />
      </div>

      <div className={`overflow-hidden transition-all duration-300 ease-in-out ${collapsed ? 'max-h-0 opacity-0' : 'max-h-[1200px] opacity-100'}`}>
        <div className="space-y-4 border-t border-gray-700 px-4 py-4">
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
            roleOptions={claimRoleOptions}
            minionOptions={minionOptions}
            townsfolkOptions={townsfolkOptions}
            updateInfo={updateInfo}
            computeEmpathNeighbours={computeEmpathNeighbours}
            getBodyFromPreviousNight={getBodyFromPreviousNight}
            activePlayerSelectModal={activePlayerSelectModal}
            onPlayerSelectClick={onPlayerSelectClick}
            evilRoleNames={evilRoleNames}
            goodRoleNames={goodRoleNames}
            playerNames={playerNames}
          />
        </div>
      </div>
    </div>
  );
}