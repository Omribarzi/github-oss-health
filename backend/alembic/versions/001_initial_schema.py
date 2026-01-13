"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'repos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.Integer(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('stars', sa.Integer(), nullable=False),
        sa.Column('forks', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('pushed_at', sa.DateTime(), nullable=False),
        sa.Column('archived', sa.Boolean(), nullable=False),
        sa.Column('is_fork', sa.Boolean(), nullable=False),
        sa.Column('first_discovered_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('eligible', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_repos_id', 'repos', ['id'])
    op.create_index('ix_repos_github_id', 'repos', ['github_id'], unique=True)
    op.create_index('ix_repos_owner', 'repos', ['owner'])
    op.create_index('ix_repos_name', 'repos', ['name'])
    op.create_index('ix_repos_full_name', 'repos', ['full_name'], unique=True)
    op.create_index('ix_repos_language', 'repos', ['language'])
    op.create_index('ix_repos_stars', 'repos', ['stars'])
    op.create_index('ix_repos_created_at', 'repos', ['created_at'])
    op.create_index('ix_repos_pushed_at', 'repos', ['pushed_at'])
    op.create_index('ix_repos_eligible', 'repos', ['eligible'])
    op.create_index('idx_repo_stars_created', 'repos', ['stars', 'created_at'])
    op.create_index('idx_repo_eligible_stars', 'repos', ['eligible', 'stars'])

    op.create_table(
        'discovery_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(), nullable=False),
        sa.Column('stars', sa.Integer(), nullable=False),
        sa.Column('forks', sa.Integer(), nullable=False),
        sa.Column('pushed_at', sa.DateTime(), nullable=False),
        sa.Column('eligible', sa.Boolean(), nullable=False),
        sa.Column('snapshot_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_discovery_snapshots_id', 'discovery_snapshots', ['id'])
    op.create_index('ix_discovery_snapshots_repo_id', 'discovery_snapshots', ['repo_id'])
    op.create_index('ix_discovery_snapshots_snapshot_date', 'discovery_snapshots', ['snapshot_date'])
    op.create_index('idx_discovery_repo_date', 'discovery_snapshots', ['repo_id', 'snapshot_date'])

    op.create_table(
        'deep_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(), nullable=False),
        sa.Column('monthly_active_contributors_6m', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('contribution_distribution', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('weekly_commits_12w', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('weekly_prs_12w', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('weekly_issues_12w', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('commit_trend_slope', sa.Float(), nullable=True),
        sa.Column('pr_trend_slope', sa.Float(), nullable=True),
        sa.Column('issue_trend_slope', sa.Float(), nullable=True),
        sa.Column('median_issue_response_time_hours', sa.Float(), nullable=True),
        sa.Column('median_pr_response_time_hours', sa.Float(), nullable=True),
        sa.Column('response_time_availability', sa.String(), nullable=True),
        sa.Column('dependents_count', sa.Integer(), nullable=True),
        sa.Column('npm_downloads_30d', sa.Integer(), nullable=True),
        sa.Column('fork_to_star_ratio', sa.Float(), nullable=True),
        sa.Column('adoption_availability', sa.String(), nullable=True),
        sa.Column('top_contributor_share', sa.Float(), nullable=True),
        sa.Column('gini_coefficient', sa.Float(), nullable=True),
        sa.Column('active_maintainers_count', sa.Integer(), nullable=True),
        sa.Column('health_index', sa.Float(), nullable=True),
        sa.Column('metrics_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_deep_snapshots_id', 'deep_snapshots', ['id'])
    op.create_index('ix_deep_snapshots_repo_id', 'deep_snapshots', ['repo_id'])
    op.create_index('ix_deep_snapshots_snapshot_date', 'deep_snapshots', ['snapshot_date'])
    op.create_index('idx_deep_repo_date', 'deep_snapshots', ['repo_id', 'snapshot_date'])

    op.create_table(
        'repo_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('priority_reason', sa.String(), nullable=False),
        sa.Column('queued_at', sa.DateTime(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('last_deep_analysis_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_repo_queue_id', 'repo_queue', ['id'])
    op.create_index('ix_repo_queue_repo_id', 'repo_queue', ['repo_id'])
    op.create_index('ix_repo_queue_priority', 'repo_queue', ['priority'])
    op.create_index('ix_repo_queue_processed', 'repo_queue', ['processed'])
    op.create_index('ix_repo_queue_last_deep_analysis_at', 'repo_queue', ['last_deep_analysis_at'])
    op.create_index('idx_queue_priority', 'repo_queue', ['processed', 'priority', 'queued_at'])

    op.create_table(
        'investor_watchlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=False),
        sa.Column('watchlist_date', sa.DateTime(), nullable=False),
        sa.Column('momentum_score', sa.Float(), nullable=False),
        sa.Column('durability_score', sa.Float(), nullable=False),
        sa.Column('adoption_score', sa.Float(), nullable=False),
        sa.Column('rationale', sa.String(), nullable=False),
        sa.Column('metrics_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_investor_watchlists_id', 'investor_watchlists', ['id'])
    op.create_index('ix_investor_watchlists_repo_id', 'investor_watchlists', ['repo_id'])
    op.create_index('ix_investor_watchlists_watchlist_date', 'investor_watchlists', ['watchlist_date'])
    op.create_index('idx_watchlist_date_momentum', 'investor_watchlists', ['watchlist_date', 'momentum_score'])
    op.create_index('idx_watchlist_date_durability', 'investor_watchlists', ['watchlist_date', 'durability_score'])
    op.create_index('idx_watchlist_date_adoption', 'investor_watchlists', ['watchlist_date', 'adoption_score'])

    op.create_table(
        'job_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('stats_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_job_runs_id', 'job_runs', ['id'])
    op.create_index('ix_job_runs_job_type', 'job_runs', ['job_type'])
    op.create_index('ix_job_runs_started_at', 'job_runs', ['started_at'])
    op.create_index('idx_job_type_started', 'job_runs', ['job_type', 'started_at'])

    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('repo_id', sa.Integer(), nullable=True),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['repo_id'], ['repos.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alerts_id', 'alerts', ['id'])
    op.create_index('ix_alerts_alert_type', 'alerts', ['alert_type'])
    op.create_index('ix_alerts_severity', 'alerts', ['severity'])
    op.create_index('ix_alerts_repo_id', 'alerts', ['repo_id'])
    op.create_index('ix_alerts_resolved', 'alerts', ['resolved'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])
    op.create_index('idx_alert_unresolved', 'alerts', ['resolved', 'severity', 'created_at'])


def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_table('job_runs')
    op.drop_table('investor_watchlists')
    op.drop_table('repo_queue')
    op.drop_table('deep_snapshots')
    op.drop_table('discovery_snapshots')
    op.drop_table('repos')
