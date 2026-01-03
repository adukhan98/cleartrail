import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { Sidebar } from '@/components/ui/Sidebar';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Compliance Packet Agent',
    description: 'AI-assisted evidence compiler for SOC 2 and ISO 27001 compliance',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <Providers>
                    <div className="flex min-h-screen">
                        <Sidebar />
                        <main className="flex-1 p-8">{children}</main>
                    </div>
                </Providers>
            </body>
        </html>
    );
}
