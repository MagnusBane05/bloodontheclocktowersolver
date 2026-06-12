import { useEffect, useMemo, useState } from 'react';
import { PlayerCircleRing } from './PlayerCircleRing';
import { getAlignment, titleCaseRole } from "./claim-circle/PlayerCircle";
import type { SolveResponse, GrimoireSolution, GrimoirePage } from '../types';
import { Toggle } from './Toggle';
import { TrashButton } from './TrashButton';
import { Button } from './Button';

interface ResultsDisplayProps {
  results: SolveResponse | null;
  error: string | null;
  playerNames: string[];
}

interface FilterEntry {
  player: number | '';
  role: string;
  alignment: string;
  not: boolean;
}

export function ResultsDisplay({ results, error, playerNames }: ResultsDisplayProps): JSX.Element {
  const [roles, setRoles] = useState<string[]>([]);
  const [evilRoleNames, setEvilRoleNames] = useState<Set<string>>(new Set());
  const [goodRoleNames, setGoodRoleNames] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState<FilterEntry[]>([{ player: '', role: '', alignment: '', not: false }]);

  useEffect(() => {
    fetch('/api/metadata')
      .then((response) => response.json())
      .then((data) => {
        setRoles(data.roles || []);
        setEvilRoleNames(new Set(data.evilRoles || []));
        setGoodRoleNames(new Set(data.goodRoles || []));
      })
      .catch(() => {
        setRoles([]);
        setEvilRoleNames(new Set());
        setGoodRoleNames(new Set());
      });
  }, []);

  useEffect(() => {
    setFilters([{ player: '', role: '', alignment: '', not: false }]);
  }, [results]);

  const playerCount = results?.solutions?.[0]?.pages?.[0]?.characters.length ?? 0;
  const playerOptions = Array.from({ length: playerCount }, (_, i) => ({ value: i, label: `${i}` }));

  const uniqueSolutions = useMemo(() => {
    if (!results) {
      return [];
    }

    let uniqueSolutionsList: GrimoireSolution[] = []

    const comparePages = (a: GrimoirePage, b: GrimoirePage) => {
      if (a.characters.length != b.characters.length) {
        return false;
      }
      for (let i=0; i<a.characters.length; i++) {
        if (a.characters[i] != b.characters[i]) {
          return false;
        }
      }
      return true;
    }

    const compareSolutions = (a: GrimoireSolution, b: GrimoireSolution) => {
      if (a.pages.length != b.pages.length) {
        return false;
      }
      for (let i=0; i<a.pages.length; i++) {
        if (!comparePages(a.pages[i], b.pages[i])) {
          return false
        }
      }
      return true;
    }

    const isSolutionInRemaining = (solution: GrimoireSolution, i: number) => {
      for (let j=i+1; j<results.solutions.length; j++) {
        if (compareSolutions(solution, results.solutions[j])) {
          return true;
        }
      }
      return false;
    }

    for (let i=0; i<results.solutionCount; i++) {
      if (!isSolutionInRemaining(results.solutions[i], i)) {
        uniqueSolutionsList.push(results.solutions[i]);
      }
    }

    return uniqueSolutionsList;
  }, [results])

  const filteredSolutions = useMemo(() => {
    if (!results) {
      return [];
    }

    const activeFilters = filters.filter((filter) =>
      typeof filter.player === 'number' && filter.player >= 0 &&
      (filter.role.trim() !== '' || filter.alignment.trim() !== '')
    );

    if (activeFilters.length === 0) {
      return uniqueSolutions;
    }

    return uniqueSolutions.filter((solution) => {
      const page = solution.pages[0];
      return activeFilters.every((filter) => {
        const playerIndex = filter.player;
        if (typeof playerIndex !== 'number') {
          return false;
        }

        const role = page.characters[playerIndex];
        if (!role) {
          return false;
        }

        const matchesRole = filter.role.trim() === '' || role === filter.role;
        const matchesAlignment = filter.alignment.trim() === '' || getAlignment(role, evilRoleNames, goodRoleNames) === filter.alignment;
        const matches = matchesRole && matchesAlignment;

        return filter.not ? !matches : matches;
      });
    });
  }, [uniqueSolutions, filters, evilRoleNames, goodRoleNames]);

  const clearFilters = () => {
    setFilters([{ player: '', role: '', alignment: '', not: false }]);
  };

  const updateFilter = (index: number, field: keyof FilterEntry, value: string | number | '' | boolean) => {
    setFilters((currentFilters) => {
      const next = [...currentFilters];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const addFilter = () => {
    setFilters((currentFilters) => [...currentFilters, { player: '', role: '', alignment: '', not: false }]);
  };

  const removeFilter = (index: number) => {
    setFilters((currentFilters) => currentFilters.filter((_, i) => i !== index));
  };

  if (error) {
    return (
      <div className="p-4 bg-red-900 border border-red-700 rounded-md">
        <strong className="text-red-200">Error:</strong> <span className="text-red-100">{error}</span>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="p-4 bg-gray-700 rounded-md">
        <p className="text-gray-300">Enter game information and click "Solve" to find possible grimoires.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">
          Solutions Found: {filteredSolutions.length}
          {filteredSolutions.length !== uniqueSolutions.length && (
            <span className="text-gray-300">{' '} (filtered from {uniqueSolutions.length})</span>
          )}
        </h2>
      </div>

      {uniqueSolutions.length > 0 &&
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-sm">
          <div className='flex justify-between items-center'>
            <h3 className="text-xl font-semibold text-white mb-3">Social reads (filters)</h3>
            <div className="flex flex-col gap-3 sm:flex-row pb-4">
              <Button
                type="button"
                onClick={addFilter}
                style="primary"
              >
                <span className='pi pi-plus mr-2 text-sm'/>Add filter
              </Button>
              <Button
                type="button"
                onClick={clearFilters}
                style='remove'
              >
                <span className='pi pi-trash mr-2' />Clear filters
              </Button>
            </div>
          </div>
          <div className="space-y-4">
            {filters.map((filter, index) => (
              <div key={index} className="flex gap-4 justify-between items-end bg-gray-800 rounded-md p-4 border border-gray-700">
                <div className='w-full'>
                  <label className="block text-sm font-medium text-gray-200">Player</label>
                  <select
                    className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white"
                    value={filter.player}
                    onChange={(event) => {
                      const value = event.target.value;
                      updateFilter(index, 'player', value === '' ? '' : Number(value));
                    }}
                  >
                    <option value="">Select player...</option>
                    {playerOptions.map((option) => (
                      <option key={option.value} value={option.value}>{playerNames?.[option.value] ?? `Player ${option.value}`}</option>
                    ))}
                  </select>
                </div>

                <div className='flex flex-col gap-1'>
                  <label className="block text-sm font-medium text-gray-200">NOT</label>
                  <div className='mt-2'>
                    <Toggle 
                      checked={filter.not ?? false}
                      onChange={(b) => updateFilter(index, 'not', b)}
                      id={`filter-not-${index}`}
                    />
                  </div>
                </div>

                <div className='w-full'>
                  <label className="block text-sm font-medium text-gray-200">Role</label>
                  <select
                    className="mt-1 w-full bg-gray-700 border border-gray-600 rounded-md p-2 text-white"
                    value={filter.role}
                    onChange={(event) => updateFilter(index, 'role', event.target.value)}
                  >
                    <option value="">No role filter</option>
                    {roles.map((roleName) => (
                      <option key={roleName} value={roleName}>{titleCaseRole(roleName)}</option>
                    ))}
                  </select>
                </div>

                <div className='w-full'>
                  <label className="block text-sm font-medium text-gray-200">Alignment</label>
                  <div className="flex items-center gap-2">
                    <select
                      className="mt-1 flex-1 bg-gray-700 border border-gray-600 rounded-md p-2 text-white"
                      value={filter.alignment}
                      onChange={(event) => updateFilter(index, 'alignment', event.target.value)}
                    >
                      <option value="">No alignment filter</option>
                      <option value="good">Good</option>
                      <option value="evil">Evil</option>
                    </select>
                  </div>
                </div>
                <div className='pb-2'>
                  <TrashButton
                    onClick={() => removeFilter(index)}
                  />
                </div>
              </div>
            ))}

            <p className="text-sm text-gray-300">
              Add multiple player-based filters. Each row is combined with AND: all active filters must match a solution.
            </p>
          </div>
        </div>
      }

      {uniqueSolutions.length == 0 && 
        <div>No solutions found. Please make sure all information was input correctly. If you believe we're missing a solution, please contact us at</div>
      }

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredSolutions.map((solution, idx) => (
          <SolutionCard key={idx} solution={solution} index={idx} evilRoleNames={evilRoleNames} goodRoleNames={goodRoleNames} playerNames={playerNames} />
        ))}
      </div>
    </div>
  );
}

interface SolutionCardProps {
  solution: GrimoireSolution;
  index: number;
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
  playerNames: string[];
}

function SolutionCard({ solution, index, evilRoleNames, goodRoleNames, playerNames }: SolutionCardProps): JSX.Element {
  const [currentPageIndex, setCurrentPageIndex] = useState(() => Math.max(solution.pages.length - 1, 0));

  useEffect(() => {
    setCurrentPageIndex(Math.max(solution.pages.length - 1, 0));
  }, [solution.pages.length]);

  const page = solution.pages[currentPageIndex];

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-lg shadow-black/50">
      <h3 className="text-lg font-semibold mb-4 text-center text-white">Solution {index + 1}</h3>
      <div className="space-y-4">
        <GrimoirePage page={page} evilRoleNames={evilRoleNames} goodRoleNames={goodRoleNames} playerNames={playerNames} />
        <div className="flex items-center justify-center gap-2">
          <button
            type="button"
            onClick={() => setCurrentPageIndex((current) => Math.max(current - 1, 0))}
            disabled={currentPageIndex <= 0}
            className="w-10 h-10 rounded-full bg-gray-600 hover:bg-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-white flex items-center justify-center"
            aria-label="Previous page"
          >
            <span className='pi pi-chevron-left'/>
          </button>
          <div className="text-sm text-gray-300 text-center min-w-[110px]">
            Page {currentPageIndex + 1} / {solution.pages.length}
          </div>
          <button
            type="button"
            onClick={() => setCurrentPageIndex((current) => Math.min(current + 1, solution.pages.length - 1))}
            disabled={currentPageIndex >= solution.pages.length - 1}
            className="w-10 h-10 rounded-full bg-gray-600 hover:bg-gray-500 disabled:opacity-50 disabled:cursor-not-allowed text-white flex items-center justify-center"
            aria-label="Next page"
          >
            <span className='pi pi-chevron-right'/>
          </button>
        </div>
      </div>
    </div>
  );
}

interface GrimoirePageProps {
  page: GrimoirePage;
  evilRoleNames: Set<string>;
  goodRoleNames: Set<string>;
  playerNames: string[];
}

function GrimoirePage({ page, evilRoleNames, goodRoleNames, playerNames }: GrimoirePageProps): JSX.Element {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-md p-4">
      <h4 className="text-center font-bold text-lg mb-4">Night {page.night}</h4>
      <PlayerCircleRing
        count={page.characters.length}
        playerNames={playerNames}
        playerRoles={page.characters}
        deadFlags={page.dead}
        evilRoleNames={evilRoleNames}
        goodRoleNames={goodRoleNames}
        size={280}
        className="mx-auto"
        innerRingClassName="absolute inset-0 rounded-full border border-gray-800"
        playerSize={74}
        poisoned={page.poisoned}
      />
    </div>
  );
}
