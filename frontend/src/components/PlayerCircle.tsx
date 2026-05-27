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
