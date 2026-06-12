import { ReactNode } from 'react';
import { getAlignment } from "./claim-circle/PlayerCircle";
import VialIcon from '../assets/vial.svg?react';
import { PlayerCircle } from './claim-circle/PlayerCircle';
import { CircleLayout } from './claim-circle/CircleLayout';

function addAlpha(color: string, opacity: number) {
  const _opacity = Math.round(Math.min(Math.max(opacity ?? 1, 0), 1) * 255);
  return color + _opacity.toString(16).toUpperCase();
}

export function getPlayerStyles(
  role: string,
  dead: boolean,
  evilRoles: Set<string>,
  goodRoles: Set<string>,
): { backgroundColor: string; color: string; filter?: string } {
  const alignment = getAlignment(role, evilRoles, goodRoles);
  const aliveStyle =
    alignment === 'unknown'
      ? { backgroundColor: '#808080', color: '#ffffff' }
      : alignment === 'evil'
      ? { backgroundColor: '#ef4444', color: '#ffffff' }
      : { backgroundColor: '#3b82f6', color: '#ffffff' };

  if (!dead) {
    return aliveStyle;
  }

  const deadBackground = addAlpha(aliveStyle.backgroundColor, 0.35);
  return { backgroundColor: deadBackground, color: '#ffffff', filter: 'grayscale(40%)' };
}

interface PlayerCircleRingProps {
  count: number;
  playerNames?: string[];
  playerRoles?: string[];
  deadFlags?: boolean[];
  playerClaims?: Record<number, string[]>;
  selectedPlayer?: number | null;
  onPlayerSelect?: (player: number) => void;
  onPlayerNameChange?: (player: number, name: string) => void;
  editablePlayerNames?: boolean;
  onPlayerContextMenu?: (player: number, e: React.MouseEvent) => void;
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
  size?: number | string;
  className?: string;
  innerRingClassName?: string;
  playerSize?: number;
  centerContent?: ReactNode;
  poisoned?: boolean[];
}

function getClaimDisplayRole(claims: Record<number, string[]> | undefined, index: number): string | undefined {
  const claimLabels = claims?.[index] ?? [];
  if (claimLabels.length === 0) {
    return undefined;
  }

  return `${claimLabels[0]}${claimLabels.length > 1 ? ` +${claimLabels.length - 1}` : ''}`;
}

export function PlayerCircleRing({
  count,
  playerNames,
  playerRoles = [],
  deadFlags = [],
  playerClaims,
  selectedPlayer = null,
  onPlayerSelect,
  onPlayerNameChange,
  editablePlayerNames = false,
  onPlayerContextMenu,
  evilRoleNames,
  goodRoleNames,
  size = 280,
  className = '',
  innerRingClassName = 'absolute inset-0 rounded-full border border-white/30',
  playerSize = 74,
  centerContent,
  poisoned,
}: PlayerCircleRingProps): JSX.Element {
  
  const showEditableNames = editablePlayerNames && typeof onPlayerNameChange === 'function';

  return (
    <div className={className} style={{ width: size, height: size, position: 'relative' }}>
      <CircleLayout
        count={count}
        size="100%"
        className="h-full w-full"
        innerRingClassName={innerRingClassName}
        renderPlayer={(index, style, angle) => {
          const claimLabels = playerClaims?.[index] ?? [];
          const role = claimLabels.length > 0 ? claimLabels[0] : playerRoles[index];
          const displayRole = getClaimDisplayRole(playerClaims, index);
          const dead = deadFlags[index] ?? false;
          const name = playerNames?.[index] ?? `Player ${index + 1}`;
          const showPoisonIndicator = poisoned?.[index];
          const poisonRadiusPercent = 19;
          const poisonX = 50 + Math.cos(angle) * poisonRadiusPercent;
          const poisonY = 50 + Math.sin(angle) * poisonRadiusPercent;

          return [
            <div
              key={`player-${index}`}
              style={{
                position: 'absolute',
                left: style.left,
                top: style.top,
                transform: style.transform,
                width: playerSize,
                height: playerSize,
                pointerEvents: 'auto',
              }}
            >
              <div className="relative mx-auto" style={{ width: playerSize, height: playerSize }}>
                <PlayerCircle
                  player={index}
                  playerName={name}
                  role={role}
                  displayRole={displayRole}
                  dead={dead}
                  selected={selectedPlayer === index}
                  onClick={onPlayerSelect ? () => onPlayerSelect(index) : undefined}
                  onContextMenu={onPlayerContextMenu ? (e) => {
                    e.preventDefault();
                    onPlayerContextMenu(index, e);
                  } : undefined}
                  evilRoleNames={evilRoleNames}
                  goodRoleNames={goodRoleNames}
                  className=""
                  style={{ width: playerSize, height: playerSize }}
                  size={playerSize}
                  editableName={showEditableNames}
                  onNameChange={showEditableNames ? (value) => onPlayerNameChange(index, value) : undefined}
                />
              </div>
            </div>,
            showPoisonIndicator ? (
              <div
                key={`poison-${index}`}
                className="absolute flex items-center justify-center rounded-full border border-gray-600 shadow-md"
                style={{
                  left: `${poisonX}%`,
                  top: `${poisonY}%`,
                  transform: 'translate(-50%, -50%)',
                  width: 22,
                  height: 22,
                  pointerEvents: 'none',
                }}
              >
                <VialIcon width={14} height={14} fill="#dc2626" />
              </div>
            ) : null,
          ];
        }}
      />
      {centerContent}
    </div>
  );
}
