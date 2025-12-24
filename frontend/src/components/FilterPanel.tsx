import { Fragment, useState } from 'react';
import type { Platform, RegistryMode, Vampirism, HemomancyCentrality, POV } from '../types';
import { PLATFORM_INFO } from '../types';

// Types
export interface NecromancyFilter {
  centrality: 'a' | 'b' | 'c' | 'd';
  pov: 'character' | 'unit';
  naming: 'explicit' | 'implied';
}

export type Availability = 'instant' | 'gated' | 'unknown';

export interface FilterState {
  genres: string[];
  platforms: Platform[];
  announcementDateFrom: string;
  announcementDateTo: string;
  lastUpdatedFrom: string;
  lastUpdatedTo: string;
  priceMin: string;
  priceMax: string;
  includeEarlyAccess: boolean;
  includeUnreleased: boolean;
  availability: Availability[];
  necromancyGrid: NecromancyFilter[];
  // Blood registry filters
  vampirism: Vampirism[];
  hemomancy: HemomancyCentrality[];
  bloodPov: POV[];
}

// Necromancy dimension keys
const CENTRALITY_KEYS = ['a', 'b', 'c', 'd'] as const;
const POV_KEYS = ['character', 'unit'] as const;
const NAMING_KEYS = ['explicit', 'implied'] as const;
const AVAILABILITY_KEYS: Availability[] = ['instant', 'gated', 'unknown'];

// Blood dimension keys
const VAMPIRISM_KEYS: Vampirism[] = ['outright', 'implied', 'channeled', 'absent'];
const HEMOMANCY_KEYS: HemomancyCentrality[] = ['a', 'b', 'c', 'd', 'absent'];
const BLOOD_POV_KEYS: POV[] = ['character', 'unit'];

// Generate all 16 necromancy combinations
export function getAllNecromancyCombinations(): NecromancyFilter[] {
  const combinations: NecromancyFilter[] = [];
  for (const centrality of CENTRALITY_KEYS) {
    for (const pov of POV_KEYS) {
      for (const naming of NAMING_KEYS) {
        combinations.push({ centrality, pov, naming });
      }
    }
  }
  return combinations;
}

// Initial state with all necromancy checkboxes checked
export const initialFilterState: FilterState = {
  genres: [],
  platforms: [],
  announcementDateFrom: '',
  announcementDateTo: '',
  lastUpdatedFrom: '',
  lastUpdatedTo: '',
  priceMin: '',
  priceMax: '',
  includeEarlyAccess: true,
  includeUnreleased: false,
  availability: [...AVAILABILITY_KEYS],
  necromancyGrid: getAllNecromancyCombinations(),
  // Blood filters - all selected by default
  vampirism: [...VAMPIRISM_KEYS],
  hemomancy: [...HEMOMANCY_KEYS],
  bloodPov: [...BLOOD_POV_KEYS],
};

interface FilterPanelProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  availableGenres: string[];
  availablePlatforms: Platform[];
  onClear: () => void;
  matchingCount: number;
  totalCount: number;
  mode: RegistryMode;
}

// Necromancy dimension labels
const CENTRALITY_LABELS: Record<string, string> = {
  a: 'Core',
  b: 'Dedicated Branch',
  c: 'Isolated',
  d: 'Minimal',
};

// Availability labels
const AVAILABILITY_LABELS: Record<Availability, string> = {
  instant: 'Instant',
  gated: 'Gated',
  unknown: 'Unknown',
};

// Blood dimension labels
const VAMPIRISM_LABELS: Record<Vampirism, string> = {
  outright: 'Outright',
  implied: 'Implied',
  channeled: 'Channeled',
  absent: 'Absent',
};

const HEMOMANCY_LABELS: Record<HemomancyCentrality, string> = {
  a: 'Core',
  b: 'Dedicated Branch',
  c: 'Isolated',
  d: 'Minimal',
  absent: 'Absent',
};

const BLOOD_POV_LABELS: Record<POV, string> = {
  character: 'Character',
  unit: 'Unit',
};

