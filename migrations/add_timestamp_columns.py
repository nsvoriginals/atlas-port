"""add timestamp columns

Revision ID: add_timestamp_columns
Revises: 
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = 'add_timestamp_columns'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add created_at and updated_at columns to resumes table
    op.add_column('resumes', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()))
    op.add_column('resumes', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now()))

def downgrade():
    # Remove the columns if needed to rollback
    op.drop_column('resumes', 'updated_at')
    op.drop_column('resumes', 'created_at') 