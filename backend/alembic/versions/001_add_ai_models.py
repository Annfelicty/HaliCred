"""Add AI models

Revision ID: 001_add_ai_models
Revises: 
Create Date: 2024-08-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_ai_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_evidence table
    op.create_table('ai_evidence',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=False),
    sa.Column('file_name', sa.String(length=255), nullable=False),
    sa.Column('file_size_mb', sa.Float(), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('sector', sa.String(length=50), nullable=False),
    sa.Column('region', sa.String(length=50), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('location_accuracy', sa.Float(), nullable=True),
    sa.Column('processing_status', sa.String(length=20), nullable=True),
    sa.Column('processing_started_at', sa.DateTime(), nullable=True),
    sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_evidence_sector', 'ai_evidence', ['sector'], unique=False)
    op.create_index('idx_evidence_status', 'ai_evidence', ['processing_status'], unique=False)
    op.create_index('idx_evidence_type', 'ai_evidence', ['type'], unique=False)
    op.create_index('idx_evidence_uploaded_at', 'ai_evidence', ['uploaded_at'], unique=False)
    op.create_index('idx_evidence_user_id', 'ai_evidence', ['user_id'], unique=False)

    # Create ocr_results table
    op.create_table('ocr_results',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('raw_text', sa.Text(), nullable=True),
    sa.Column('vendor', sa.String(length=255), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('items', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('text_regions_count', sa.Integer(), nullable=True),
    sa.Column('processing_method', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['evidence_id'], ['ai_evidence.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create cv_results table
    op.create_table('cv_results',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('labels', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('confidence_scores', postgresql.ARRAY(sa.Float()), nullable=True),
    sa.Column('bounding_boxes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('solar_panels_detected', sa.Boolean(), nullable=True),
    sa.Column('led_lights_detected', sa.Boolean(), nullable=True),
    sa.Column('meters_detected', sa.Boolean(), nullable=True),
    sa.Column('equipment_count', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('processing_method', sa.String(length=50), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['evidence_id'], ['ai_evidence.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create emission_results table
    op.create_table('emission_results',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('co2_kg_total', sa.Float(), nullable=False),
    sa.Column('co2_kg_components', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('emission_factors_used', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('method', sa.String(length=50), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('data_completeness', sa.Float(), nullable=True),
    sa.Column('features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['evidence_id'], ['ai_evidence.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create greenscore_results table
    op.create_table('greenscore_results',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('greenscore', sa.Integer(), nullable=False),
    sa.Column('subscores', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('co2_saved_tonnes', sa.Float(), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('explainers', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('actions', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('sector', sa.String(length=50), nullable=False),
    sa.Column('region', sa.String(length=50), nullable=True),
    sa.Column('calculation_method', sa.String(length=50), nullable=True),
    sa.Column('provenance', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('review_required', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['evidence_id'], ['ai_evidence.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_greenscore_created_at', 'greenscore_results', ['created_at'], unique=False)
    op.create_index('idx_greenscore_score', 'greenscore_results', ['greenscore'], unique=False)
    op.create_index('idx_greenscore_sector', 'greenscore_results', ['sector'], unique=False)
    op.create_index('idx_greenscore_user_id', 'greenscore_results', ['user_id'], unique=False)

    # Create carbon_credits table
    op.create_table('carbon_credits',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('greenscore_result_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('standard', sa.String(length=50), nullable=False),
    sa.Column('tonnes_co2', sa.Float(), nullable=False),
    sa.Column('annual_tonnes', sa.Float(), nullable=False),
    sa.Column('project_lifetime_years', sa.Integer(), nullable=True),
    sa.Column('buffer_percentage', sa.Float(), nullable=False),
    sa.Column('gross_value_usd', sa.Float(), nullable=False),
    sa.Column('net_value_usd', sa.Float(), nullable=False),
    sa.Column('verification_cost_usd', sa.Float(), nullable=True),
    sa.Column('pooling_fee_usd', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('approach', sa.String(length=20), nullable=False),
    sa.Column('pool_id', sa.String(length=100), nullable=True),
    sa.Column('additionality_verified', sa.Boolean(), nullable=True),
    sa.Column('estimated_issuance', sa.DateTime(), nullable=True),
    sa.Column('actual_issuance', sa.DateTime(), nullable=True),
    sa.Column('registry_id', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['evidence_id'], ['ai_evidence.id'], ),
    sa.ForeignKeyConstraint(['greenscore_result_id'], ['greenscore_results.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_carbon_credit_created_at', 'carbon_credits', ['created_at'], unique=False)
    op.create_index('idx_carbon_credit_standard', 'carbon_credits', ['standard'], unique=False)
    op.create_index('idx_carbon_credit_status', 'carbon_credits', ['status'], unique=False)
    op.create_index('idx_carbon_credit_user_id', 'carbon_credits', ['user_id'], unique=False)

    # Create sector_baselines table
    op.create_table('sector_baselines',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('sector', sa.String(length=50), nullable=False),
    sa.Column('region', sa.String(length=50), nullable=False),
    sa.Column('baseline_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('data_source', sa.String(length=200), nullable=False),
    sa.Column('sample_size', sa.Integer(), nullable=True),
    sa.Column('valid_from', sa.DateTime(), nullable=True),
    sa.Column('valid_until', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sector_baseline_sector_region', 'sector_baselines', ['sector', 'region'], unique=False)
    op.create_index('idx_sector_baseline_valid', 'sector_baselines', ['valid_from', 'valid_until'], unique=False)

    # Create review_cases table
    op.create_table('review_cases',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('case_id', sa.String(length=100), nullable=False),
    sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('greenscore_result_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('priority', sa.String(length=10), nullable=True),
    sa.Column('reasons', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('confidence_score', sa.Float(), nullable=True),
    sa.Column('assigned_reviewer_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('reviewer_notes', sa.Text(), nullable=True),
    sa.Column('review_decision', sa.String(length=20), nullable=True),
    sa.Column('review_completed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('review_deadline', sa.DateTime(), nullable=True),
    sa.Column('escalation_level', sa.Integer(), nullable=True),
    sa.Column('ai_result_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['assigned_reviewer_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['evidence_id'], ['ai_evidence.id'], ),
    sa.ForeignKeyConstraint(['greenscore_result_id'], ['greenscore_results.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('case_id')
    )
    op.create_index('idx_review_case_created_at', 'review_cases', ['created_at'], unique=False)
    op.create_index('idx_review_case_deadline', 'review_cases', ['review_deadline'], unique=False)
    op.create_index('idx_review_case_priority', 'review_cases', ['priority'], unique=False)
    op.create_index('idx_review_case_status', 'review_cases', ['status'], unique=False)

    # Create ai_processing_logs table
    op.create_table('ai_processing_logs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('request_id', sa.String(length=100), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('processing_method', sa.String(length=50), nullable=True),
    sa.Column('processing_time_ms', sa.Integer(), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('ai_model_used', sa.String(length=50), nullable=True),
    sa.Column('function_calls_made', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('confidence_final', sa.Float(), nullable=True),
    sa.Column('greenscore_achieved', sa.Integer(), nullable=True),
    sa.Column('carbon_credits_calculated', sa.Integer(), nullable=True),
    sa.Column('review_triggered', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['evidence_id'], ['ai_evidence.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('request_id')
    )
    op.create_index('idx_ai_log_created_at', 'ai_processing_logs', ['created_at'], unique=False)
    op.create_index('idx_ai_log_success', 'ai_processing_logs', ['success'], unique=False)
    op.create_index('idx_ai_log_user_id', 'ai_processing_logs', ['user_id'], unique=False)

    # Create user_greenscore_history table
    op.create_table('user_greenscore_history',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('greenscore', sa.Integer(), nullable=False),
    sa.Column('subscores', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('evidence_count', sa.Integer(), nullable=True),
    sa.Column('total_co2_saved_tonnes', sa.Float(), nullable=True),
    sa.Column('total_carbon_credits_value_usd', sa.Float(), nullable=True),
    sa.Column('sector_percentile', sa.Float(), nullable=True),
    sa.Column('regional_percentile', sa.Float(), nullable=True),
    sa.Column('global_percentile', sa.Float(), nullable=True),
    sa.Column('calculation_date', sa.DateTime(), nullable=True),
    sa.Column('period_start', sa.DateTime(), nullable=True),
    sa.Column('period_end', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_history_date', 'user_greenscore_history', ['calculation_date'], unique=False)
    op.create_index('idx_user_history_score', 'user_greenscore_history', ['greenscore'], unique=False)
    op.create_index('idx_user_history_user_id', 'user_greenscore_history', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('user_greenscore_history')
    op.drop_table('ai_processing_logs')
    op.drop_table('review_cases')
    op.drop_table('sector_baselines')
    op.drop_table('carbon_credits')
    op.drop_table('greenscore_results')
    op.drop_table('emission_results')
    op.drop_table('cv_results')
    op.drop_table('ocr_results')
    op.drop_table('ai_evidence')
