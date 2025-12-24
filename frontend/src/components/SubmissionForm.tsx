import { useState } from 'react';
import type { RegistryMode } from '../types';

interface SubmissionFormProps {
  isOpen: boolean;
  onClose: () => void;
  mode: RegistryMode;
}

type SubmissionType = 'addition' | 'revision';
type SubmitterType = 'player' | 'developer';
type Centrality = '' | 'a' | 'b' | 'c' | 'd';
type POV = '' | 'character' | 'unit';
type Naming = '' | 'explicit' | 'implied';
type Availability = '' | 'instant' | 'gated';

// Blood registry types
type Vampirism = '' | 'outright' | 'implied' | 'channeled' | 'absent';
type Hemomancy = '' | 'a' | 'b' | 'c' | 'd' | 'absent';

interface FormData {
  gameName: string;
  steamId: string;
  submissionType: SubmissionType;
  submitterType: SubmitterType;
  availability: Availability;
  // Necromancy-specific
  centrality: Centrality;
  pov: POV;
  naming: Naming;
  // Blood-specific
  vampirism: Vampirism;
  hemomancy: Hemomancy;
  // Shared
  notes: string;
  contact: string;
  registry: RegistryMode;
}

const CENTRALITY_OPTIONS = [
  { value: 'a', label: 'Core', description: 'Necromancy is central to gameplay and identity' },
  { value: 'b', label: 'Dedicated Branch', description: 'Cohesive group of necromantic features available' },
  { value: 'c', label: 'Isolated', description: 'Some necromantic features exist, but scattered' },
  { value: 'd', label: 'Minimal', description: 'Necromancy by technicality or lore only' },
];

const POV_OPTIONS = [
  { value: 'character', label: 'Character', description: 'Play AS the necromancer (who may control others / a faction)' },
  { value: 'unit', label: 'Unit', description: 'Control necromancers / necromancy faction' },
];

const BLOOD_POV_OPTIONS = [
  { value: 'character', label: 'Character', description: 'Play AS the vampire/blood mage' },
  { value: 'unit', label: 'Unit', description: 'Control vampire/blood mage units but not as them directly' },
];

const NAMING_OPTIONS = [
  { value: 'explicit', label: 'Explicit', description: '"Necromancer" or variant used' },
  { value: 'implied', label: 'Implied', description: 'Necromancy not named explicitly' },
];

const AVAILABILITY_OPTIONS = [
  { value: 'instant', label: 'Instant', description: 'Always available immediately from the start' },
  { value: 'gated', label: 'Gated', description: 'Takes time or progression to unlock, or not deterministically available' },
];

// Blood registry options
const VAMPIRISM_OPTIONS = [
  { value: 'outright', label: 'Outright', description: 'Character is a vampire, dhampir, or vampirically transformed' },
  { value: 'implied', label: 'Implied', description: 'Vampire-like characteristics without explicit identification' },
  { value: 'channeled', label: 'Channeled', description: 'Wields vampiric powers without being vampiric' },
  { value: 'absent', label: 'Absent', description: 'No vampiric connection (blood mage only)' },
];

const HEMOMANCY_OPTIONS = [
  { value: 'a', label: 'Core', description: 'Blood magic is central to gameplay and identity' },
  { value: 'b', label: 'Dedicated Branch', description: 'Cohesive blood magic skill tree or ability set' },
  { value: 'c', label: 'Isolated', description: 'Blood magic abilities exist but not grouped cohesively' },
  { value: 'd', label: 'Minimal', description: 'Blood magic technically present with minimal impact' },
  { value: 'absent', label: 'Absent', description: 'No blood magic mechanics' },
];

