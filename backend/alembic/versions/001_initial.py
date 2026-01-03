"""Initial migration - create all tables.

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========== Organizations ==========
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('audit_period_start', sa.Date, nullable=True),
        sa.Column('audit_period_end', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    # ========== Users ==========
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, default='member'),
        sa.Column('external_auth_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_org_id', 'users', ['org_id'])
    op.create_index('ix_users_external_auth_id', 'users', ['external_auth_id'])

    # ========== Integrations ==========
    op.create_table(
        'integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('connector_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='disconnected'),
        sa.Column('encrypted_credentials', sa.Text, nullable=True),
        sa.Column('config', postgresql.JSONB, nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_integrations_org_id', 'integrations', ['org_id'])
    op.create_index('ix_integrations_connector_type', 'integrations', ['connector_type'])

    # ========== Sync Jobs ==========
    op.create_table(
        'sync_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('integrations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('artifacts_found', sa.Integer, nullable=False, default=0),
        sa.Column('artifacts_created', sa.Integer, nullable=False, default=0),
        sa.Column('error_details', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_sync_jobs_integration_id', 'sync_jobs', ['integration_id'])
    op.create_index('ix_sync_jobs_status', 'sync_jobs', ['status'])

    # ========== Controls ==========
    op.create_table(
        'controls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('control_id', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('evidence_requirements', sa.Text, nullable=True),
        sa.Column('required_evidence_types', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('framework', 'control_id', name='uq_controls_framework_control_id'),
    )
    op.create_index('ix_controls_framework', 'controls', ['framework'])
    op.create_index('ix_controls_control_id', 'controls', ['control_id'])

    # ========== Evidence Artifacts ==========
    op.create_table(
        'evidence_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sync_job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sync_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_system', sa.String(50), nullable=False),
        sa.Column('source_object_id', sa.String(255), nullable=False),
        sa.Column('source_url', sa.String(2048), nullable=False),
        sa.Column('source_created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('artifact_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('raw_content', postgresql.JSONB, nullable=False),
        sa.Column('normalized_content', postgresql.JSONB, nullable=False),
        sa.Column('period_start', sa.Date, nullable=True),
        sa.Column('period_end', sa.Date, nullable=True),
        sa.Column('approval_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('org_id', 'source_system', 'source_object_id', name='uq_artifacts_source'),
    )
    op.create_index('ix_evidence_artifacts_org_id', 'evidence_artifacts', ['org_id'])
    op.create_index('ix_evidence_artifacts_source_system', 'evidence_artifacts', ['source_system'])
    op.create_index('ix_evidence_artifacts_artifact_type', 'evidence_artifacts', ['artifact_type'])
    op.create_index('ix_evidence_artifacts_approval_status', 'evidence_artifacts', ['approval_status'])
    op.create_index('ix_evidence_artifacts_captured_at', 'evidence_artifacts', ['captured_at'])
    op.create_index('ix_evidence_artifacts_period', 'evidence_artifacts', ['period_start', 'period_end'])

    # ========== Control Mappings ==========
    op.create_table(
        'control_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('artifact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evidence_artifacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('control_id', sa.String(50), nullable=False),
        sa.Column('mapping_source', sa.String(50), nullable=False),
        sa.Column('mapping_rationale', sa.Text, nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=False, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('artifact_id', 'control_id', name='uq_control_mappings_artifact_control'),
    )
    op.create_index('ix_control_mappings_artifact_id', 'control_mappings', ['artifact_id'])
    op.create_index('ix_control_mappings_control_id', 'control_mappings', ['control_id'])

    # ========== Approval Records ==========
    op.create_table(
        'approval_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('artifact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evidence_artifacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved', sa.Boolean, nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('signature_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_approval_records_artifact_id', 'approval_records', ['artifact_id'])
    op.create_index('ix_approval_records_user_id', 'approval_records', ['user_id'])
    op.create_index('ix_approval_records_approved_at', 'approval_records', ['approved_at'])

    # ========== Evidence Packets ==========
    op.create_table(
        'evidence_packets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('control_id', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='draft'),
        sa.Column('ai_narrative', sa.Text, nullable=True),
        sa.Column('narrative_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('narrative_approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('narrative_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('drive_folder_url', sa.String(2048), nullable=True),
        sa.Column('exported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_evidence_packets_org_id', 'evidence_packets', ['org_id'])
    op.create_index('ix_evidence_packets_control_id', 'evidence_packets', ['control_id'])
    op.create_index('ix_evidence_packets_status', 'evidence_packets', ['status'])

    # ========== Packet Items ==========
    op.create_table(
        'packet_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('packet_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evidence_packets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('artifact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evidence_artifacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('display_order', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('packet_id', 'artifact_id', name='uq_packet_items_packet_artifact'),
    )
    op.create_index('ix_packet_items_packet_id', 'packet_items', ['packet_id'])
    op.create_index('ix_packet_items_artifact_id', 'packet_items', ['artifact_id'])

    # ========== Audit Logs (append-only) ==========
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('previous_value', postgresql.JSONB, nullable=True),
        sa.Column('new_value', postgresql.JSONB, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_org_id', 'audit_logs', ['org_id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'])
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    # ========== Seed Change Management Controls ==========
    op.execute("""
        INSERT INTO controls (id, framework, control_id, title, description, required_evidence_types, is_active, created_at, updated_at)
        VALUES 
        (gen_random_uuid(), 'soc2', 'CC7.1', 'Change Management Process', 
         'The entity implements policies and procedures to manage the initiation, development, acquisition, configuration, modification, approval, testing, and implementation of changes.',
         ARRAY['pull_request', 'jira_issue', 'document'], true, NOW(), NOW()),
        (gen_random_uuid(), 'soc2', 'CC7.2', 'Change Testing', 
         'The entity tests changes before implementation to verify that they function as intended.',
         ARRAY['pull_request', 'code_review'], true, NOW(), NOW()),
        (gen_random_uuid(), 'soc2', 'CC7.3', 'Change Approval', 
         'Changes are authorized before implementation and the authorization is documented.',
         ARRAY['code_review', 'jira_issue'], true, NOW(), NOW())
    """)


def downgrade() -> None:
    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_table('audit_logs')
    op.drop_table('packet_items')
    op.drop_table('evidence_packets')
    op.drop_table('approval_records')
    op.drop_table('control_mappings')
    op.drop_table('evidence_artifacts')
    op.drop_table('controls')
    op.drop_table('sync_jobs')
    op.drop_table('integrations')
    op.drop_table('users')
    op.drop_table('organizations')
