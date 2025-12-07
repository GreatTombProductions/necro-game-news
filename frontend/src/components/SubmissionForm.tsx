import { useState } from 'react';

interface SubmissionFormProps {
  isOpen: boolean;
  onClose: () => void;
}

type SubmissionType = 'addition' | 'revision';
type SubmitterType = 'player' | 'developer';
type Centrality = '' | 'a' | 'b' | 'c' | 'd';
type POV = '' | 'character' | 'unit';
type Naming = '' | 'explicit' | 'implied';

interface FormData {
  gameName: string;
  steamId: string;
  submissionType: SubmissionType;
  submitterType: SubmitterType;
  centrality: Centrality;
  pov: POV;
  naming: Naming;
  notes: string;
  contact: string;
}

const CENTRALITY_OPTIONS = [
  { value: 'a', label: 'Core', description: 'Necromancy is central to gameplay' },
  { value: 'b', label: 'Dedicated Spec', description: 'Cohesive necromantic specialization available' },
  { value: 'c', label: 'Isolated', description: 'Some necromantic features exist, but scattered' },
  { value: 'd', label: 'Minimal', description: 'Necromancy by technicality or lore only' },
];

const POV_OPTIONS = [
  { value: 'character', label: 'Character', description: 'Play AS the necromancer (who may control others / a faction)' },
  { value: 'unit', label: 'Unit', description: 'Control necromancers / necromancy faction' },
];

const NAMING_OPTIONS = [
  { value: 'explicit', label: 'Explicit', description: '"Necromancer" or variant used' },
  { value: 'implied', label: 'Implied', description: 'Necromancy not named explicitly' },
];

export default function SubmissionForm({ isOpen, onClose }: SubmissionFormProps) {
  const [formData, setFormData] = useState<FormData>({
    gameName: '',
    steamId: '',
    submissionType: 'addition',
    submitterType: 'player',
    centrality: '',
    pov: '',
    naming: '',
    notes: '',
    contact: '',
  });
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
    setFormData({
      gameName: '',
      steamId: '',
      submissionType: 'addition',
      submitterType: 'player',
      centrality: '',
      pov: '',
      naming: '',
      notes: '',
      contact: '',
    });
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
      <div className="relative bg-gray-900 border border-purple-700/50 rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gray-900 border-b border-purple-700/30 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-purple-200">
            {submitted ? 'Submission Received' : 'Submit a Game'}
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-purple-300 transition-colors p-1"
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
              <div className="text-5xl mb-4">&#128128;</div>
              <p className="text-gray-300 mb-2">Thanks for your submission!</p>
              <p className="text-sm text-gray-500">We'll review it and add it to our crypt if it qualifies.</p>
              <button
                onClick={handleClose}
                className="mt-6 px-6 py-2 bg-purple-700 hover:bg-purple-600 text-white rounded-lg transition-colors"
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
                  <label className="block text-sm font-medium text-purple-300 mb-1">
                    Game Name
                  </label>
                  <input
                    type="text"
                    value={formData.gameName}
                    onChange={(e) => setFormData({ ...formData, gameName: e.target.value })}
                    placeholder="e.g., Necromancer's Revenge"
                    className="w-full px-3 py-2 bg-gray-800 border border-purple-700/50 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-purple-300 mb-1">
                    Steam App ID
                  </label>
                  <input
                    type="text"
                    value={formData.steamId}
                    onChange={(e) => setFormData({ ...formData, steamId: e.target.value })}
                    placeholder="e.g., 1234567"
                    className="w-full px-3 py-2 bg-gray-800 border border-purple-700/50 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30"
                  />
                  <p className="text-xs text-gray-500 mt-1">At least one of the above is required</p>
                </div>
              </div>

              {/* Submission type */}
              <div>
                <label className="block text-sm font-medium text-purple-300 mb-2">
                  What are you submitting?
                </label>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, submissionType: 'addition' })}
                    className={`flex-1 px-4 py-2 rounded-lg border transition-colors text-sm ${
                      formData.submissionType === 'addition'
                        ? 'bg-purple-700 border-purple-500 text-white'
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
                        ? 'bg-purple-700 border-purple-500 text-white'
                        : 'bg-gray-800 border-purple-700/50 text-gray-300 hover:border-purple-500'
                    }`}
                  >
                    Correction
                  </button>
                </div>
              </div>

              {/* Submitter type */}
              <div>
                <label className="block text-sm font-medium text-purple-300 mb-2">
                  Who are you?
                </label>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, submitterType: 'player' })}
                    className={`flex-1 px-4 py-2 rounded-lg border transition-colors text-sm ${
                      formData.submitterType === 'player'
                        ? 'bg-purple-700 border-purple-500 text-white'
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
                        ? 'bg-purple-700 border-purple-500 text-white'
                        : 'bg-gray-800 border-purple-700/50 text-gray-300 hover:border-purple-500'
                    }`}
                  >
                    Developer
                  </button>
                </div>
              </div>

              {/* Taxonomy section */}
              <div className="border-t border-purple-700/30 pt-4">
                <p className="text-sm text-gray-400 mb-3">
                  How would you categorize this game? <span className="text-gray-500">(optional)</span>
                </p>

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
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-purple-300 mb-1">
                  Notes / Justification <span className="text-gray-500 font-normal">(optional)</span>
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Tell us why this game belongs here, or what needs correcting..."
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-800 border border-purple-700/50 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 resize-none"
                />
              </div>

              {/* Contact */}
              <div>
                <label className="block text-sm font-medium text-purple-300 mb-1">
                  Contact <span className="text-gray-500 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={formData.contact}
                  onChange={(e) => setFormData({ ...formData, contact: e.target.value })}
                  placeholder="Discord, email, Twitter, etc."
                  className="w-full px-3 py-2 bg-gray-800 border border-purple-700/50 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30"
                />
                <p className="text-xs text-gray-500 mt-1">In case we have questions about your submission</p>
              </div>

              {/* Submit button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-3 bg-purple-700 hover:bg-purple-600 disabled:bg-purple-700/50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
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