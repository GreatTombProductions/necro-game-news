import type { RegistryMode } from '../types';

interface ModeToggleProps {
  mode: RegistryMode;
  onModeChange: (mode: RegistryMode) => void;
}

export default function ModeToggle({ mode, onModeChange }: ModeToggleProps) {
  const isBlood = mode === 'blood';

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onModeChange(isBlood ? 'necromancy' : 'blood')}
        className={`
          relative flex items-center gap-2 px-3 py-1.5 rounded-full
          font-medium text-sm transition-all duration-300 ease-in-out
          border-2
          ${isBlood
            ? 'bg-red-900/50 border-red-500 text-red-200 hover:bg-red-900/70'
            : 'bg-purple-900/50 border-purple-500 text-purple-200 hover:bg-purple-900/70'
          }
        `}
        title={`Switch to ${isBlood ? 'Necromancy' : 'Blood'} Registry`}
      >
        {/* Necromancy icon (skull) */}
        <span
          className={`transition-opacity duration-300 ${isBlood ? 'opacity-40' : 'opacity-100'}`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-4 h-4"
          >
            <path d="M12 2C6.48 2 2 6.48 2 12c0 2.76 1.12 5.26 2.93 7.07L12 22l7.07-2.93C20.88 17.26 22 14.76 22 12c0-5.52-4.48-10-10-10zm-2 15v-2h4v2h-4zm4-4h-4v-2h4v2zm2-4c0 .55-.45 1-1 1h-1v1h-4v-1H9c-.55 0-1-.45-1-1V7c0-.55.45-1 1-1h6c.55 0 1 .45 1 1v2z" />
          </svg>
        </span>

        {/* Toggle indicator */}
        <div className="relative w-10 h-5 rounded-full bg-gray-700/50 transition-colors duration-300">
          <div
            className={`
              absolute top-0.5 w-4 h-4 rounded-full transition-all duration-300
              ${isBlood
                ? 'left-5 bg-red-400'
                : 'left-0.5 bg-purple-400'
              }
            `}
          />
        </div>

        {/* Blood icon (drop) */}
        <span
          className={`transition-opacity duration-300 ${isBlood ? 'opacity-100' : 'opacity-40'}`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-4 h-4"
          >
            <path d="M12 2c-5.33 4.55-8 8.48-8 11.8 0 4.98 3.8 8.2 8 8.2s8-3.22 8-8.2c0-3.32-2.67-7.25-8-11.8zm0 18c-3.35 0-6-2.57-6-6.2 0-2.34 1.95-5.44 6-9.14 4.05 3.7 6 6.79 6 9.14 0 3.63-2.65 6.2-6 6.2z" />
          </svg>
        </span>
      </button>
    </div>
  );
}