export default function SubmissionForm({ isOpen, onClose, mode }: SubmissionFormProps) {
  const isBlood = mode === 'blood';

  const getInitialFormData = (): FormData => ({
    gameName: '',
    steamId: '',
    submissionType: 'addition',
    submitterType: 'player',
    availability: '',
    centrality: '',
    pov: '',
    naming: '',
    vampirism: '',
    hemomancy: '',
    notes: '',
    contact: '',
    registry: mode,
  });

  const [formData, setFormData] = useState<FormData>(getInitialFormData);
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation: at least one of name or steam ID required
    if (!formData.gameName.trim() && !formData.steamId.trim()) {
      setError('Please provide either a game name or Steam ID');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || 'Failed to submit');
      }

      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setFormData(getInitialFormData());
    setSubmitted(false);
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className={`relative bg-gray-900 border rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto ${
        isBlood ? 'border-red-700/50' : 'border-purple-700/50'
      }`}>
        {/* Header */}
        <div className={`sticky top-0 bg-gray-900 border-b px-6 py-4 flex items-center justify-between ${
          isBlood ? 'border-red-700/30' : 'border-purple-700/30'
        }`}>
          <h2 className={`text-xl font-semibold ${isBlood ? 'text-red-200' : 'text-purple-200'}`}>
            {submitted ? 'Submission Received' : 'Submit a Game'}
          </h2>
          <button
            onClick={handleClose}
            className={`text-gray-400 transition-colors p-1 ${isBlood ? 'hover:text-red-300' : 'hover:text-purple-300'}`}
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {submitted ? (
            <div className="text-center py-8">
              <div className="text-5xl mb-4">{isBlood ? '🩸' : '💀'}</div>
              <p className="text-gray-300 mb-2">Thanks for your submission!</p>
              <p className="text-sm text-gray-500">
                {isBlood
                  ? "We'll review it and add it to our sanguine archives if it qualifies."
                  : "We'll review it and add it to our crypt if it qualifies."
                }
              </p>
              <button
                onClick={handleClose}
                className={`mt-6 px-6 py-2 text-white rounded-lg transition-colors ${
                  isBlood ? 'bg-red-700 hover:bg-red-600' : 'bg-purple-700 hover:bg-purple-600'
                }`}
              >
                Close
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Error message */}
              {error && (
                <div className="bg-red-900/30 border border-red-700/50 rounded-lg px-4 py-3 text-sm text-red-300">
                  {error}
                </div>
              )}

              {/* Game identification */}
              <div className="space-y-3">
                <div>
                  <label className={`block text-sm font-medium mb-1 ${isBlood ? 'text-red-300' : 'text-purple-300'}`}>
                    Game Name
                  </label>
                  <input
                    type="text"
                    value={formData.gameName}
                    onChange={(e) => setFormData({ ...formData, gameName: e.target.value })}
                    placeholder={isBlood ? "e.g., V Rising" : "e.g., Necromancer's Revenge"}
                    className={`w-full px-3 py-2 bg-gray-800 border rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 ${
                      isBlood
                        ? 'border-red-700/50 focus:border-red-500 focus:ring-red-500/30'
                        : 'border-purple-700/50 focus:border-purple-500 focus:ring-purple-500/30'
                    }`}
                  />
                </div>
                <div>
                  <label className={`block text-sm font-medium mb-1 ${isBlood ? 'text-red-300' : 'text-purple-300'}`}>
                    Steam App ID
                  </label>
                  <input
                    type="text"
                    value={formData.steamId}
                    onChange={(e) => setFormData({ ...formData, steamId: e.target.value })}
                    placeholder="e.g., 1234567"
                    className={`w-full px-3 py-2 bg-gray-800 border rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 ${
                      isBlood
                        ? 'border-red-700/50 focus:border-red-500 focus:ring-red-500/30'
                        : 'border-purple-700/50 focus:border-purple-500 focus:ring-purple-500/30'
                    }`}
                  />
                  <p className="text-xs text-gray-500 mt-1">At least one of the above is required</p>
                </div>
              </div>

              {/* Submission type */}
              <div>
                <label className={`block text-sm font-medium mb-2 ${isBlood ? 'text-red-300' : 'text-purple-300'}`}>
                  What are you submitting?
                </label>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, submissionType: 'addition' })}
                    className={`flex-1 px-4 py-2 rounded-lg border transition-colors text-sm ${
                      formData.submissionType === 'addition'
                        ? isBlood
                          ? 'bg-red-700 border-red-500 text-white'
                          : 'bg-purple-700 border-purple-500 text-white'
                        : isBlood
                          ? 'bg-gray-800 border-red-700/50 text-gray-300 hover:border-red-500'
                          : 'bg-gray-800 border-purple-700/50 text-gray-300 hover:border-purple-500'
                    }`}
                  >
                    New Game
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, submissionType: 'revision' })}
                    className={`flex-1 px-4 py-2 rounded-lg border transition-colors text-sm ${
                      formData.submissionType === 'revision'
                        ? isBlood
                          ? 'bg-red-700 border-red-500 text-white'
                          : 'bg-purple-700 border-purple-500 text-white'
                        : isBlood
                          ? 'bg-gray-800 border-red-700/50 text-gray-300 hover:border-red-500'
                          : 'bg-gray-800 border-purple-700/50 text-gray-300 hover:border-purple-500'
                    }`}
                  >
                    Correction
                  </button>
                </div>
              </div>

              {/* Submitter type */}
              <div>
                <label className={`block text-sm font-medium mb-2 ${isBlood ? 'text-red-300' : 'text-purple-300'}`}>
                  Who are you?
                </label>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, submitterType: 'player' })}
                    className={`flex-1 px-4 py-2 rounded-lg border transition-colors text-sm ${
                      formData.submitterType === 'player'
                        ? isBlood
                          ? 'bg-red-700 border-red-500 text-white'
                          : 'bg-purple-700 border-purple-500 text-white'
                        : isBlood
                          ? 'bg-gray-800 border-red-700/50 text-gray-300 hover:border-red-500'
                          : 'bg-gray-800 border-purple-700/50 text-gray-300 hover:border-purple-500'
                    }`}
                  >
                    Player
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, submitterType: 'developer' })}
                    className={`flex-1 px-4 py-2 rounded-lg border transition-colors text-sm ${
                      formData.submitterType === 'developer'
                        ? isBlood
                          ? 'bg-red-700 border-red-500 text-white'
                          : 'bg-purple-700 border-purple-500 text-white'
                        : isBlood
                          ? 'bg-gray-800 border-red-700/50 text-gray-300 hover:border-red-500'
                          : 'bg-gray-800 border-purple-700/50 text-gray-300 hover:border-purple-500'
                    }`}
                  >
                    Developer
                  </button>
                </div>
              </div>

              {/* Availability section */}
              <div className={`border-t pt-4 ${isBlood ? 'border-red-700/30' : 'border-purple-700/30'}`}>
                <label className={`block text-sm font-medium mb-2 ${isBlood ? 'text-red-300' : 'text-purple-300'}`}>
                  {isBlood
                    ? 'When is vampirism/blood magic available?'
                    : 'When is necromancy available?'
                  } <span className="text-gray-500 font-normal">(optional)</span>
                </label>
                <select
                  value={formData.availability}
                  onChange={(e) => setFormData({ ...formData, availability: e.target.value as Availability })}
                  className={`w-full px-3 py-2 bg-gray-800 border rounded-lg text-gray-200 focus:outline-none focus:ring-1 text-sm ${
                    isBlood
                      ? 'border-red-700/50 focus:border-red-500 focus:ring-red-500/30'
                      : 'border-purple-700/50 focus:border-purple-500 focus:ring-purple-500/30'
                  }`}
                >
                  <option value="">Not sure / Skip</option>
                  {AVAILABILITY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label} — {opt.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Taxonomy section */}
              <div className={`border-t pt-4 ${isBlood ? 'border-red-700/30' : 'border-purple-700/30'}`}>
                <p className="text-sm text-gray-400 mb-3">
                  How would you categorize this game? <span className="text-gray-500">(optional)</span>
                </p>

                {isBlood ? (
                  <>
                    {/* Vampirism */}
                    <div className="mb-3">
                      <label className="block text-xs font-medium text-red-400 mb-1.5">
                        Vampirism
                      </label>
                      <select
                        value={formData.vampirism}
                        onChange={(e) => setFormData({ ...formData, vampirism: e.target.value as Vampirism })}
                        className="w-full px-3 py-2 bg-gray-800 border border-red-700/50 rounded-lg text-gray-200 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30 text-sm"
                      >
                        <option value="">Not sure / Skip</option>
                        {VAMPIRISM_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label} — {opt.description}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Hemomancy */}
                    <div className="mb-3">
                      <label className="block text-xs font-medium text-red-400 mb-1.5">
                        Blood Magic Centrality
                      </label>
                      <select
                        value={formData.hemomancy}
                        onChange={(e) => setFormData({ ...formData, hemomancy: e.target.value as Hemomancy })}
                        className="w-full px-3 py-2 bg-gray-800 border border-red-700/50 rounded-lg text-gray-200 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30 text-sm"
                      >
                        <option value="">Not sure / Skip</option>
                        {HEMOMANCY_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label} — {opt.description}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* POV (blood mode) */}
                    <div>
                      <label className="block text-xs font-medium text-red-400 mb-1.5">
                        Point of View
                      </label>
                      <select
                        value={formData.pov}
                        onChange={(e) => setFormData({ ...formData, pov: e.target.value as POV })}
                        className="w-full px-3 py-2 bg-gray-800 border border-red-700/50 rounded-lg text-gray-200 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30 text-sm"
                      >
                        <option value="">Not sure / Skip</option>
                        {BLOOD_POV_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label} — {opt.description}
                          </option>
                        ))}
                      </select>
                    </div>
                  </>
                ) : (
                  <>
                    {/* Centrality */}
                    <div className="mb-3">
                      <label className="block text-xs font-medium text-purple-400 mb-1.5">
                        Centrality of Necromancy
                      </label>
                      <select
                        value={formData.centrality}
                        onChange={(e) => setFormData({ ...formData, centrality: e.target.value as Centrality })}
                        className="w-full px-3 py-2 bg-gray-800 border border-purple-700/50 rounded-lg text-gray-200 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 text-sm"
                      >
                        <option value="">Not sure / Skip</option>
                        {CENTRALITY_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label} — {opt.description}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* POV */}
                    <div className="mb-3">
                      <label className="block text-xs font-medium text-purple-400 mb-1.5">
                        Point of View
                      </label>
                      <select
                        value={formData.pov}
                        onChange={(e) => setFormData({ ...formData, pov: e.target.value as POV })}
                        className="w-full px-3 py-2 bg-gray-800 border border-purple-700/50 rounded-lg text-gray-200 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 text-sm"
                      >
                        <option value="">Not sure / Skip</option>
                        {POV_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label} — {opt.description}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Naming */}
                    <div>
                      <label className="block text-xs font-medium text-purple-400 mb-1.5">
                        Naming
                      </label>
                      <select
                        value={formData.naming}
                        onChange={(e) => setFormData({ ...formData, naming: e.target.value as Naming })}
                        className="w-full px-3 py-2 bg-gray-800 border border-purple-700/50 rounded-lg text-gray-200 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 text-sm"
                      >
                        <option value="">Not sure / Skip</option>
                        {NAMING_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label} — {opt.description}
                          </option>
                        ))}
                      </select>
                    </div>
                  </>
                )}
              </div>

              {/* Notes */}
              <div>
                <label className={`block text-sm font-medium mb-1 ${isBlood ? 'text-red-300' : 'text-purple-300'}`}>
                  Notes / Justification <span className="text-gray-500 font-normal">(optional)</span>
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Tell us why this game belongs here, or what needs correcting..."
                  rows={3}
                  className={`w-full px-3 py-2 bg-gray-800 border rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 resize-none ${
                    isBlood
                      ? 'border-red-700/50 focus:border-red-500 focus:ring-red-500/30'
                      : 'border-purple-700/50 focus:border-purple-500 focus:ring-purple-500/30'
                  }`}
                />
              </div>

              {/* Contact */}
              <div>
                <label className={`block text-sm font-medium mb-1 ${isBlood ? 'text-red-300' : 'text-purple-300'}`}>
                  Contact <span className="text-gray-500 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={formData.contact}
                  onChange={(e) => setFormData({ ...formData, contact: e.target.value })}
                  placeholder="Discord, email, Twitter, etc."
                  className={`w-full px-3 py-2 bg-gray-800 border rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 ${
                    isBlood
                      ? 'border-red-700/50 focus:border-red-500 focus:ring-red-500/30'
                      : 'border-purple-700/50 focus:border-purple-500 focus:ring-purple-500/30'
                  }`}
                />
                <p className="text-xs text-gray-500 mt-1">In case we have questions about your submission</p>
              </div>

              {/* Submit button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`w-full py-3 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed ${
                    isBlood
                      ? 'bg-red-700 hover:bg-red-600 disabled:bg-red-700/50'
                      : 'bg-purple-700 hover:bg-purple-600 disabled:bg-purple-700/50'
                  }`}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit for Review'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}