import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Python Quest · A little code. A new adventure.', description: 'Your personal Python learning world. Explore four original courses and solve real Python challenges.', icons: { icon: '/favicon.svg' } };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en"><body>{children}</body></html>; }
