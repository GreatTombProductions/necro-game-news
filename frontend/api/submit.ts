import type { VercelRequest, VercelResponse } from '@vercel/node';

type RegistryMode = 'necromancy' | 'blood';

interface SubmissionData {
  gameName: string;
  steamId: string;
  submissionType: 'addition' | 'revision';
  submitterType: 'player' | 'developer';
  availability: string;
  centrality: string;
  pov: string;
  naming: string;
  vampirism: string;
  hemomancy: string;
  notes: string;
  contact: string;
  registry: RegistryMode;
}

// Lazy-loaded Firebase singleton — avoids module-scope crash if env vars missing.
let _db: any = null;
let _FieldValue: any = null;

async function initFirebase() {
  if (_db && _FieldValue) return { db: _db, FieldValue: _FieldValue };

  const admin = await import('firebase-admin');

  if (!admin.apps.length) {
    const projectId = process.env.FIREBASE_PROJECT_ID;
    const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;
    const privateKey = process.env.FIREBASE_PRIVATE_KEY;

    if (!projectId || !clientEmail || !privateKey) {
      throw new Error(
        `Missing Firebase env vars. projectId=${!!projectId} clientEmail=${!!clientEmail} privateKey=${!!privateKey}`
      );
    }

    admin.initializeApp({
      credential: admin.credential.cert({
        projectId,
        clientEmail,
        privateKey: privateKey.replace(/\\n/g, '\n'),
      }),
    });
  }

  _db = admin.firestore();
  _FieldValue = admin.firestore.FieldValue;
  return { db: _db, FieldValue: _FieldValue };
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const data: SubmissionData = req.body;

    if (!data.gameName?.trim() && !data.steamId?.trim()) {
      return res.status(400).json({ error: 'Game name or Steam ID is required' });
    }

    const { db, FieldValue } = await initFirebase();

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
      created_at: FieldValue.serverTimestamp(),
    });

    return res.status(200).json({ success: true, id: doc.id });
  } catch (error: any) {
    console.error('Submission error:', error?.message || error);
    return res.status(500).json({
      error: 'Internal server error',
      detail: error?.message || String(error),
    });
  }
}
