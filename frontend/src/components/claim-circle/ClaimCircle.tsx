import { useState } from "react";
import { PlayerCircleRing } from "../PlayerCircleRing";
import { ClaimModal } from "./ClaimModal";
import { InfoFormEntry, SelectOption } from "../game-form/types";

interface ClaimCircleProps {
  onPlayerNameChange: (index: number, value: string) => void;
  infos: InfoFormEntry[];
  addInfo: (info: InfoFormEntry | null) => void;
  updateInfo: (index: number, field: string, value: any) => void;
  removeInfo: (index: number) => void;
  claimRoleOptions: SelectOption[];
  characterTypeOptions: SelectOption[];
  playerNames: string[];
  players: number;
  playerClaims: Record<number, string[]>;
  deadFlags: boolean[];
  handlePlayerContextMenu: (player: number, e: React.MouseEvent<Element, MouseEvent>) => void;
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
}

export function ClaimCircle({
  onPlayerNameChange,
  infos,
  addInfo,
  updateInfo,
  removeInfo,
  claimRoleOptions,
  characterTypeOptions,
  players,
  playerNames,
  playerClaims,
  deadFlags,
  handlePlayerContextMenu,
  evilRoleNames,
  goodRoleNames,
} : ClaimCircleProps
) {
  const [selectedPlayer, setSelectedPlayer] = useState<number | null>(null);

  return (
    <>
      <PlayerCircleRing
        count={players}
        playerNames={playerNames}
        playerClaims={playerClaims}
        deadFlags={deadFlags}
        selectedPlayer={selectedPlayer}
        onPlayerSelect={setSelectedPlayer}
        onPlayerNameChange={onPlayerNameChange}
        editablePlayerNames
        onPlayerContextMenu={handlePlayerContextMenu}
        evilRoleNames={evilRoleNames}
        goodRoleNames={goodRoleNames}
        size="100%"
        className="h-full w-full"
        innerRingClassName="absolute inset-0 rounded-full border border-yellow-800/30"
        playerSize={74}
      />
      {selectedPlayer !== null && (
        <ClaimModal
          player={selectedPlayer}
          characterOptions={claimRoleOptions}
          characterTypeOptions={characterTypeOptions}
          playerNames={playerNames} 
          onSelectedPlayerChange={setSelectedPlayer}
          infos={infos}
          addInfo={addInfo}
          updateInfo={updateInfo}
          removeInfo={removeInfo}
        />
      )}
    </>
  );
}