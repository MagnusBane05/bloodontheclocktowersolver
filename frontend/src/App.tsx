import { useState } from 'react';
import { GameForm } from './components/game-form/GameForm';
import { ResultsDisplay } from './ResultsDisplay';
import { SolveRequest, SolveResponse } from './types';

function App(): JSX.Element {
  const [results, setResults] = useState<SolveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSolve = async (request: SolveRequest) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch('/api/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'An error occurred');
      }

      const result: SolveResponse = await response.json();
      setResults(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-800 to-gray-900 text-gray-100 p-4">
      <div className="max-w-6xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 text-shadow">Blood on the Clocktower Solver</h1>
          <p className="text-lg opacity-90">Enter game information to find possible grimoires</p>
        </header>

        <main className="space-y-8">
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <GameForm onSubmit={handleSolve} loading={loading} />
          </div>

          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <ResultsDisplay results={results} error={error} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;