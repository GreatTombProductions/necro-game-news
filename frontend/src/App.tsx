import { useEffect, useState, useCallback, useRef } from 'react';
import GamesTable from './components/GamesTable';
import ModeToggle from './components/ModeToggle';
import type { Game, Stats, BloodStats, RegistryMode } from './types';

// Get initial mode from URL
function getInitialMode(): RegistryMode {
  const params = new URLSearchParams(window.location.search);
  const urlMode = params.get('mode');
  if (urlMode === 'blood') return 'blood';
  return 'necromancy';
}

function App() {
  const [mode, setMode] = useState<RegistryMode>(getInitialMode);
  const [games, setGames] = useState<Game[]>([]);
  const [stats, setStats] = useState<Stats | BloodStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isInitialLoad = useRef(true);

  // Handle mode change - update URL and reload data
  const handleModeChange = useCallback((newMode: RegistryMode) => {
    setMode(newMode);
    // Update URL without reload
    const params = new URLSearchParams(window.location.search);
    if (newMode === 'necromancy') {
      params.delete('mode');
    } else {
      params.set('mode', newMode);
    }
    const newUrl = params.toString()
      ? `${window.location.pathname}?${params.toString()}`
      : window.location.pathname;
    window.history.replaceState({}, '', newUrl);
  }, []);

  useEffect(() => {
    async function loadData() {
      // Only show loading screen on initial load, not mode switches
      if (isInitialLoad.current) {
        setLoading(true);
      }

      try {
        // Choose data files based on mode
        const gamesPath = mode === 'necromancy' ? '/data/games.json' : '/data/blood_games.json';
        const statsPath = mode === 'necromancy' ? '/data/stats.json' : '/data/blood_stats.json';

        const [gamesRes, statsRes] = await Promise.all([
          fetch(gamesPath),
          fetch(statsPath),
        ]);

        if (!gamesRes.ok || !statsRes.ok) {
          throw new Error('Failed to load data');
        }

        const gamesData = await gamesRes.json();
        const statsData = await statsRes.json();

        setGames(gamesData);
        setStats(statsData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
        isInitialLoad.current = false;
      }
    }

    loadData();
  }, [mode]);

  // Mode-based styling
  const isBlood = mode === 'blood';
  const bgGradient = isBlood
    ? 'from-gray-900 via-red-900 to-black'
    : 'from-gray-900 via-purple-900 to-black';
  const titleGradient = isBlood
    ? 'from-red-400 to-rose-400'
    : 'from-purple-400 to-green-400';
  const loadingText = isBlood ? 'Loading blood data...' : 'Loading necromantic data...';
  const tagline = isBlood
    ? 'Where thirst finds focus'
    : 'Where necromancy games rise from obscurity';

  if (loading) {
    return (
      <div className={`min-h-screen bg-gradient-to-br ${bgGradient} flex items-center justify-center transition-colors duration-300`}>
        <div className={`${isBlood ? 'text-red-300' : 'text-purple-300'} text-xl`}>{loadingText}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-screen bg-gradient-to-br ${bgGradient} flex items-center justify-center transition-colors duration-300`}>
        <div className="text-red-400 text-xl">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gradient-to-br ${bgGradient} p-4 sm:p-8 transition-colors duration-300`}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-4 sm:mb-8">
          {/* Title row with toggle */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 mb-1 sm:mb-2">
            <h1 className={`text-3xl sm:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r ${titleGradient} pb-1 transition-all duration-300 min-w-[240px] sm:min-w-[380px] text-center`}>
              {isBlood ? 'Vampiric Realms' : 'Necrotic Realms'}
            </h1>
            <ModeToggle mode={mode} onModeChange={handleModeChange} />
          </div>

          <div className="text-center">
            <p className="text-sm sm:text-base text-gray-400 mb-2 sm:mb-3 transition-colors duration-300">{tagline}</p>
          </div>
        </div>

        {/* Main Table */}
        <GamesTable games={games} mode={mode} />

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          Last updated: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : 'Unknown'}
        </div>
      </div>
    </div>
  );
}

export default App;