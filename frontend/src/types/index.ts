/**
 * Type definitions for the Compliance Packet Agent
 */

// Re-export API types
export type {
    Integration,
    Artifact,
    ArtifactListParams,
    ArtifactListResponse,
    Control,
    CoverageReport,
    Gap,
    Packet,
    PacketItem,
    CreatePacketRequest,
    ExportJob,
} from '@/lib/api';

// Additional UI types
export type Status = 'pending' | 'approved' | 'rejected';

export type Severity = 'high' | 'medium' | 'low';

export type IntegrationType = 'github' | 'jira' | 'google_drive';

export type Framework = 'soc2' | 'iso27001';

export interface User {
    id: string;
    email: string;
    name: string;
    org_id: string | null;
    role: 'owner' | 'admin' | 'member';
}

export interface Organization {
    id: string;
    name: string;
    slug: string;
    audit_period_start: string | null;
    audit_period_end: string | null;
}

export interface AuditPeriod {
    start: Date;
    end: Date;
    label: string;
}
