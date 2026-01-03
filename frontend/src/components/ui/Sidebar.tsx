'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    Link2,
    FileCheck,
    Shield,
    Package,
    Settings,
    HelpCircle,
} from 'lucide-react';
import { clsx } from 'clsx';

const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Integrations', href: '/integrations', icon: Link2 },
    { name: 'Evidence', href: '/evidence', icon: FileCheck },
    { name: 'Controls', href: '/controls', icon: Shield },
    { name: 'Packets', href: '/packets', icon: Package },
];

const secondaryNavigation = [
    { name: 'Settings', href: '/settings', icon: Settings },
    { name: 'Help', href: '/help', icon: HelpCircle },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="flex w-64 flex-col border-r border-slate-200 bg-white">
            {/* Logo */}
            <div className="flex h-16 items-center gap-2 border-b border-slate-200 px-6">
                <Shield className="h-8 w-8 text-primary-600" />
                <div>
                    <span className="text-lg font-bold text-slate-900">Compliance</span>
                    <span className="block text-xs text-slate-500">Packet Agent</span>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1 px-3 py-4">
                {navigation.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={clsx(
                                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                                isActive
                                    ? 'bg-primary-50 text-primary-700'
                                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                            )}
                        >
                            <item.icon className="h-5 w-5" />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>

            {/* Secondary Navigation */}
            <div className="border-t border-slate-200 px-3 py-4 space-y-1">
                {secondaryNavigation.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={clsx(
                                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                                isActive
                                    ? 'bg-primary-50 text-primary-700'
                                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                            )}
                        >
                            <item.icon className="h-5 w-5" />
                            {item.name}
                        </Link>
                    );
                })}
            </div>

            {/* Audit Period Indicator */}
            <div className="border-t border-slate-200 p-4">
                <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-xs font-medium text-slate-500 uppercase">
                        Audit Period
                    </p>
                    <p className="mt-1 text-sm font-semibold text-slate-900">
                        Q4 2024
                    </p>
                    <p className="text-xs text-slate-500">Oct 1 - Dec 31, 2024</p>
                </div>
            </div>
        </aside>
    );
}
