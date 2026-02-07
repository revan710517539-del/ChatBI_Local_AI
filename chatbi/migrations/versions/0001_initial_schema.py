"""Initial database schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-01-10 10:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create datasources table
    op.create_table(
        'datasources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('connection_info', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_datasources')),
        sa.UniqueConstraint('name', name=op.f('uq_datasources_name'))
    )
    op.create_index(op.f('ix_datasources_name'), 'datasources', ['name'], unique=False)
    op.create_index(op.f('ix_datasources_type'), 'datasources', ['type'], unique=False)

    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('datasource_id', sa.String(length=36), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('last_active', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id'], name=op.f('fk_chat_sessions_datasource_id_datasources')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_chat_sessions'))
    )

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('table_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('query_sql', sa.Text(), nullable=True),
        sa.Column('execution_time', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], name=op.f('fk_chat_messages_session_id_chat_sessions')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_chat_messages'))
    )

    # Create visualizations table
    op.create_table(
        'visualizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('message_id', sa.String(length=36), nullable=False),
        sa.Column('chart_type', sa.String(length=50), nullable=False),
        sa.Column('chart_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], name=op.f('fk_visualizations_message_id_chat_messages')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_visualizations'))
    )

    # Create query_history table
    op.create_table(
        'query_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('datasource_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('sql', sa.Text(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=False),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='success', nullable=False),
        sa.Column('executed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id'], name=op.f('fk_query_history_datasource_id_datasources')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_query_history'))
    )
    op.create_index(op.f('idx_query_history_datasource_id'), 'query_history', ['datasource_id'], unique=False)
    op.create_index(op.f('idx_query_history_executed_at'), 'query_history', ['executed_at'], unique=False)

    # Create chat_history table
    op.create_table(
        'chat_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('question', sa.Text(), nullable=True),
        sa.Column('sql', sa.Text(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('usage', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('field_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_chat_history'))
    )
    op.create_index(op.f('ix_chat_history_conversation_id'), 'chat_history', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_chat_history_user_id'), 'chat_history', ['user_id'], unique=False)

    # Create saved_queries table
    op.create_table(
        'saved_queries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sql', sa.Text(), nullable=False),
        sa.Column('datasource_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('tags', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id'], name=op.f('fk_saved_queries_datasource_id_datasources')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_saved_queries'))
    )

    # Create app_users table
    op.create_table(
        'app_users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_app_users')),
        sa.UniqueConstraint('email', name=op.f('uq_app_users_email')),
        sa.UniqueConstraint('username', name=op.f('uq_app_users_username'))
    )

    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_sessions')),
        sa.UniqueConstraint('refresh_token', name=op.f('uq_user_sessions_refresh_token'))
    )
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)

    # Create MDL tables
    op.create_table(
        'mdl_projects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('datasource_id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id'], name=op.f('fk_mdl_projects_datasource_id_datasources'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['app_users.id'], name=op.f('fk_mdl_projects_owner_id_app_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_mdl_projects'))
    )

    op.create_table(
        'mdl_models',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('primary_key', sa.String(length=100), nullable=True),
        sa.Column('sql_table', sa.String(length=255), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['mdl_projects.id'], name=op.f('fk_mdl_models_project_id_mdl_projects'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_mdl_models'))
    )

    op.create_table(
        'mdl_fields',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('model_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('field_type', sa.String(length=50), nullable=False),
        sa.Column('expression', sa.Text(), nullable=True),
        sa.Column('is_calculated', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['mdl_models.id'], name=op.f('fk_mdl_fields_model_id_mdl_models'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_mdl_fields'))
    )

    op.create_table(
        'mdl_relationships',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('from_model_id', sa.UUID(), nullable=False),
        sa.Column('to_model_id', sa.UUID(), nullable=False),
        sa.Column('join_type', sa.String(length=20), nullable=False),
        sa.Column('condition', sa.Text(), nullable=False),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['from_model_id'], ['mdl_models.id'], name=op.f('fk_mdl_relationships_from_model_id_mdl_models'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['mdl_projects.id'], name=op.f('fk_mdl_relationships_project_id_mdl_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_model_id'], ['mdl_models.id'], name=op.f('fk_mdl_relationships_to_model_id_mdl_models'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_mdl_relationships'))
    )

    # Create diagnosis tables
    op.create_table(
        'error_patterns',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('error_type', sa.String(length=100), nullable=False),
        sa.Column('pattern_regex', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('solution_template', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('frequency_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_error_patterns'))
    )

    op.create_table(
        'sql_corrections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('original_sql', sa.Text(), nullable=False),
        sa.Column('corrected_sql', sa.Text(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('correction_type', sa.String(length=50), nullable=True),
        sa.Column('datasource_id', sa.String(length=36), nullable=True),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id'], name=op.f('fk_sql_corrections_datasource_id_datasources')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sql_corrections'))
    )

    # Create diagnosis_results table
    op.create_table(
        'diagnosis_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('query_id', sa.String(length=36), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('key_points', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_diagnosis_results'))
    )
    op.create_index(op.f('ix_diagnosis_results_query_id'), 'diagnosis_results', ['query_id'], unique=False)

    # Create correction_logs table
    op.create_table(
        'correction_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('query_id', sa.String(length=36), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('original_sql', sa.Text(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('corrected_sql', sa.Text(), nullable=True),
        sa.Column('was_successful', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_correction_logs'))
    )
    op.create_index(op.f('ix_correction_logs_query_id'), 'correction_logs', ['query_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('correction_logs')
    op.drop_table('diagnosis_results')
    op.drop_table('sql_corrections')
    op.drop_table('error_patterns')
    op.drop_table('mdl_relationships')
    op.drop_table('mdl_fields')
    op.drop_table('mdl_models')
    op.drop_table('mdl_projects')
    op.drop_table('user_sessions')
    op.drop_table('app_users')
    op.drop_table('saved_queries')
    op.drop_table('chat_history')
    op.drop_table('query_history')
    op.drop_table('visualizations')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('datasources')
