import { useEffect, useMemo, useState } from 'react';
import { Button } from '../Button';
import { SelectField } from '../game-form/fields';
import { ModalHeader } from '../game-form/ModalHeader';
import { InfoFormEntry, SelectOption } from '../game-form/types';
import { createInfoEntryForClaimRole } from '../game-form/utils';

const getInfoKindForClaimRole = (character: string | null) => {
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

const alignmentTypeOptions = [{value: 'Unknown Good', label: 'good'}, {value: 'Unknown Evil', label: 'evil'}];

interface ClaimModalProps {
  player: number;
  characterOptions: SelectOption[];
  characterTypeOptions: SelectOption[];
  onSelectedPlayerChange: (value: number | null) => void;
  playerNames: string[];
  infos: InfoFormEntry[];
  addInfo: (info: InfoFormEntry | null) => void;
  updateInfo: (index: number, field: string, value: any) => void;
  removeInfo: (index: number) => void;
}

export function ClaimModal({
  player,
  onSelectedPlayerChange,
  characterOptions,
  characterTypeOptions,
  playerNames,
  infos,
  addInfo,
  updateInfo,
  removeInfo,
}: ClaimModalProps): JSX.Element {
  const [state, setState] = useState<'character' | 'alignment' | 'character type'>('character');
  const [claim, setClaim] = useState<string | null>(null);

  useEffect(() => {
    if (player === null) {
      setClaim(null);
      return;
    }

    const existingClaim = infos.find((info) => {
      const infoAny = info as any;
      return infoAny.kind === 'claim' && infoAny.player === player;
    }) as any;

    setClaim(existingClaim?.character ?? null);
  }, [player, infos]);

  useEffect(() => {
    if (claim == null || characterOptions.map((option) => option.value).includes(claim)) {
      setState('character');
    }
    else if (characterTypeOptions.map((option) => option.value).includes(claim)) {
      setState('character type');
    }
    else if (alignmentTypeOptions.map((option) => option.value).includes(claim)) {
      setState('alignment');
    }
  }, [claim]);

  const options = useMemo(() => {
    switch (state) {
      case 'character':
        return characterOptions;
      case 'alignment':
        return alignmentTypeOptions;
      case 'character type':
        return characterTypeOptions;
    }
  }, [state, characterOptions, characterTypeOptions]);

  const placeholder = useMemo(() => {
    switch (state) {
      case 'character':
        return 'Select character...';
      case 'alignment':
        return 'Select alignment...';
      case 'character type':
        return 'Select character type...';
    }
  }, [state]);

  const canAddClaim = claim !== null;
  const infoKindExists = !!getInfoKindForClaimRole(claim);
  const canAddClaimAndInfo = canAddClaim && infoKindExists;

  const playerName = playerNames[player] ?? `Player ${player + 1}`;

  const findClaimInfoIndex = () => 
    infos.findIndex((info) => {
      const infoAny = info as any;
      return (infoAny.kind === 'claim' && infoAny.player === player);
  }); 

  const handleAddClaim = () => {
    if (player === null || !claim) {
      return;
    }

    const currentInfoIndex = findClaimInfoIndex();

    if (currentInfoIndex === -1) {
      addInfo({
        kind: 'claim',
        player: player,
        character: claim,
      } as InfoFormEntry);
    } else {
      updateInfo(currentInfoIndex, 'kind', 'claim');
      updateInfo(currentInfoIndex, 'player', player);
      updateInfo(currentInfoIndex, 'character', claim);
    }

    onSelectedPlayerChange(null);
    setClaim(null);
  };
  
  const handleAddClaimAndInfo = () => {
    if (player === null || !claim) {
      return;
    }

    const infoKind = getInfoKindForClaimRole(claim);
    const infoEntry = infoKind ? createInfoEntryForClaimRole(infoKind, player) : null;

    if (!infoEntry) {
      return;
    }

    const currentInfoIndex = findClaimInfoIndex();    
    if (currentInfoIndex === -1) {
      addInfo({
        kind: 'claim',
        player: player,
        character: claim,
      } as InfoFormEntry);
    } else {
      updateInfo(currentInfoIndex, 'kind', 'claim');
      updateInfo(currentInfoIndex, 'player', player);
      updateInfo(currentInfoIndex, 'character', claim);
      // Object.keys(infoEntry).forEach((key) => 
      //   updateInfo(currentInfoIndex, key, infoEntry[key as keyof InfoFormEntry])
      // );
    }
    addInfo(infoEntry);

    onSelectedPlayerChange(null);
    setClaim(null);
  };
  
  const handleClearClaim = () => {
    if (player === null) {
      return;
    };

    const currentInfoIndex = findClaimInfoIndex();

    if (currentInfoIndex !== -1) {
      removeInfo(currentInfoIndex);
    };
  };

  const handleCloseClaimModal = () => {
    onSelectedPlayerChange(null);
    setClaim(null);
  };

  return (
    <div
      className="fixed inset-0 z-30 flex items-center justify-center bg-black/50"
      onClick={handleCloseClaimModal}
    >
      <div
        className="bg-gray-800 border border-gray-600 rounded-lg p-6 max-w-sm w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <ModalHeader content={`${playerName} claim`} onClose={handleCloseClaimModal} />

        <div className="space-y-4">
          <div className='space-y-1'>
            <select 
              className='bg-gray-800 focus:outline-none'
              style={{width: `${8*state.length + 20}px`}}
              value={state}
              onChange={(e) => setState(e.target.value as 'character' | 'alignment' | 'character type')}
            >
              <option value='character'>Character</option>
              <option value='alignment'>Alignment</option>
              <option value='character type'>Character Type</option>
            </select>
            <SelectField
              id="claim-modal-character"
              // label="Character"
              value={claim}
              options={options}
              placeholder={placeholder}
              onChange={(val) => setClaim(val as string | null)}
              disabled={options.length === 0}
            />
          </div>
          {state === 'character' && claim && !infoKindExists && (
            <p className="text-sm text-yellow-300">
              There is no matching info type for this claim.
            </p>
          )}
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <Button
            type="button"
            style='remove'
            onClick={handleClearClaim}
            disabled={!claim}
          >
            Clear
          </Button>
          <Button
            type="button"
            onClick={handleAddClaim}
            disabled={!canAddClaim}
            style='secondary'
          >
            Add Claim
          </Button>
          {state === 'character' &&
            <Button
              type="button"
              onClick={handleAddClaimAndInfo}
              disabled={!canAddClaimAndInfo}
              style='primary'
            >
              Add Claim and Info
            </Button>
          }
        </div>
      </div>
    </div>
  );
}
