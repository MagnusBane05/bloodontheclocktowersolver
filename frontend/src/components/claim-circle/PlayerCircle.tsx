import { CSSProperties } from 'react';
import { getPlayerStyles } from '../PlayerCircleRing';

export function titleCaseRole(role: string): string {
  return role
    .toLowerCase()
    .split('_')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
}

export function getAlignment(role: string, evilRoles: Set<string>, goodRoles: Set<string>): 'good' | 'evil' | 'unknown' {
  if (evilRoles.has(role)) {
    return 'evil';
  }

  if (goodRoles.has(role)) {
    return 'good';
  }

  return 'unknown';
}

export interface PlayerCircleProps {
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

export function PlayerCircle({
  player, playerName, role, displayRole, dead = false, selected = false, onClick, onContextMenu, evilRoleNames, goodRoleNames, className = '', style, size = 74, editableName = false, onNameChange,
}: PlayerCircleProps): JSX.Element {
  const nameLabel = playerName ?? `Player ${player}`;
  const subLabel = displayRole ?? (role ? titleCaseRole(role) : null);
  const styles = getPlayerStyles(role ?? '', dead, evilRoleNames, goodRoleNames);

  return (
    <button
      type="button"
      onClick={onClick}
      onContextMenu={onContextMenu}
      className={`flex flex-col items-center justify-center rounded-full border shadow-md text-center p-2 text-white transition ${selected ? 'ring-2 ring-blue-400' : 'border-white/40'} ${onClick ? ' hover:opacity-80 cursor-pointer' : 'cursor-default'}
      ${className}`}
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
          className="pointer-events-auto font-bold text-sm w-[76px] bg-transparent px-0 py-0 text-white text-center whitespace-normal break-words focus:italic rounded-md"
          style={{ outline: 'none', border: 'none' }} />
      ) : (
        <span className="font-bold text-sm break-words">{nameLabel}</span>
      )}
      {subLabel && (
        <span className="mt-1 text-[10px] leading-tight max-w-[60px] break-words capitalize">{subLabel}</span>
      )}
    </button>
  );
}

