import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Overcut - F1 Race Engineer Dashboard',
    description: 'Interactive F1 Telemetry & Strategy Analysis',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="dark">
            <body className={`${inter.className} bg-background text-text-primary antialiased`}>
                {children}
            </body>
        </html>
    );
}