// Helper to check if a combination is selected
function isSelected(
  grid: NecromancyFilter[],
  centrality: string,
  pov: string,
  naming: string
): boolean {
  return grid.some(
    (f) => f.centrality === centrality && f.pov === pov && f.naming === naming
  );
}

// Availability Checkboxes Component
function AvailabilityCheckboxes({
  value,
  onChange,
}: {
  value: Availability[];
  onChange: (availability: Availability[]) => void;
}) {
  const toggleAvailability = (avail: Availability) => {
    if (value.includes(avail)) {
      onChange(value.filter((a) => a !== avail));
    } else {
      onChange([...value, avail]);
    }
  };

  const selectAll = () => onChange([...AVAILABILITY_KEYS]);
  const deselectAll = () => onChange([]);
  const allSelected = value.length === AVAILABILITY_KEYS.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        {AVAILABILITY_KEYS.map((avail) => (
          <label
            key={avail}
            className="flex items-center gap-1.5 cursor-pointer text-sm"
          >
            <input
              type="checkbox"
              checked={value.includes(avail)}
              onChange={() => toggleAvailability(avail)}
              className="w-4 h-4 rounded border-purple-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800 cursor-pointer"
            />
            <span className="text-gray-300">{AVAILABILITY_LABELS[avail]}</span>
          </label>
        ))}
      </div>
      <button
        type="button"
        onClick={allSelected ? deselectAll : selectAll}
        className="text-xs text-gray-500 hover:text-purple-300 transition-colors"
      >
        {allSelected ? 'Deselect all' : 'Select all'}
      </button>
    </div>
  );
}

// Vampirism Checkboxes Component (Blood mode)
function VampirismCheckboxes({
  value,
  onChange,
}: {
  value: Vampirism[];
  onChange: (vampirism: Vampirism[]) => void;
}) {
  const toggleVampirism = (v: Vampirism) => {
    if (value.includes(v)) {
      onChange(value.filter((x) => x !== v));
    } else {
      onChange([...value, v]);
    }
  };

  const selectAll = () => onChange([...VAMPIRISM_KEYS]);
  const deselectAll = () => onChange([]);
  const allSelected = value.length === VAMPIRISM_KEYS.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        {VAMPIRISM_KEYS.map((v) => (
          <label
            key={v}
            className="flex items-center gap-1.5 cursor-pointer text-sm"
          >
            <input
              type="checkbox"
              checked={value.includes(v)}
              onChange={() => toggleVampirism(v)}
              className="w-4 h-4 rounded border-red-600 bg-gray-700 text-red-500 focus:ring-red-500 focus:ring-offset-gray-800 cursor-pointer"
            />
            <span className="text-gray-300">{VAMPIRISM_LABELS[v]}</span>
          </label>
        ))}
      </div>
      <button
        type="button"
        onClick={allSelected ? deselectAll : selectAll}
        className="text-xs text-gray-500 hover:text-red-300 transition-colors"
      >
        {allSelected ? 'Deselect all' : 'Select all'}
      </button>
    </div>
  );
}

// Hemomancy Checkboxes Component (Blood mode)
function HemomancyCheckboxes({
  value,
  onChange,
}: {
  value: HemomancyCentrality[];
  onChange: (hemomancy: HemomancyCentrality[]) => void;
}) {
  const toggleHemomancy = (h: HemomancyCentrality) => {
    if (value.includes(h)) {
      onChange(value.filter((x) => x !== h));
    } else {
      onChange([...value, h]);
    }
  };

  const selectAll = () => onChange([...HEMOMANCY_KEYS]);
  const deselectAll = () => onChange([]);
  const allSelected = value.length === HEMOMANCY_KEYS.length;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3">
        {HEMOMANCY_KEYS.map((h) => (
          <label
            key={h}
            className="flex items-center gap-1.5 cursor-pointer text-sm"
          >
            <input
              type="checkbox"
              checked={value.includes(h)}
              onChange={() => toggleHemomancy(h)}
              className="w-4 h-4 rounded border-red-600 bg-gray-700 text-red-500 focus:ring-red-500 focus:ring-offset-gray-800 cursor-pointer"
            />
            <span className="text-gray-300">{HEMOMANCY_LABELS[h]}</span>
          </label>
        ))}
      </div>
      <button
        type="button"
        onClick={allSelected ? deselectAll : selectAll}
        className="text-xs text-gray-500 hover:text-red-300 transition-colors"
      >
        {allSelected ? 'Deselect all' : 'Select all'}
      </button>
    </div>
  );
}

