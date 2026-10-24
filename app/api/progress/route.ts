import { getChatGPTUser } from '../../chatgpt-auth';
import { getDb } from '../../../db';
import { progress, profiles } from '../../../db/schema';
import { eq, sql } from 'drizzle-orm';
import { courses } from '../../curriculum';
export const dynamic = 'force-dynamic';
export async function GET() {
  const user = await getChatGPTUser();
  if (!user) return Response.json({ error: 'Sign in to save your progress.' }, { status: 401 });
  try {
    const db = getDb();
    const records = await db.select().from(progress).where(eq(progress.userId, user.userId));
    const profile = (await db.select().from(profiles).where(eq(profiles.userId, user.userId)))[0];
    return Response.json({ records: records.map(({userId: _, ...record}) => record), profile: profile ? { name: profile.name, goal: profile.goal } : { name: user.fullName || 'Explorer', goal: 1 } }, { headers: { 'Cache-Control': 'no-store' } });
  } catch { return Response.json({ error: 'Progress is temporarily unavailable. Please retry.' }, { status: 503 }); }
}
export async function PUT(request: Request) {
  const user = await getChatGPTUser();
  if (!user) return Response.json({ error: 'Sign in to save your progress.' }, { status: 401 });
  try {
    const raw = await request.text();
    if (raw.length > 70000) return Response.json({ error: 'Your draft is too large.' }, { status: 413 });
    const body = JSON.parse(raw);
    const db = getDb();
    if (body.profile) {
      const { name, goal } = body.profile;
      if (typeof name !== 'string' || !name.trim() || name.length > 40 || ![1,2,3].includes(goal)) return Response.json({ error: 'Use a name up to 40 characters and a goal of 1–3 lessons.' }, { status: 400 });
      await db.insert(profiles).values({ userId: user.userId, name: name.trim(), goal }).onConflictDoUpdate({ target: profiles.userId, set: { name: name.trim(), goal } });
      return Response.json({ ok: true });
    }
    if (!courses.some(c => c.lessons.some(l => l.id === body.lessonId))) return Response.json({ error: 'Unknown lesson.' }, { status: 400 });
    if (typeof body.code !== 'string' || typeof body.notes !== 'string' || body.code.length > 50000 || body.notes.length > 10000 || typeof body.completed !== 'boolean') return Response.json({ error: 'Invalid lesson data.' }, { status: 400 });
    const now = new Date().toISOString();
    const values = { userId: user.userId, lessonId: body.lessonId, code: body.code, notes: body.notes, completed: body.completed, completedAt: body.completed ? now : null, updatedAt: now };
    await db.insert(progress).values(values).onConflictDoUpdate({ target: [progress.userId, progress.lessonId], set: { code: body.code, notes: body.notes, updatedAt: now, ...(body.completed ? { completed: true, completedAt: sql`coalesce(${progress.completedAt}, ${now})` } : {}) } });
    return Response.json({ ok: true });
  } catch { return Response.json({ error: 'Could not save. Check your connection and retry.' }, { status: 503 }); }
}
