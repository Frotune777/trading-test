"""
Alembic migration: Add PKScreener tables

Revision ID: add_screener_tables
Revises: add_ml_tables
Create Date: 2026-01-09 22:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_screener_tables'
down_revision = 'add_ml_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create PKScreener tables."""
    
    # Custom Stock Lists table
    op.create_table(
        'custom_stock_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('stocks', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_custom_stock_lists_id'), 'custom_stock_lists', ['id'], unique=False)
    
    # PKScreener Results table
    op.create_table(
        'pkscreener_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.String(length=50), nullable=True),
        sa.Column('index_name', sa.String(length=50), nullable=True),
        sa.Column('strategy_name', sa.String(length=100), nullable=True),
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('scan_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pkscreener_results_id'), 'pkscreener_results', ['id'], unique=False)
    op.create_index(op.f('ix_pkscreener_results_scan_id'), 'pkscreener_results', ['scan_id'], unique=False)


def downgrade():
    """Drop PKScreener tables."""
    op.drop_index(op.f('ix_pkscreener_results_scan_id'), table_name='pkscreener_results')
    op.drop_index(op.f('ix_pkscreener_results_id'), table_name='pkscreener_results')
    op.drop_table('pkscreener_results')
    op.drop_index(op.f('ix_custom_stock_lists_id'), table_name='custom_stock_lists')
    op.drop_table('custom_stock_lists')
