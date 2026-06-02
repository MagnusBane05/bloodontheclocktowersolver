import { SolveRequest } from '../../types';
import { PlayerCircleRing } from '../PlayerCircleRing';
import { NumberField, SelectField } from './fields';
import { InfoFields } from './info-sections';
import { DeathModal } from './DeathModal';
import { ClaimModal } from './ClaimModal';
import { PlayerSelectModal } from './PlayerSelectModal';
import { useGameForm } from './useGameForm';
import { InfoEntry } from './InfoEntry';
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

export function GameForm({ onSubmit, loading }: { onSubmit: (request: SolveRequest) => void; loading: boolean }): JSX.Element {
  const {
    players,
    setPlayers,
    infos,
    claimRoleOptions,
    minionOptions,
    townsfolkOptions,
    allInfoKinds,
    evilRoleNames,
    goodRoleNames,
    selectedClaimPlayer,
    selectedClaimCharacter,
    infoErrors,
    selectedDeathPlayer,
    deathModalType,
    deathModalDayNight,
    activePlayerSelectModal,
    playerSelectLabel,
    playerClaimMap,
    deadFlags,
    computeEmpathNeighboursLocal,
    getBodyFromPreviousNightLocal,
    handleAddClaim,
    handleAddClaimAndInfo,
    handleClearClaim,
    handleCloseClaimModal,
    handlePlayerContextMenu,
    handleDeathConfirm,
    handleCloseDeathModal,
    handleClearDeath,
    handlePlayerSelectClick,
    handleClosePlayerSelectModal,
    handlePlayerSelectConfirm,
    handleSubmit,
    addInfo,
    clearInfo,
    updateInfo,
    removeInfo,
    setSelectedClaimPlayer,
    setSelectedClaimCharacter,
    setDeathModalType,
    setDeathModalDayNight,
  } = useGameForm(onSubmit);

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          <div className="space-y-4">
            <div className="rounded-xl border border-gray-600 bg-gray-800 p-5 shadow-sm">
              <div className="relative">
                <div className="flex justify-between mb-2">
                  <div>
                    <h3 className="text-lg font-semibold">Graphical Claim Input</h3>
                    <p className="text-sm text-gray-300">Click a player in the circle to pick a role.</p>
                    <p className="text-sm text-gray-300">Right click to set their death (execution or demon kill).</p>
                  </div>
                  <div className="space-y-2">
                    <NumberField
                      id={`player-count`}
                      label="Number of players"
                      value={players}
                      min={5}
                      max={15}
                      onChange={(value) => setPlayers(value ?? 5)}
                    />
                  </div>
                </div>
                <div className="mx-auto w-full max-w-md">
                  <div className="relative aspect-square w-full rounded-full border border-gray-600 bg-gray-900/80">
                    <PlayerCircleRing
                      count={players}
                      playerClaims={playerClaimMap}
                      deadFlags={deadFlags}
                      selectedPlayer={selectedClaimPlayer}
                      onPlayerSelect={setSelectedClaimPlayer}
                      onPlayerContextMenu={handlePlayerContextMenu}
                      evilRoleNames={evilRoleNames}
                      goodRoleNames={goodRoleNames}
                      size="100%"
                      className="h-full w-full"
                      innerRingClassName="absolute inset-0 rounded-full border border-yellow-800/30"
                      playerSize={74}
                    />
                  </div>
                </div>
                {selectedClaimPlayer !== null && (
                  <ClaimModal
                    player={selectedClaimPlayer}
                    value={selectedClaimCharacter}
                    options={claimRoleOptions}
                    onChange={setSelectedClaimCharacter}
                    onAddClaim={() => handleAddClaim(selectedClaimCharacter)}
                    onAddClaimAndInfo={() => handleAddClaimAndInfo(selectedClaimCharacter)}
                    onClear={handleClearClaim}
                    onClose={handleCloseClaimModal}
                    infoKindExists={!!getInfoKindForClaimRole(selectedClaimCharacter)}
                  />
                )}
                {selectedDeathPlayer !== null && (
                  <DeathModal
                    player={selectedDeathPlayer}
                    deathType={deathModalType}
                    dayNight={deathModalDayNight}
                    maxDayNight={players * 2}
                    onDeathTypeChange={setDeathModalType}
                    onDayNightChange={setDeathModalDayNight}
                    onConfirm={handleDeathConfirm}
                    onClear={handleClearDeath}
                    onClose={handleCloseDeathModal}
                  />
                )}
                {activePlayerSelectModal !== null && (
                  <PlayerSelectModal
                    playerCount={players}
                    selectionLabel={playerSelectLabel}
                    onSelect={handlePlayerSelectConfirm}
                    onCancel={handleClosePlayerSelectModal}
                    evilRoleNames={evilRoleNames}
                    goodRoleNames={goodRoleNames}
                  />
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-xl border border-gray-600 bg-gray-800 p-5 shadow-sm">
              <h3 className="text-lg font-semibold">Info List</h3>
              <div className="space-y-4">
                {infos.map((info, index) => (
                  <InfoEntry
                    key={index}
                    info={info}
                    index={index}
                    allInfoKinds={allInfoKinds}
                    infoErrors={infoErrors}
                    claimRoleOptions={claimRoleOptions}
                    minionOptions={minionOptions}
                    townsfolkOptions={townsfolkOptions}
                    updateInfo={updateInfo}
                    removeInfo={removeInfo}
                    computeEmpathNeighbours={computeEmpathNeighboursLocal}
                    getBodyFromPreviousNight={getBodyFromPreviousNightLocal}
                    activePlayerSelectModal={activePlayerSelectModal}
                    onPlayerSelectClick={handlePlayerSelectClick}
                    evilRoleNames={evilRoleNames}
                    goodRoleNames={goodRoleNames}
                  />
                ))}
                <div className="flex flex-col gap-3 sm:flex-row">
                  <button
                    type="button"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
                    onClick={addInfo}
                  >
                    Add Info
                  </button>
                  <button
                    type="button"
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md"
                    onClick={clearInfo}
                  >
                    Clear all info
                  </button>
                </div>
              </div>
            </div>
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
    </div>
  );
}
