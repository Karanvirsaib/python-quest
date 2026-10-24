import { sqliteTable, text, integer, primaryKey } from 'drizzle-orm/sqlite-core';
export const progress = sqliteTable('progress', {
 userId: text('user_id').notNull(), lessonId: text('lesson_id').notNull(),
 code: text('code').notNull().default(''), notes: text('notes').notNull().default(''),
 completed: integer('completed', { mode: 'boolean' }).notNull().default(false),
 completedAt: text('completed_at'), updatedAt: text('updated_at').notNull(),
}, t => [primaryKey({ columns: [t.userId, t.lessonId] })]);
export const profiles = sqliteTable('profiles', { userId: text('user_id').primaryKey(), name: text('name').notNull(), goal: integer('goal').notNull().default(1) });
