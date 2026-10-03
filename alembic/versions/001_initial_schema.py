"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-03

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Active'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Policies table
    op.create_table(
        'policies',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('policy_name', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('service', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policies_id'), 'policies', ['id'], unique=False)

    # Permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('policy_id', sa.String(length=100), nullable=False),
        sa.Column('effect', sa.String(length=20), nullable=False, server_default='Allow'),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('resource', sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Access Logs table
    op.create_table(
        'access_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('service', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('resource', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SUCCESS'),
        sa.Column('source_ip', sa.String(length=50), nullable=True),
        sa.Column('region', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Findings table
    op.create_table(
        'findings',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('finding_type', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('policy_id', sa.String(length=100), nullable=True),
        sa.Column('service', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('resource', sa.String(length=500), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Open'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_findings_id'), 'findings', ['id'], unique=False)

    # Recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('finding_id', sa.String(length=100), nullable=False),
        sa.Column('current_action', sa.String(length=255), nullable=False),
        sa.Column('recommended_action', sa.String(length=255), nullable=False),
        sa.Column('current_resource', sa.String(length=500), nullable=False),
        sa.Column('recommended_resource', sa.String(length=500), nullable=False),
        sa.Column('reason', sa.String(length=1000), nullable=False),
        sa.Column('risk_reduction', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Audit Reports table
    op.create_table(
        'audit_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('audit_id', sa.String(length=100), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('policies_analyzed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('users_analyzed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('events_analyzed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('high_risk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('least_privilege_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='completed'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_reports_audit_id'), 'audit_reports', ['audit_id'], unique=True)


def downgrade() -> None:
    op.drop_table('audit_reports')
    op.drop_table('recommendations')
    op.drop_table('findings')
    op.drop_table('access_logs')
    op.drop_table('permissions')
    op.drop_table('policies')
    op.drop_table('users')
