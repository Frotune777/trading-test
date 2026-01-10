"""
Alembic migration: Add ML tables

Revision ID: add_ml_tables
Revises: 
Create Date: 2026-01-09 22:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_ml_tables'
down_revision = None  # Update this to the latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Create ML tables."""
    
    # ML Models table
    op.create_table(
        'ml_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=True),
        sa.Column('interval', sa.String(length=10), nullable=True),
        sa.Column('model_path', sa.Text(), nullable=False),
        sa.Column('scaler_path', sa.Text(), nullable=True),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('feature_names', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('target_classes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_champion', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ml_models_active', 'ml_models', ['is_active', 'model_type'])
    op.create_index('idx_ml_models_symbol', 'ml_models', ['symbol', 'model_type'])
    op.create_index(op.f('ix_ml_models_id'), 'ml_models', ['id'])
    op.create_index(op.f('ix_ml_models_is_active'), 'ml_models', ['is_active'])
    op.create_index(op.f('ix_ml_models_symbol'), 'ml_models', ['symbol'])
    
    # ML Predictions table
    op.create_table(
        'ml_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('prediction', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('probabilities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('features_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('actual_outcome', sa.String(length=20), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('predicted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['ml_models.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ml_predictions_model', 'ml_predictions', ['model_id', 'predicted_at'])
    op.create_index('idx_ml_predictions_symbol_time', 'ml_predictions', ['symbol', 'predicted_at'])
    op.create_index(op.f('ix_ml_predictions_id'), 'ml_predictions', ['id'])
    op.create_index(op.f('ix_ml_predictions_model_id'), 'ml_predictions', ['model_id'])
    op.create_index(op.f('ix_ml_predictions_predicted_at'), 'ml_predictions', ['predicted_at'])
    op.create_index(op.f('ix_ml_predictions_symbol'), 'ml_predictions', ['symbol'])
    
    # ML Experiments table
    op.create_table(
        'ml_experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('artifact_location', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('experiment_id')
    )
    op.create_index(op.f('ix_ml_experiments_experiment_id'), 'ml_experiments', ['experiment_id'], unique=True)
    op.create_index(op.f('ix_ml_experiments_id'), 'ml_experiments', ['id'])
    
    # ML Features Cache table
    op.create_table(
        'ml_features',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('interval', sa.String(length=10), nullable=False),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('feature_count', sa.Integer(), nullable=True),
        sa.Column('data_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rows_count', sa.Integer(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ml_features_symbol_interval', 'ml_features', ['symbol', 'interval'])
    op.create_index(op.f('ix_ml_features_calculated_at'), 'ml_features', ['calculated_at'])
    op.create_index(op.f('ix_ml_features_id'), 'ml_features', ['id'])
    op.create_index(op.f('ix_ml_features_symbol'), 'ml_features', ['symbol'])


def downgrade():
    """Drop ML tables."""
    op.drop_table('ml_features')
    op.drop_table('ml_experiments')
    op.drop_table('ml_predictions')
    op.drop_table('ml_models')
