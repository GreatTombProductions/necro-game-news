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
  const accentColor = isBlood ? 'text-red-400' : 'text-purple-400';
  const accentHover = isBlood ? 'hover:text-red-300' : 'hover:text-purple-300';
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
            <div className="flex items-center justify-center gap-3 sm:gap-4 text-sm sm:text-base">
              <a
                href="https://www.instagram.com/necrotic.realms/"
                target="_blank"
                rel="noopener noreferrer"
                className={`inline-flex items-center gap-1.5 sm:gap-2 ${accentColor} ${accentHover} transition-colors`}
              >
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
                @necrotic.realms
              </a>
              <a
                href="https://ko-fi.com/mortythegravegel"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 sm:gap-2 text-pink-400 hover:text-pink-300 transition-colors"
              >
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.881 8.948c-.773-4.085-4.859-4.593-4.859-4.593H.723c-.604 0-.679.798-.679.798s-.082 7.324-.022 11.822c.164 2.424 2.586 2.672 2.586 2.672s8.267-.023 11.966-.049c2.438-.426 2.683-2.566 2.658-3.734 4.352.24 7.422-2.831 6.649-6.916zm-11.062 3.511c-1.246 1.453-4.011 3.976-4.011 3.976s-.121.119-.31.023c-.076-.057-.108-.09-.108-.09-.443-.441-3.368-3.049-4.034-3.954-.709-.965-1.041-2.7-.091-3.71.951-1.01 3.005-1.086 4.363.407 0 0 1.565-1.782 3.468-.963 1.904.82 1.832 3.011.723 4.311zm6.173.478c-.928.116-1.682.028-1.682.028V7.284h1.77s1.971.551 1.971 2.638c0 1.913-.985 2.667-2.059 3.015z"/>
                </svg>
                <span className="hidden sm:inline">Support Morty the Grave Gel</span>
                <span className="sm:hidden">Support</span>
              </a>
            </div>
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