// Blood POV Checkboxes Component (Blood mode)
function BloodPovCheckboxes({
  value,
  onChange,
}: {
  value: POV[];
  onChange: (pov: POV[]) => void;
}) {
  const togglePov = (p: POV) => {
    if (value.includes(p)) {
      onChange(value.filter((x) => x !== p));
    } else {
      onChange([...value, p]);
    }
  };

  const selectAll = () => onChange([...BLOOD_POV_KEYS]);
  const deselectAll = () => onChange([]);
  const allSelected = value.length === BLOOD_POV_KEYS.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        {BLOOD_POV_KEYS.map((p) => (
          <label
            key={p}
            className="flex items-center gap-1.5 cursor-pointer text-sm"
          >
            <input
              type="checkbox"
              checked={value.includes(p)}
              onChange={() => togglePov(p)}
              className="w-4 h-4 rounded border-red-600 bg-gray-700 text-red-500 focus:ring-red-500 focus:ring-offset-gray-800 cursor-pointer"
            />
            <span className="text-gray-300">{BLOOD_POV_LABELS[p]}</span>
          </label>
        ))}
      </div>
      <button
        type="button"
        onClick={allSelected ? deselectAll : selectAll}
        className="text-xs text-gray-500 hover:text-red-300 transition-colors"
      >
        {allSelected ? 'Deselect all' : 'Select all'}
      </button>
    </div>
  );
}

