import { useEffect, useState } from 'react';
import GamesTable from './components/GamesTable';
import type { Game, Stats } from './types';

function App() {
  const [games, setGames] = useState<Game[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [gamesRes, statsRes] = await Promise.all([
          fetch('/data/games.json'),
          fetch('/data/stats.json'),
        ]);

        if (!gamesRes.ok || !statsRes.ok) {
          throw new Error('Failed to load data');
        }

        const gamesData = await gamesRes.json();
        const statsData = await statsRes.json();

        setGames(gamesData);
        setStats(statsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black flex items-center justify-center">
        <div className="text-purple-300 text-xl">Loading necromantic data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black flex items-center justify-center">
        <div className="text-red-400 text-xl">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-green-400 mb-2">
            💀 Necro Game News
          </h1>
          <p className="text-gray-400">Tracking the dark arts across {stats?.total_games || 0} games</p>
        </div>

        {/* Main Table */}
        <GamesTable games={games} />

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          Last updated: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : 'Unknown'}
        </div>
      </div>
    </div>
  );
}

export default App;