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

        {/* Stats Footer */}
        {stats && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800/50 backdrop-blur-sm border border-purple-700/30 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-400">{stats.dimension_1.a || 0}</div>
              <div className="text-sm text-gray-400">Core Identity</div>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm border border-purple-700/30 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-blue-400">{stats.dimension_1.b || 0}</div>
              <div className="text-sm text-gray-400">Specialization</div>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm border border-purple-700/30 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-purple-400">{stats.total_updates}</div>
              <div className="text-sm text-gray-400">Total Updates Tracked</div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          Last updated: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : 'Unknown'}
        </div>
      </div>
    </div>
  );
}

export default App;