"""0001 initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-15 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums
    news_scope_enum = postgresql.ENUM('global', 'national', 'city', name='news_scope_enum')
    news_scope_enum.create(op.get_bind(), checkfirst=True)

    verdict_enum = postgresql.ENUM('TRUE', 'MISLEADING', 'SATIRE', 'FAKE', name='verdict_enum')
    verdict_enum.create(op.get_bind(), checkfirst=True)

    # 2. Create sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('rss_url', sa.String(length=1024), nullable=False, unique=True),
        sa.Column('default_scope', sa.Enum('global', 'national', 'city', name='news_scope_enum'), nullable=False),
        sa.Column('default_city_tag', sa.String(length=50), nullable=True),
        sa.Column('credibility_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('is_whitelisted', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 3. Create articles table
    op.create_table(
        'articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('summary_60_words', sa.Text(), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('image_url', sa.String(length=1024), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scope', sa.Enum('global', 'national', 'city', name='news_scope_enum'), nullable=False),
        sa.Column('city_tag', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_articles_url', 'articles', ['url'], unique=True)
    op.create_index('ix_articles_source_id', 'articles', ['source_id'])
    op.create_index('ix_articles_published_at', 'articles', ['published_at'])
    op.create_index('ix_articles_scope', 'articles', ['scope'])
    op.create_index('ix_articles_city_tag', 'articles', ['city_tag'])
    op.create_index('ix_articles_created_at', 'articles', ['created_at'])

    # 4. Create verification_dossiers table
    op.create_table(
        'verification_dossiers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('claim_hash', sa.String(length=64), nullable=False),
        sa.Column('verdict', sa.Enum('TRUE', 'MISLEADING', 'SATIRE', 'FAKE', name='verdict_enum'), nullable=False),
        sa.Column('truth_score', sa.Float(), nullable=False),
        sa.Column('explanation_bullets', sa.JSON(), nullable=False),
        sa.Column('evidence_sources', sa.JSON(), nullable=False),
        sa.Column('debunk_card_url', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_verification_dossiers_claim_hash', 'verification_dossiers', ['claim_hash'], unique=True)
    op.create_index('ix_verification_dossiers_verdict', 'verification_dossiers', ['verdict'])
    op.create_index('ix_verification_dossiers_created_at', 'verification_dossiers', ['created_at'])


def downgrade() -> None:
    op.drop_table('verification_dossiers')
    op.drop_table('articles')
    op.drop_table('sources')
    op.execute('DROP TYPE IF EXISTS verdict_enum')
    op.execute('DROP TYPE IF EXISTS news_scope_enum')
