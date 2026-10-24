import data from './curriculum.json';
export type Lesson = { id: string; title: string; summary: string; theory: string; example: string; task: string; starter: string; hint: string; solution: string; tests: string; minutes: number; xp: number; input: string };
export type Course = { id: string; title: string; subtitle: string; description: string; color: string; icon: string; level: string; time: string; land: string; lessons: Lesson[] };
export const courses: Course[] = data;
