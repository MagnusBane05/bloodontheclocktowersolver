import { useState } from "react";
import { PlayerCircleRing } from "../PlayerCircleRing";
import { ClaimModal } from "./ClaimModal";
import { InfoFormEntry, SelectOption } from "../game-form/types";
import { DeathModal } from "./DeathModal";
import { DemonKillInfo, ExecutionInfo } from "../../types";

interface ClaimCircleProps {
  players: number;
  playerNames: string[];
  playerClaims: Record<number, string[]>;
  claimRoleOptions: SelectOption[];
  characterTypeOptions: SelectOption[];
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
  deadFlags: boolean[];
  infos: InfoFormEntry[];
  executions: ExecutionInfo[];
  demonKills: DemonKillInfo[];
  onPlayerNameChange: (index: number, value: string) => void;
  addInfo: (info: InfoFormEntry | null) => void;
  updateInfo: (index: number, field: string, value: any) => void;
  removeInfo: (index: number) => void;
  setExecutions: (executions: ExecutionInfo[]) => void;
  setDemonKills: (demonKills: DemonKillInfo[]) => void;
  removeExecution: (player: number, night: number) => void;
}

export function ClaimCircle({
  players,
  playerNames,
  playerClaims,
  claimRoleOptions,
  characterTypeOptions,
  evilRoleNames,
  goodRoleNames,
  deadFlags,
  infos,
  executions,
  demonKills,
  onPlayerNameChange,
  addInfo,
  updateInfo,
  removeInfo,
  setExecutions,
  setDemonKills,
  removeExecution,
} : ClaimCircleProps
) {
  const [selectedPlayer, setSelectedPlayer] = useState<number | null>(null);
  const [displayClaimModal, setDisplayClaimModal] = useState<boolean>(false);
  const [displayDeathModal, setDisplayDeathModal] = useState<boolean>(false);
  const [deathModalType, setDeathModalType] = useState<'execution' | 'demon' | null>(null);
  const [deathModalDayNight, setDeathModalDayNight] = useState<number | null>(null);

  const handleSelectClaimPlayer = (player: number | null) => {
    setSelectedPlayer(player);
    if (player != null) {
      setDisplayClaimModal(true);
    } else {
      setDisplayClaimModal(false);
    }
  };

  const handleSelectDeathPlayer = (player: number | null) => {
    setSelectedPlayer(player);
    if (player != null) {
      setDisplayDeathModal(true);
    } else {
      setDisplayDeathModal(false);
    }
  }

  const getExistingDeath = (player: number) => {
    const death = [...executions, ...demonKills].filter((d) => d.player === player);
    if (death && death.length > 0) {
      return death[0];
    }
    return null;
  };

  const handlePlayerContextMenu = (player: number, event: React.MouseEvent) => {
    event.preventDefault();

    const existingDeath = getExistingDeath(player);
    setDeathModalType(existingDeath?.kind ?? null);
    setDeathModalDayNight(existingDeath?.night ?? null);
    handleSelectDeathPlayer(player);
  };

  return (
    <>
      <PlayerCircleRing
        count={players}
        playerNames={playerNames}
        playerClaims={playerClaims}
        deadFlags={deadFlags}
        selectedPlayer={selectedPlayer}
        onPlayerSelect={handleSelectClaimPlayer}
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
      {selectedPlayer !== null && displayClaimModal && (
        <ClaimModal
          player={selectedPlayer}
          characterOptions={claimRoleOptions}
          characterTypeOptions={characterTypeOptions}
          playerNames={playerNames} 
          onSelectedPlayerChange={handleSelectClaimPlayer}
          infos={infos}
          addInfo={addInfo}
          updateInfo={updateInfo}
          removeInfo={removeInfo}
        />
      )}
      {selectedPlayer !== null && displayDeathModal && (
        <DeathModal
          maxDayNight={players * 2}
          playerNames={playerNames}
          player={selectedPlayer}
          deathType={deathModalType}
          dayNight={deathModalDayNight}
          executions={executions}
          demonKills={demonKills}
          onDeathTypeChange={setDeathModalType}
          onDayNightChange={setDeathModalDayNight}
          onSelectedPlayerChange={handleSelectDeathPlayer}
          setExecutions={setExecutions}
          setDemonKills={setDemonKills}
          removeExecution={removeExecution}
        />
      )}
    </>
  );
}