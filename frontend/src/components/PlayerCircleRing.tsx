import type { CSSProperties, ReactNode } from 'react';
import { getAlignment, titleCaseRole } from './PlayerCircle';
import VialIcon from '../assets/vial.svg?react';

interface CircleLayoutProps {
  count: number;
  size?: number | string;
  className?: string;
  style?: CSSProperties;
  innerRingClassName?: string;
  renderPlayer: (index: number, style: CSSProperties, angle: number) => ReactNode;
  centerContent?: ReactNode;
}

function CircleLayout({
  count,
  size = 280,
  className = '',
  style,
  innerRingClassName = 'absolute inset-0 rounded-full border border-white/30',
  renderPlayer,
  centerContent,
}: CircleLayoutProps): JSX.Element {
  const ringRadiusPercent = 37.5;

  return (
    <div className={className} style={{ width: size, height: size, position: 'relative', ...style }}>
      <div className={innerRingClassName} />
      {Array.from({ length: count }, (_, index) => {
        const angle = ((-90 + (360 * index) / count) * Math.PI) / 180;
        const x = 50 + Math.cos(angle) * ringRadiusPercent;
        const y = 50 + Math.sin(angle) * ringRadiusPercent;
        return renderPlayer(
          index,
          {
            position: 'absolute',
            left: `${x}%`,
            top: `${y}%`,
            transform: 'translate(-50%, -50%)',
          },
          angle,
        );
      })}
      {centerContent}
    </div>
  );
}

function addAlpha(color: string, opacity: number) {
  const _opacity = Math.round(Math.min(Math.max(opacity ?? 1, 0), 1) * 255);
  return color + _opacity.toString(16).toUpperCase();
}

function getPlayerStyles(
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

interface PlayerCircleProps {
  player: number;
  playerName?: string;
  role?: string;
  displayRole?: string;
  dead?: boolean;
  selected?: boolean;
  onClick?: () => void;
  onContextMenu?: (e: React.MouseEvent) => void;
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
  className?: string;
  style?: CSSProperties;
  size?: number;
  editableName?: boolean;
  onNameChange?: (name: string) => void;
}

function PlayerCircle({
  player,
  playerName,
  role,
  displayRole,
  dead = false,
  selected = false,
  onClick,
  onContextMenu,
  evilRoleNames,
  goodRoleNames,
  className = '',
  style,
  size = 74,
  editableName = false,
  onNameChange,
}: PlayerCircleProps): JSX.Element {
  const nameLabel = playerName ?? `Player ${player}`;
  const subLabel = displayRole ?? (role ? titleCaseRole(role) : null);
  const styles = getPlayerStyles(role ?? '', dead, evilRoleNames, goodRoleNames);

  return (
    <button
      type="button"
      onClick={onClick}
      onContextMenu={onContextMenu}
      className={`flex flex-col items-center justify-center rounded-full border shadow-md text-center p-2 text-white transition ${
        selected ? 'ring-2 ring-blue-400' : 'border-white/40'
      } ${className}`}
      style={{
        width: size,
        height: size,
        backgroundColor: styles.backgroundColor,
        color: styles.color,
        filter: styles.filter,
        borderColor: '#ffffff40',
        ...style,
      }}
    >
      {editableName ? (
        <input
          id={`player-name-input-${player}`}
          value={nameLabel}
          onChange={(event) => onNameChange?.(event.target.value)}
          onClick={(event) => event.stopPropagation()}
          className="font-bold text-sm w-[76px] bg-transparent px-0 py-0 text-white text-center whitespace-normal break-words focus:outline-none focus:ring-0"
          style={{ outline: 'none', border: 'none' }}
        />
      ) : (
        <span className="font-bold text-sm break-words">{nameLabel}</span>
      )}
      {subLabel && (
        <span className="mt-1 text-[10px] leading-tight max-w-[60px] break-words">{subLabel}</span>
      )}
    </button>
  );
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