// Necromancy Grid Component
function NecromancyGrid({
  value,
  onChange,
}: {
  value: NecromancyFilter[];
  onChange: (grid: NecromancyFilter[]) => void;
}) {
  const toggleCell = (centrality: string, pov: string, naming: string) => {
    const exists = isSelected(value, centrality, pov, naming);
    if (exists) {
      onChange(
        value.filter(
          (f) =>
            !(f.centrality === centrality && f.pov === pov && f.naming === naming)
        )
      );
    } else {
      onChange([
        ...value,
        {
          centrality: centrality as NecromancyFilter['centrality'],
          pov: pov as NecromancyFilter['pov'],
          naming: naming as NecromancyFilter['naming'],
        },
      ]);
    }
  };

  // Helper to get all combinations for a row (centrality level)
  const getRowCombinations = (centrality: string): NecromancyFilter[] => {
    const combinations: NecromancyFilter[] = [];
    for (const pov of POV_KEYS) {
      for (const naming of NAMING_KEYS) {
        combinations.push({
          centrality: centrality as NecromancyFilter['centrality'],
          pov,
          naming,
        });
      }
    }
    return combinations;
  };

  // Helper to get all combinations for a column (naming type across all)
  const getColumnCombinations = (pov: typeof POV_KEYS[number], naming: typeof NAMING_KEYS[number]): NecromancyFilter[] => {
    return CENTRALITY_KEYS.map((centrality) => ({
      centrality,
      pov,
      naming,
    }));
  };

  // Helper to get all combinations for a POV group (character or unit)
  const getPovCombinations = (pov: typeof POV_KEYS[number]): NecromancyFilter[] => {
    const combinations: NecromancyFilter[] = [];
    for (const centrality of CENTRALITY_KEYS) {
      for (const naming of NAMING_KEYS) {
        combinations.push({
          centrality,
          pov,
          naming,
        });
      }
    }
    return combinations;
  };

  // Check if all combinations in a group are selected
  const areAllSelected = (combinations: NecromancyFilter[]): boolean => {
    return combinations.every((c) =>
      value.some(
        (v) => v.centrality === c.centrality && v.pov === c.pov && v.naming === c.naming
      )
    );
  };

  // Toggle all combinations in a group (select all if any unselected, deselect all if all selected)
  const toggleGroup = (combinations: NecromancyFilter[]) => {
    const allSelected = areAllSelected(combinations);
    if (allSelected) {
      // Deselect all in group
      onChange(
        value.filter(
          (v) =>
            !combinations.some(
              (c) => c.centrality === v.centrality && c.pov === v.pov && c.naming === v.naming
            )
        )
      );
    } else {
      // Select all in group (add missing ones)
      const missing = combinations.filter(
        (c) =>
          !value.some(
            (v) => v.centrality === c.centrality && v.pov === c.pov && v.naming === c.naming
          )
      );
      onChange([...value, ...missing]);
    }
  };

  const selectAllCheckboxClass = "w-4 h-4 rounded border-purple-500 bg-gray-600 text-purple-400 focus:ring-purple-500 focus:ring-offset-gray-800 cursor-pointer";

  return (
    <div className="overflow-x-auto">
      <table className="text-xs">
        <thead>
          <tr>
            <th className="px-2 py-1"></th>
            <th className="px-2 py-1"></th>
            <th colSpan={2} className="px-2 py-1 text-center border-b border-purple-700/30">
              <label className="flex items-center justify-center gap-1.5 cursor-pointer text-purple-300">
                <input
                  type="checkbox"
                  checked={areAllSelected(getPovCombinations('character'))}
                  onChange={() => toggleGroup(getPovCombinations('character'))}
                  className={selectAllCheckboxClass}
                />
                Character
              </label>
            </th>
            <th className="px-1 text-gray-600">|</th>
            <th colSpan={2} className="px-2 py-1 text-center border-b border-purple-700/30">
              <label className="flex items-center justify-center gap-1.5 cursor-pointer text-purple-300">
                <input
                  type="checkbox"
                  checked={areAllSelected(getPovCombinations('unit'))}
                  onChange={() => toggleGroup(getPovCombinations('unit'))}
                  className={selectAllCheckboxClass}
                />
                Unit
              </label>
            </th>
          </tr>
          <tr>
            <th className="px-2 py-1"></th>
            <th className="px-2 py-1"></th>
            <th className="px-2 py-1 text-center text-gray-400 font-normal">Explicit</th>
            <th className="px-2 py-1 text-center text-gray-400 font-normal">Implied</th>
            <th className="px-1 text-gray-600">|</th>
            <th className="px-2 py-1 text-center text-gray-400 font-normal">Explicit</th>
            <th className="px-2 py-1 text-center text-gray-400 font-normal">Implied</th>
          </tr>
        </thead>
        <tbody>
          {CENTRALITY_KEYS.map((centrality) => (
            <tr key={centrality}>
              <td className="px-2 py-1 text-gray-300 font-medium whitespace-nowrap">
                {CENTRALITY_LABELS[centrality]}
              </td>
              {/* Row select-all checkbox */}
              <td className="px-2 py-1 text-center">
                <input
                  type="checkbox"
                  checked={areAllSelected(getRowCombinations(centrality))}
                  onChange={() => toggleGroup(getRowCombinations(centrality))}
                  className={selectAllCheckboxClass}
                  title={`Select all ${CENTRALITY_LABELS[centrality]}`}
                />
              </td>
              {POV_KEYS.map((pov, povIndex) => (
                <Fragment key={pov}>
                  {povIndex === 1 && (
                    <td className="px-1 text-gray-600">|</td>
                  )}
                  {NAMING_KEYS.map((naming) => (
                    <td key={`${centrality}-${pov}-${naming}`} className="px-2 py-1 text-center">
                      <input
                        type="checkbox"
                        checked={isSelected(value, centrality, pov, naming)}
                        onChange={() => toggleCell(centrality, pov, naming)}
                        className="w-4 h-4 rounded border-purple-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800 cursor-pointer"
                      />
                    </td>
                  ))}
                </Fragment>
              ))}
            </tr>
          ))}
          {/* Column select-all row */}
          <tr className="border-t border-purple-700/30">
            <td className="px-2 py-1"></td>
            <td className="px-2 py-1"></td>
            {POV_KEYS.map((pov, povIndex) => (
              <Fragment key={pov}>
                {povIndex === 1 && (
                  <td className="px-1 text-gray-600">|</td>
                )}
                {NAMING_KEYS.map((naming) => (
                  <td key={`col-${pov}-${naming}`} className="px-2 py-1 text-center">
                    <input
                      type="checkbox"
                      checked={areAllSelected(getColumnCombinations(pov, naming))}
                      onChange={() => toggleGroup(getColumnCombinations(pov, naming))}
                      className={selectAllCheckboxClass}
                      title={`Select all ${pov} ${naming}`}
                    />
                  </td>
                ))}
              </Fragment>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}

// Multi-select Platforms Component
function PlatformSelect({
  value,
  onChange,
  availablePlatforms,
}: {
  value: Platform[];
  onChange: (platforms: Platform[]) => void;
  availablePlatforms: Platform[];
}) {
  const [isOpen, setIsOpen] = useState(false);

  const togglePlatform = (platform: Platform) => {
    if (value.includes(platform)) {
      onChange(value.filter((p) => p !== platform));
    } else {
      onChange([...value, platform]);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-2 py-1.5 bg-gray-700 border border-purple-700/50 rounded text-left text-sm text-gray-300 hover:border-purple-600 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 flex items-center justify-between"
      >
        <span className={value.length === 0 ? 'text-gray-500' : ''}>
          {value.length === 0 ? 'All platforms' : `${value.length} selected`}
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-purple-700/50 rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto">
            {availablePlatforms.map((platform) => (
              <label
                key={platform}
                className="flex items-center px-3 py-2 hover:bg-purple-900/30 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={value.includes(platform)}
                  onChange={() => togglePlatform(platform)}
                  className="w-4 h-4 rounded border-purple-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800 mr-2"
                />
                <span className="text-sm text-gray-300">{PLATFORM_INFO[platform].name}</span>
              </label>
            ))}
          </div>
        </>
      )}

      {value.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {value.map((platform) => (
            <span
              key={platform}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-900/50 border border-purple-700/50 rounded text-xs text-purple-300"
            >
              {PLATFORM_INFO[platform].name}
              <button
                type="button"
                onClick={() => togglePlatform(platform)}
                className="hover:text-purple-100"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// Multi-select Genres Component
function GenreSelect({
  value,
  onChange,
  availableGenres,
}: {
  value: string[];
  onChange: (genres: string[]) => void;
  availableGenres: string[];
}) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleGenre = (genre: string) => {
    if (value.includes(genre)) {
      onChange(value.filter((g) => g !== genre));
    } else {
      onChange([...value, genre]);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 bg-gray-700 border border-purple-700/50 rounded-lg text-left text-sm text-gray-300 hover:border-purple-600 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 flex items-center justify-between"
      >
        <span className={value.length === 0 ? 'text-gray-500' : ''}>
          {value.length === 0 ? 'Select genres...' : `${value.length} selected`}
        </span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-purple-700/50 rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto">
            {availableGenres.map((genre) => (
              <label
                key={genre}
                className="flex items-center px-3 py-2 hover:bg-purple-900/30 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={value.includes(genre)}
                  onChange={() => toggleGenre(genre)}
                  className="w-4 h-4 rounded border-purple-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800 mr-2"
                />
                <span className="text-sm text-gray-300">{genre}</span>
              </label>
            ))}
          </div>
        </>
      )}

      {value.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {value.map((genre) => (
            <span
              key={genre}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-900/50 border border-purple-700/50 rounded text-xs text-purple-300"
            >
              {genre}
              <button
                type="button"
                onClick={() => toggleGenre(genre)}
                className="hover:text-purple-100"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// Date Range Input Component
function DateRangeInput({
  label,
  fromValue,
  toValue,
  onFromChange,
  onToChange,
}: {
  label: string;
  fromValue: string;
  toValue: string;
  onFromChange: (value: string) => void;
  onToChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm text-gray-400 mb-1">{label}</label>
      <div className="flex gap-2 items-center">
        <input
          type="date"
          value={fromValue}
          onChange={(e) => onFromChange(e.target.value)}
          className="flex-1 px-2 py-1.5 bg-gray-700 border border-purple-700/50 rounded text-sm text-gray-300 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
        />
        <span className="text-gray-500 text-sm">to</span>
        <input
          type="date"
          value={toValue}
          onChange={(e) => onToChange(e.target.value)}
          className="flex-1 px-2 py-1.5 bg-gray-700 border border-purple-700/50 rounded text-sm text-gray-300 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
        />
      </div>
    </div>
  );
}

// Price Range Input Component
function PriceRangeInput({
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
}: {
  minValue: string;
  maxValue: string;
  onMinChange: (value: string) => void;
  onMaxChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm text-gray-400 mb-1">Price (USD)</label>
      <div className="flex gap-2 items-center">
        <div className="flex-1 relative">
          <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 text-sm">$</span>
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Min"
            value={minValue}
            onChange={(e) => onMinChange(e.target.value)}
            className="w-full pl-5 pr-2 py-1.5 bg-gray-700 border border-purple-700/50 rounded text-sm text-gray-300 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
          />
        </div>
        <span className="text-gray-500 text-sm">to</span>
        <div className="flex-1 relative">
          <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 text-sm">$</span>
          <input
            type="number"
            min="0"
            step="0.01"
            placeholder="Max"
            value={maxValue}
            onChange={(e) => onMaxChange(e.target.value)}
            className="w-full pl-5 pr-2 py-1.5 bg-gray-700 border border-purple-700/50 rounded text-sm text-gray-300 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
          />
        </div>
      </div>
    </div>
  );
}

// Main FilterPanel Component
export default function FilterPanel({
  filters,
  onChange,
  availableGenres,
  availablePlatforms,
  onClear,
  matchingCount,
  totalCount,
  mode,
}: FilterPanelProps) {
  const isBlood = mode === 'blood';
  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    onChange({ ...filters, [key]: value });
  };

  // Check for active taxonomy filters based on mode
  const hasTaxonomyFilters = isBlood
    ? filters.vampirism.length < 4 || filters.hemomancy.length < 5 || filters.bloodPov.length < 2
    : filters.necromancyGrid.length < 16;

  const hasActiveFilters =
    filters.genres.length > 0 ||
    filters.platforms.length > 0 ||
    filters.announcementDateFrom ||
    filters.announcementDateTo ||
    filters.lastUpdatedFrom ||
    filters.lastUpdatedTo ||
    filters.priceMin ||
    filters.priceMax ||
    !filters.includeEarlyAccess ||
    !filters.includeUnreleased ||
    filters.availability.length < 3 || // Less than all 3 = filter active
    hasTaxonomyFilters;

  return (
    <div className={`mt-4 p-4 bg-gray-800/70 border rounded-lg transition-colors duration-300 ${
      isBlood ? 'border-red-700/30' : 'border-purple-700/30'
    }`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-sm font-semibold transition-colors duration-300 ${
          isBlood ? 'text-red-300' : 'text-purple-300'
        }`}>Advanced Filters</h3>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">
            {matchingCount} of {totalCount} games
          </span>
          {hasActiveFilters && (
            <button
              type="button"
              onClick={onClear}
              className={`text-xs text-gray-400 transition-colors ${
                isBlood ? 'hover:text-red-300' : 'hover:text-purple-300'
              }`}
            >
              Clear all
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Genres/Tags */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">Genres/Tags</label>
          <GenreSelect
            value={filters.genres}
            onChange={(genres) => updateFilter('genres', genres)}
            availableGenres={availableGenres}
          />
        </div>

        {/* Date Ranges */}
        <DateRangeInput
          label="News"
          fromValue={filters.announcementDateFrom}
          toValue={filters.announcementDateTo}
          onFromChange={(v) => updateFilter('announcementDateFrom', v)}
          onToChange={(v) => updateFilter('announcementDateTo', v)}
        />

        <DateRangeInput
          label="Updates/Patches"
          fromValue={filters.lastUpdatedFrom}
          toValue={filters.lastUpdatedTo}
          onFromChange={(v) => updateFilter('lastUpdatedFrom', v)}
          onToChange={(v) => updateFilter('lastUpdatedTo', v)}
        />

        {/* Price Range */}
        <PriceRangeInput
          minValue={filters.priceMin}
          maxValue={filters.priceMax}
          onMinChange={(v) => updateFilter('priceMin', v)}
          onMaxChange={(v) => updateFilter('priceMax', v)}
        />

        {/* Platforms */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">Platforms</label>
          <PlatformSelect
            value={filters.platforms}
            onChange={(platforms) => updateFilter('platforms', platforms)}
            availablePlatforms={availablePlatforms}
          />
        </div>

        {/* Early Access & Unreleased Toggles */}
        <div className="flex gap-6">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Early Access</label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => updateFilter('includeEarlyAccess', !filters.includeEarlyAccess)}
                className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500/20 ${
                  filters.includeEarlyAccess ? 'bg-purple-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform ${
                    filters.includeEarlyAccess ? 'translate-x-7' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className="text-sm text-gray-400">
                {filters.includeEarlyAccess ? 'Included' : 'Excluded'}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Unreleased</label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => updateFilter('includeUnreleased', !filters.includeUnreleased)}
                className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500/20 ${
                  filters.includeUnreleased ? 'bg-purple-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform ${
                    filters.includeUnreleased ? 'translate-x-7' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className="text-sm text-gray-400">
                {filters.includeUnreleased ? 'Included' : 'Excluded'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Availability & Taxonomy Row */}
      <div className={`mt-4 pt-4 border-t flex flex-col md:flex-row gap-6 transition-colors duration-300 ${
        isBlood ? 'border-red-700/30' : 'border-purple-700/30'
      }`}>
        {/* Availability */}
        <div className="flex-shrink-0">
          <label className="block text-sm text-gray-400 mb-2">Availability</label>
          <AvailabilityCheckboxes
            value={filters.availability}
            onChange={(availability) => updateFilter('availability', availability)}
          />
          {filters.availability.length < 3 && (
            <p className="text-xs text-gray-500 mt-2">
              {filters.availability.length} of 3 selected
            </p>
          )}
        </div>

        {/* Mode-specific taxonomy filters */}
        {isBlood ? (
          // Blood mode: Vampirism, Hemomancy, POV checkboxes
          <div className="flex-grow flex flex-col md:flex-row gap-6">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Vampirism</label>
              <VampirismCheckboxes
                value={filters.vampirism}
                onChange={(vampirism) => updateFilter('vampirism', vampirism)}
              />
              {filters.vampirism.length < 4 && (
                <p className="text-xs text-gray-500 mt-2">
                  {filters.vampirism.length} of 4 selected
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Blood</label>
              <HemomancyCheckboxes
                value={filters.hemomancy}
                onChange={(hemomancy) => updateFilter('hemomancy', hemomancy)}
              />
              {filters.hemomancy.length < 5 && (
                <p className="text-xs text-gray-500 mt-2">
                  {filters.hemomancy.length} of 5 selected
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">POV</label>
              <BloodPovCheckboxes
                value={filters.bloodPov}
                onChange={(pov) => updateFilter('bloodPov', pov)}
              />
              {filters.bloodPov.length < 2 && (
                <p className="text-xs text-gray-500 mt-2">
                  {filters.bloodPov.length} of 2 selected
                </p>
              )}
            </div>
          </div>
        ) : (
          // Necromancy mode: Original grid
          <div className="flex-grow">
            <label className="block text-sm text-gray-400 mb-2">Degree of Necromancy</label>
            <NecromancyGrid
              value={filters.necromancyGrid}
              onChange={(grid) => updateFilter('necromancyGrid', grid)}
            />
            {filters.necromancyGrid.length < 16 && (
              <p className="text-xs text-gray-500 mt-2">
                {filters.necromancyGrid.length} of 16 combinations selected
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Helper function to count active filters (for badge)
export function countActiveFilters(filters: FilterState): number {
  let count = 0;
  if (filters.genres.length > 0) count++;
  if (filters.platforms.length > 0) count++;
  if (filters.announcementDateFrom || filters.announcementDateTo) count++;
  if (filters.lastUpdatedFrom || filters.lastUpdatedTo) count++;
  if (filters.priceMin || filters.priceMax) count++;
  if (!filters.includeEarlyAccess) count++;
  if (!filters.includeUnreleased) count++;
  if (filters.availability.length < 3) count++; // Only count if some are deselected
  if (filters.necromancyGrid.length < 16) count++; // Only count if some are deselected
  return count;
}
