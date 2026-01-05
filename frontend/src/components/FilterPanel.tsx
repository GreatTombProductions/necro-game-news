import { Fragment, useState } from 'react';
import type { Platform, RegistryMode, Vampirism, HemomancyCentrality, POV } from '../types';
import { PLATFORM_INFO } from '../types';

// Types
export interface NecromancyFilter {
  centrality: 'a' | 'b' | 'c' | 'd';
  pov: 'character' | 'unit';
  naming: 'explicit' | 'implied';
}

export interface BloodFilter {
  vampirism: Vampirism;
  hemomancy: HemomancyCentrality;
  pov: POV;
}

export type Availability = 'instant' | 'gated' | 'unknown';
export type EarlyAccessFilter = 'early_access' | 'full_release';
export type ReleaseStatusFilter = 'released' | 'unreleased';
export type GameTypeFilter = 'game' | 'mod';

export interface FilterState {
  genres: string[];
  platforms: Platform[];
  announcementDateFrom: string;
  announcementDateTo: string;
  lastUpdatedFrom: string;
  lastUpdatedTo: string;
  priceMin: string;
  priceMax: string;
  earlyAccess: EarlyAccessFilter[];
  releaseStatus: ReleaseStatusFilter[];
  gameType: GameTypeFilter[];
  availability: Availability[];
  necromancyGrid: NecromancyFilter[];
  // Blood registry filters
  bloodGrid: BloodFilter[];
}

// Necromancy dimension keys
const CENTRALITY_KEYS = ['a', 'b', 'c', 'd'] as const;
const POV_KEYS = ['character', 'unit'] as const;
const NAMING_KEYS = ['explicit', 'implied'] as const;
const AVAILABILITY_KEYS: Availability[] = ['instant', 'gated', 'unknown'];
const EARLY_ACCESS_KEYS: EarlyAccessFilter[] = ['early_access', 'full_release'];
const RELEASE_STATUS_KEYS: ReleaseStatusFilter[] = ['released', 'unreleased'];
const GAME_TYPE_KEYS: GameTypeFilter[] = ['game', 'mod'];

const GAME_TYPE_LABELS: Record<GameTypeFilter, string> = {
  game: 'Games',
  mod: 'Mods (full conversion / expansive)',
};

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

