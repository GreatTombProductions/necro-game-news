import type { VercelRequest, VercelResponse } from '@vercel/node';

interface SubmissionData {
  gameName: string;
  steamId: string;
  submissionType: 'addition' | 'revision';
  submitterType: 'player' | 'developer';
  centrality: string;
  pov: string;
  naming: string;
  notes: string;
  contact: string;
}

const CENTRALITY_LABELS: Record<string, string> = {
  a: 'Core',
  b: 'Dedicated Spec',
  c: 'Isolated',
  d: 'Minimal',
};

const POV_LABELS: Record<string, string> = {
  character: 'Character',
  unit: 'Unit',
};

const NAMING_LABELS: Record<string, string> = {
  explicit: 'Explicit',
  implied: 'Implied',
};

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Check for webhook URL
  const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
  if (!webhookUrl) {
    console.error('DISCORD_WEBHOOK_URL not configured');
    return res.status(500).json({ error: 'Server configuration error' });
  }

  try {
    const data: SubmissionData = req.body;

    // Validate: at least one of gameName or steamId required
    if (!data.gameName?.trim() && !data.steamId?.trim()) {
      return res.status(400).json({ error: 'Game name or Steam ID is required' });
    }

    // Build Discord embed
    const embed = buildDiscordEmbed(data);

    // Send to Discord
    const discordResponse = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: 'Necro Game News',
        avatar_url: 'https://necrotic-realms.vercel.app/favicon.ico',
        embeds: [embed],
      }),
    });

    if (!discordResponse.ok) {
      console.error('Discord webhook failed:', await discordResponse.text());
      return res.status(500).json({ error: 'Failed to submit' });
    }

    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Submission error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

function buildDiscordEmbed(data: SubmissionData) {
  const isAddition = data.submissionType === 'addition';
  const isDeveloper = data.submitterType === 'developer';

  // Title and color
  const title = isAddition ? 'New Game Submission' : 'Correction Submission';
  const color = isAddition ? 0x9333ea : 0xf59e0b; // Purple for new, amber for correction

  // Build fields
  const fields: Array<{ name: string; value: string; inline?: boolean }> = [];

  // Game identification
  if (data.gameName) {
    fields.push({ name: 'Game Name', value: data.gameName, inline: true });
  }
  if (data.steamId) {
    const steamUrl = `https://store.steampowered.com/app/${data.steamId}`;
    fields.push({ name: 'Steam ID', value: `[${data.steamId}](${steamUrl})`, inline: true });
  }

  // Submitter type
  fields.push({
    name: 'Submitted By',
    value: isDeveloper ? 'Developer' : 'Player',
    inline: true,
  });

  // Taxonomy (if provided)
  const taxonomy: string[] = [];
  if (data.centrality) taxonomy.push(`Centrality: **${CENTRALITY_LABELS[data.centrality] || data.centrality}**`);
  if (data.pov) taxonomy.push(`POV: **${POV_LABELS[data.pov] || data.pov}**`);
  if (data.naming) taxonomy.push(`Naming: **${NAMING_LABELS[data.naming] || data.naming}**`);

  if (taxonomy.length > 0) {
    fields.push({ name: 'Suggested Classification', value: taxonomy.join('\n') });
  }

  // Notes
  if (data.notes?.trim()) {
    fields.push({ name: 'Notes', value: data.notes.slice(0, 1024) }); // Discord limit
  }

  // Contact
  if (data.contact?.trim()) {
    fields.push({ name: 'Contact', value: data.contact.slice(0, 256) });
  }

  return {
    title,
    color,
    fields,
    timestamp: new Date().toISOString(),
    footer: {
      text: 'Necro Game News Submission',
    },
  };
}