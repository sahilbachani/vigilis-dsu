"""Add AI analysis columns to posts table

Revision ID: a1b2c3d4e5f6
Revises: e8420b4121fb
Create Date: 2026-03-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e8420b4121fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add AI analysis columns to posts table."""
    # Add AI analysis score columns
    op.add_column('posts', sa.Column('hate_score', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('posts', sa.Column('extremism_score', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('posts', sa.Column('misinformation_score', sa.Float(), nullable=True, server_default='0.0'))
    
    # Add emotion detection columns
    op.add_column('posts', sa.Column('emotion_anger', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('posts', sa.Column('emotion_fear', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('posts', sa.Column('emotion_disgust', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('posts', sa.Column('emotion_neutral', sa.Float(), nullable=True, server_default='1.0'))
    
    # Add processing status columns
    op.add_column('posts', sa.Column('ai_processed', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('posts', sa.Column('analysis_timestamp', sa.DateTime(), nullable=True))
    
    # Update existing column defaults
    op.alter_column('posts', 'confidence_score', new_column_name='confidence_score',
                    existing_type=sa.Float(), server_default='0.0')


def downgrade() -> None:
    """Remove AI analysis columns from posts table."""
    # Remove analysis columns
    op.drop_column('posts', 'analysis_timestamp')
    op.drop_column('posts', 'ai_processed')
    op.drop_column('posts', 'emotion_neutral')
    op.drop_column('posts', 'emotion_disgust')
    op.drop_column('posts', 'emotion_fear')
    op.drop_column('posts', 'emotion_anger')
    op.drop_column('posts', 'misinformation_score')
    op.drop_column('posts', 'extremism_score')
    op.drop_column('posts', 'hate_score')
