import type { SolveResponse, GrimoireSolution, GrimoirePage } from './types';

interface ResultsDisplayProps {
  results: SolveResponse | null;
  error: string | null;
}

export function ResultsDisplay({ results, error }: ResultsDisplayProps): JSX.Element {
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
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">Solutions Found: {results.solutionCount}</h2>
      </div>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {results.solutions.map((solution, idx) => (
          <SolutionCard key={idx} solution={solution} index={idx} />
        ))}
      </div>
    </div>
  );
};

interface SolutionCardProps {
  solution: GrimoireSolution;
  index: number;
}

function SolutionCard({ solution, index }: SolutionCardProps): JSX.Element {
  return (
    <div className="bg-gray-700 rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-semibold mb-4 text-center text-white">Solution {index + 1}</h3>
      <div className="space-y-4">
        {solution.pages.map((page, pageIdx) => (
          <GrimoirePage key={pageIdx} page={page} />
        ))}
      </div>
    </div>
  );
}

interface GrimoirePageProps {
  page: GrimoirePage;
}

function GrimoirePage({ page }: GrimoirePageProps): JSX.Element {
  return (
    <div className="bg-yellow-100 border-4 border-yellow-800 rounded-md p-4">
      <h4 className="text-center font-bold text-lg mb-4 text-yellow-900">Night {page.night}</h4>
      <div className="grid grid-cols-5 gap-2">
        {page.characters.map((char, i) => (
          <div key={i} className={`p-2 rounded text-center ${page.dead[i] ? 'bg-red-200 text-red-800' : 'bg-green-200 text-green-800'}`}>
            <div className="font-bold">{i}</div>
            <div className="text-sm">{char}</div>
          </div>
        ))}
      </div>
    </div>
  );
}