import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Python Quest · A little code. A new adventure.', description: 'Your personal Python learning world. Explore 12 courses and 88 Python-for-data exercises, from first principles to production scenarios.', icons: { icon: '/favicon.svg' } };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en"><body>{children}</body></html>; }
