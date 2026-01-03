import {
    FileText,
    GitPullRequest,
    AlertTriangle,
    CheckCircle,
    Clock,
} from 'lucide-react';

export default function DashboardPage() {
    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
                <p className="mt-2 text-slate-600">
                    Compliance evidence overview and audit readiness status
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <StatCard
                    title="Total Artifacts"
                    value="247"
                    change="+12 this week"
                    icon={FileText}
                    iconColor="text-primary-600"
                    bgColor="bg-primary-50"
                />
                <StatCard
                    title="Pending Approval"
                    value="18"
                    change="3 high priority"
                    icon={Clock}
                    iconColor="text-warning-500"
                    bgColor="bg-warning-50"
                />
                <StatCard
                    title="Approved"
                    value="215"
                    change="87% approval rate"
                    icon={CheckCircle}
                    iconColor="text-success-500"
                    bgColor="bg-success-50"
                />
                <StatCard
                    title="Gaps Detected"
                    value="4"
                    change="2 critical"
                    icon={AlertTriangle}
                    iconColor="text-danger-500"
                    bgColor="bg-danger-50"
                />
            </div>

            {/* Controls Overview */}
            <div className="card p-6">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">
                    Change Management Controls
                </h2>
                <div className="space-y-4">
                    <ControlRow
                        id="CC7.1"
                        name="Change Management Process"
                        artifacts={45}
                        approved={42}
                        status="partial"
                    />
                    <ControlRow
                        id="CC7.2"
                        name="Change Testing"
                        artifacts={38}
                        approved={38}
                        status="complete"
                    />
                    <ControlRow
                        id="CC7.3"
                        name="Change Approval"
                        artifacts={52}
                        approved={48}
                        status="partial"
                    />
                </div>
            </div>

            {/* Recent Activity */}
            <div className="card p-6">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">
                    Recent Activity
                </h2>
                <div className="space-y-4">
                    <ActivityItem
                        icon={GitPullRequest}
                        title="New PR synced from GitHub"
                        description="feat: Add user authentication #234"
                        time="2 minutes ago"
                    />
                    <ActivityItem
                        icon={CheckCircle}
                        title="Evidence approved"
                        description="JIRA-456: Security patch deployment"
                        time="15 minutes ago"
                    />
                    <ActivityItem
                        icon={FileText}
                        title="Narrative generated"
                        description="CC7.1 - Q4 2024 Evidence Packet"
                        time="1 hour ago"
                    />
                </div>
            </div>
        </div>
    );
}

function StatCard({
    title,
    value,
    change,
    icon: Icon,
    iconColor,
    bgColor,
}: {
    title: string;
    value: string;
    change: string;
    icon: any;
    iconColor: string;
    bgColor: string;
}) {
    return (
        <div className="card p-6">
            <div className="flex items-center gap-4">
                <div className={`rounded-lg p-3 ${bgColor}`}>
                    <Icon className={`h-6 w-6 ${iconColor}`} />
                </div>
                <div>
                    <p className="text-sm font-medium text-slate-600">{title}</p>
                    <p className="text-2xl font-bold text-slate-900">{value}</p>
                    <p className="text-sm text-slate-500">{change}</p>
                </div>
            </div>
        </div>
    );
}

function ControlRow({
    id,
    name,
    artifacts,
    approved,
    status,
}: {
    id: string;
    name: string;
    artifacts: number;
    approved: number;
    status: 'complete' | 'partial' | 'missing';
}) {
    const percentage = Math.round((approved / artifacts) * 100);
    const statusColors = {
        complete: 'badge-success',
        partial: 'badge-warning',
        missing: 'badge-danger',
    };

    return (
        <div className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0">
            <div className="flex items-center gap-4">
                <span className="font-mono text-sm font-medium text-slate-500">{id}</span>
                <span className="font-medium text-slate-900">{name}</span>
            </div>
            <div className="flex items-center gap-4">
                <div className="text-right">
                    <span className="text-sm text-slate-600">
                        {approved}/{artifacts} approved
                    </span>
                    <div className="w-24 h-2 bg-slate-100 rounded-full mt-1">
                        <div
                            className="h-2 bg-primary-500 rounded-full"
                            style={{ width: `${percentage}%` }}
                        />
                    </div>
                </div>
                <span className={`badge ${statusColors[status]}`}>
                    {status === 'complete' ? 'Complete' : status === 'partial' ? 'Partial' : 'Missing'}
                </span>
            </div>
        </div>
    );
}

function ActivityItem({
    icon: Icon,
    title,
    description,
    time,
}: {
    icon: any;
    title: string;
    description: string;
    time: string;
}) {
    return (
        <div className="flex items-start gap-4 py-3 border-b border-slate-100 last:border-0">
            <div className="rounded-lg bg-slate-100 p-2">
                <Icon className="h-5 w-5 text-slate-600" />
            </div>
            <div className="flex-1">
                <p className="font-medium text-slate-900">{title}</p>
                <p className="text-sm text-slate-600">{description}</p>
            </div>
            <span className="text-sm text-slate-500">{time}</span>
        </div>
    );
}