// Generate all 40 blood combinations (4 vampirism × 5 hemomancy × 2 pov)
export function getAllBloodCombinations(): BloodFilter[] {
  const combinations: BloodFilter[] = [];
  for (const vampirism of VAMPIRISM_KEYS) {
    for (const hemomancy of HEMOMANCY_KEYS) {
      for (const pov of BLOOD_POV_KEYS) {
        combinations.push({ vampirism, hemomancy, pov });
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
  earlyAccess: [...EARLY_ACCESS_KEYS],
  releaseStatus: ['released'], // Default to showing only released games
  gameType: [...GAME_TYPE_KEYS], // Both games and mods checked by default
  availability: [...AVAILABILITY_KEYS],
  necromancyGrid: getAllNecromancyCombinations(),
  // Blood filters - all selected by default
  bloodGrid: getAllBloodCombinations(),
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

// Early Access labels
const EARLY_ACCESS_LABELS: Record<EarlyAccessFilter, string> = {
  early_access: 'Early Access',
  full_release: 'Full Release',
};

// Release Status labels
const RELEASE_STATUS_LABELS: Record<ReleaseStatusFilter, string> = {
  released: 'Released',
  unreleased: 'Unreleased',
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

// Helper to check if a necromancy combination is selected
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

// Helper to check if a blood combination is selected
function isBloodSelected(
  grid: BloodFilter[],
  vampirism: Vampirism,
  hemomancy: HemomancyCentrality,
  pov: POV
): boolean {
  return grid.some(
    (f) => f.vampirism === vampirism && f.hemomancy === hemomancy && f.pov === pov
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

// Early Access Checkboxes Component
function EarlyAccessCheckboxes({
  value,
  onChange,
}: {
  value: EarlyAccessFilter[];
  onChange: (earlyAccess: EarlyAccessFilter[]) => void;
}) {
  const toggleEarlyAccess = (ea: EarlyAccessFilter) => {
    if (value.includes(ea)) {
      onChange(value.filter((a) => a !== ea));
    } else {
      onChange([...value, ea]);
    }
  };

  const selectAll = () => onChange([...EARLY_ACCESS_KEYS]);
  const deselectAll = () => onChange([]);
  const allSelected = value.length === EARLY_ACCESS_KEYS.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        {EARLY_ACCESS_KEYS.map((ea) => (
          <label
            key={ea}
            className="flex items-center gap-1.5 cursor-pointer text-sm"
          >
            <input
              type="checkbox"
              checked={value.includes(ea)}
              onChange={() => toggleEarlyAccess(ea)}
              className="w-4 h-4 rounded border-purple-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800 cursor-pointer"
            />
            <span className="text-gray-300">{EARLY_ACCESS_LABELS[ea]}</span>
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

// Release Status Checkboxes Component
function ReleaseStatusCheckboxes({
  value,
  onChange,
}: {
  value: ReleaseStatusFilter[];
  onChange: (releaseStatus: ReleaseStatusFilter[]) => void;
}) {
  const toggleReleaseStatus = (rs: ReleaseStatusFilter) => {
    if (value.includes(rs)) {
      onChange(value.filter((a) => a !== rs));
    } else {
      onChange([...value, rs]);
    }
  };

  const selectAll = () => onChange([...RELEASE_STATUS_KEYS]);
  const deselectAll = () => onChange([]);
  const allSelected = value.length === RELEASE_STATUS_KEYS.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        {RELEASE_STATUS_KEYS.map((rs) => (
          <label
            key={rs}
            className="flex items-center gap-1.5 cursor-pointer text-sm"
          >
            <input
              type="checkbox"
              checked={value.includes(rs)}
              onChange={() => toggleReleaseStatus(rs)}
              className="w-4 h-4 rounded border-purple-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800 cursor-pointer"
            />
            <span className="text-gray-300">{RELEASE_STATUS_LABELS[rs]}</span>
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

function GameTypeCheckboxes({
  value,
  onChange,
}: {
  value: GameTypeFilter[];
  onChange: (gameType: GameTypeFilter[]) => void;
}) {
  const toggleGameType = (gt: GameTypeFilter) => {
    if (value.includes(gt)) {
      onChange(value.filter((a) => a !== gt));
    } else {
      onChange([...value, gt]);
    }
  };

  const selectAll = () => onChange([...GAME_TYPE_KEYS]);
  const deselectAll = () => onChange([]);
  const allSelected = value.length === GAME_TYPE_KEYS.length;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        {GAME_TYPE_KEYS.map((gt) => (
          <label
            key={gt}
            className="flex items-center gap-1.5 cursor-pointer text-sm"
          >
            <input
              type="checkbox"
              checked={value.includes(gt)}
              onChange={() => toggleGameType(gt)}
              className="w-4 h-4 rounded border-purple-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800 cursor-pointer"
            />
            <span className="text-gray-300">{GAME_TYPE_LABELS[gt]}</span>
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

// Blood Grid Component (4 vampirism × 5 hemomancy × 2 pov)
function BloodGrid({
  value,
  onChange,
}: {
  value: BloodFilter[];
  onChange: (grid: BloodFilter[]) => void;
}) {
  const toggleCell = (vampirism: Vampirism, hemomancy: HemomancyCentrality, pov: POV) => {
    const exists = isBloodSelected(value, vampirism, hemomancy, pov);
    if (exists) {
      onChange(
        value.filter(
          (f) =>
            !(f.vampirism === vampirism && f.hemomancy === hemomancy && f.pov === pov)
        )
      );
    } else {
      onChange([...value, { vampirism, hemomancy, pov }]);
    }
  };

  // Helper to get all combinations for a row (vampirism level)
  const getRowCombinations = (vampirism: Vampirism): BloodFilter[] => {
    const combinations: BloodFilter[] = [];
    for (const hemomancy of HEMOMANCY_KEYS) {
      for (const pov of BLOOD_POV_KEYS) {
        combinations.push({ vampirism, hemomancy, pov });
      }
    }
    return combinations;
  };

  // Helper to get all combinations for a column (hemomancy-pov pair across all vampirism)
  const getColumnCombinations = (hemomancy: HemomancyCentrality, pov: POV): BloodFilter[] => {
    return VAMPIRISM_KEYS.map((vampirism) => ({ vampirism, hemomancy, pov }));
  };

  // Helper to get all combinations for a hemomancy group (both POVs for one hemomancy)
  const getHemomancyCombinations = (hemomancy: HemomancyCentrality): BloodFilter[] => {
    const combinations: BloodFilter[] = [];
    for (const vampirism of VAMPIRISM_KEYS) {
      for (const pov of BLOOD_POV_KEYS) {
        combinations.push({ vampirism, hemomancy, pov });
      }
    }
    return combinations;
  };

  // Check if all combinations in a group are selected
  const areAllSelected = (combinations: BloodFilter[]): boolean => {
    return combinations.every((c) =>
      value.some(
        (v) => v.vampirism === c.vampirism && v.hemomancy === c.hemomancy && v.pov === c.pov
      )
    );
  };

  // Toggle all combinations in a group
  const toggleGroup = (combinations: BloodFilter[]) => {
    const allSelected = areAllSelected(combinations);
    if (allSelected) {
      onChange(
        value.filter(
          (v) =>
            !combinations.some(
              (c) => c.vampirism === v.vampirism && c.hemomancy === v.hemomancy && c.pov === v.pov
            )
        )
      );
    } else {
      const missing = combinations.filter(
        (c) =>
          !value.some(
            (v) => v.vampirism === c.vampirism && v.hemomancy === c.hemomancy && v.pov === c.pov
          )
      );
      onChange([...value, ...missing]);
    }
  };

  const selectAllCheckboxClass = "w-4 h-4 rounded border-red-500 bg-gray-600 text-red-400 focus:ring-red-500 focus:ring-offset-gray-800 cursor-pointer";

  return (
    <div className="overflow-x-auto">
      <table className="text-xs">
        <thead>
          {/* Hemomancy dimension header */}
          <tr>
            <th className="px-2 py-1"></th>
            <th className="px-2 py-1"></th>
            <th colSpan={14} className="px-2 py-1 text-center text-red-400 font-semibold">
              Hemomancy
            </th>
          </tr>
          <tr>
            <th className="px-2 py-1"></th>
            <th className="px-2 py-1"></th>
            {HEMOMANCY_KEYS.map((hemomancy, index) => (
              <Fragment key={hemomancy}>
                {index > 0 && <th className="px-1 text-gray-600">|</th>}
                <th colSpan={2} className="px-2 py-1 text-center border-b border-red-700/30">
                  <label className="flex items-center justify-center gap-1.5 cursor-pointer text-red-300">
                    <input
                      type="checkbox"
                      checked={areAllSelected(getHemomancyCombinations(hemomancy))}
                      onChange={() => toggleGroup(getHemomancyCombinations(hemomancy))}
                      className={selectAllCheckboxClass}
                    />
                    {HEMOMANCY_LABELS[hemomancy]}
                  </label>
                </th>
              </Fragment>
            ))}
          </tr>
          <tr>
            <th className="px-2 py-1 text-red-400 font-semibold text-left">Vampirism</th>
            <th className="px-2 py-1"></th>
            {HEMOMANCY_KEYS.map((hemomancy, index) => (
              <Fragment key={hemomancy}>
                {index > 0 && <th className="px-1 text-gray-600">|</th>}
                {BLOOD_POV_KEYS.map((pov) => (
                  <th key={`${hemomancy}-${pov}`} className="px-2 py-1 text-center text-gray-400 font-normal">
                    {BLOOD_POV_LABELS[pov]}
                  </th>
                ))}
              </Fragment>
            ))}
          </tr>
        </thead>
        <tbody>
          {VAMPIRISM_KEYS.map((vampirism) => (
            <tr key={vampirism}>
              <td className="px-2 py-1 text-gray-300 font-medium whitespace-nowrap">
                {VAMPIRISM_LABELS[vampirism]}
              </td>
              {/* Row select-all checkbox */}
              <td className="px-2 py-1 text-center">
                <input
                  type="checkbox"
                  checked={areAllSelected(getRowCombinations(vampirism))}
                  onChange={() => toggleGroup(getRowCombinations(vampirism))}
                  className={selectAllCheckboxClass}
                  title={`Select all ${VAMPIRISM_LABELS[vampirism]}`}
                />
              </td>
              {HEMOMANCY_KEYS.map((hemomancy, index) => (
                <Fragment key={hemomancy}>
                  {index > 0 && <td className="px-1 text-gray-600">|</td>}
                  {BLOOD_POV_KEYS.map((pov) => (
                    <td key={`${vampirism}-${hemomancy}-${pov}`} className="px-2 py-1 text-center">
                      <input
                        type="checkbox"
                        checked={isBloodSelected(value, vampirism, hemomancy, pov)}
                        onChange={() => toggleCell(vampirism, hemomancy, pov)}
                        className="w-4 h-4 rounded border-red-600 bg-gray-700 text-red-500 focus:ring-red-500 focus:ring-offset-gray-800 cursor-pointer"
                      />
                    </td>
                  ))}
                </Fragment>
              ))}
            </tr>
          ))}
          {/* Column select-all row */}
          <tr className="border-t border-red-700/30">
            <td className="px-2 py-1"></td>
            <td className="px-2 py-1"></td>
            {HEMOMANCY_KEYS.map((hemomancy, index) => (
              <Fragment key={hemomancy}>
                {index > 0 && <td className="px-1 text-gray-600">|</td>}
                {BLOOD_POV_KEYS.map((pov) => (
                  <td key={`col-${hemomancy}-${pov}`} className="px-2 py-1 text-center">
                    <input
                      type="checkbox"
                      checked={areAllSelected(getColumnCombinations(hemomancy, pov))}
                      onChange={() => toggleGroup(getColumnCombinations(hemomancy, pov))}
                      className={selectAllCheckboxClass}
                      title={`Select all ${HEMOMANCY_LABELS[hemomancy]} ${pov}`}
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
    ? filters.bloodGrid.length < 40 // 4 vampirism × 5 hemomancy × 2 pov = 40
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
    filters.earlyAccess.length < 2 || // Less than all 2 = filter active
    filters.releaseStatus.length < 2 || // Less than all 2 = filter active
    filters.gameType.length < 2 || // Less than all 2 = filter active
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

        {/* Early Access */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">Early Access</label>
          <EarlyAccessCheckboxes
            value={filters.earlyAccess}
            onChange={(earlyAccess) => updateFilter('earlyAccess', earlyAccess)}
          />
          {filters.earlyAccess.length < 2 && (
            <p className="text-xs text-gray-500 mt-2">
              {filters.earlyAccess.length} of 2 selected
            </p>
          )}
        </div>

        {/* Release Status */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">Release Status</label>
          <ReleaseStatusCheckboxes
            value={filters.releaseStatus}
            onChange={(releaseStatus) => updateFilter('releaseStatus', releaseStatus)}
          />
          {filters.releaseStatus.length < 2 && (
            <p className="text-xs text-gray-500 mt-2">
              {filters.releaseStatus.length} of 2 selected
            </p>
          )}
        </div>

        {/* Game Type */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">Game Type</label>
          <GameTypeCheckboxes
            value={filters.gameType}
            onChange={(gameType) => updateFilter('gameType', gameType)}
          />
          {filters.gameType.length < 2 && (
            <p className="text-xs text-gray-500 mt-2">
              {filters.gameType.length} of 2 selected
            </p>
          )}
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
          // Blood mode: Grid
          <div className="flex-grow">
            <label className="block text-sm text-gray-400 mb-2">Degree of Sanguinity</label>
            <BloodGrid
              value={filters.bloodGrid}
              onChange={(grid) => updateFilter('bloodGrid', grid)}
            />
            {filters.bloodGrid.length < 40 && (
              <p className="text-xs text-gray-500 mt-2">
                {filters.bloodGrid.length} of 40 combinations selected
              </p>
            )}
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
  if (filters.earlyAccess.length < 2) count++; // Only count if some are deselected
  if (filters.releaseStatus.length < 2) count++; // Only count if some are deselected
  if (filters.gameType.length < 2) count++; // Only count if some are deselected
  if (filters.availability.length < 3) count++; // Only count if some are deselected
  if (filters.necromancyGrid.length < 16) count++; // Only count if some are deselected
  return count;
}
