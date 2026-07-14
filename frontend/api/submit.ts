import type { VercelRequest, VercelResponse } from '@vercel/node';
import * as admin from 'firebase-admin';

type RegistryMode = 'necromancy' | 'blood';

interface SubmissionData {
  gameName: string;
  steamId: string;
  submissionType: 'addition' | 'revision';
  submitterType: 'player' | 'developer';
  availability: string;
  // Necromancy-specific
  centrality: string;
  pov: string;
  naming: string;
  // Blood-specific
  vampirism: string;
  hemomancy: string;
  // Shared
  notes: string;
  contact: string;
  registry: RegistryMode;
}

// Initialize Firebase Admin at module scope.
// Uses the existing greattomb-agent-registry project; credentials from Vercel env vars.
if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.cert({
      projectId: process.env.FIREBASE_PROJECT_ID,
      clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
      privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
    }),
  });
}
const db = admin.firestore();

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const data: SubmissionData = req.body;

    // Validate: at least one of gameName or steamId required
    if (!data.gameName?.trim() && !data.steamId?.trim()) {
      return res.status(400).json({ error: 'Game name or Steam ID is required' });
    }

    const doc = await db.collection('ngn-submissions').add({
      gameName: data.gameName || '',
      steamId: data.steamId || '',
      submissionType: data.submissionType,
      submitterType: data.submitterType,
      registry: data.registry,
      availability: data.availability || '',
      centrality: data.centrality || '',
      pov: data.pov || '',
      naming: data.naming || '',
      vampirism: data.vampirism || '',
      hemomancy: data.hemomancy || '',
      notes: data.notes || '',
      contact: data.contact || '',
      status: 'pending',
      source: 'web',
      created_at: admin.firestore.FieldValue.serverTimestamp(),
    });

    return res.status(200).json({ success: true, id: doc.id });
  } catch (error) {
    console.error('Submission error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
