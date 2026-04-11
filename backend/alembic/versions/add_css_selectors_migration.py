"""Add CSS selector fields to sources table for generic website scraping

Revision ID: add_css_selectors
Revises: a1b2c3d4e5f6
Create Date: 2026-04-10 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_css_selectors'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add CSS selector columns to sources table"""
    # Add new columns for CSS selectors
    op.add_column('sources', sa.Column('post_selector', sa.String(), nullable=True))
    op.add_column('sources', sa.Column('content_selector', sa.String(), nullable=True))
    op.add_column('sources', sa.Column('title_selector', sa.String(), nullable=True))
    op.add_column('sources', sa.Column('author_selector', sa.String(), nullable=True))
    op.add_column('sources', sa.Column('date_selector', sa.String(), nullable=True))
    op.add_column('sources', sa.Column('link_selector', sa.String(), nullable=True))
    op.add_column('sources', sa.Column('image_selector', sa.String(), nullable=True))
    op.add_column('sources', sa.Column('selectors_validated', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Remove CSS selector columns from sources table"""
    op.drop_column('sources', 'selectors_validated')
    op.drop_column('sources', 'image_selector')
    op.drop_column('sources', 'link_selector')
    op.drop_column('sources', 'date_selector')
    op.drop_column('sources', 'author_selector')
    op.drop_column('sources', 'title_selector')
    op.drop_column('sources', 'content_selector')
    op.drop_column('sources', 'post_selector')
