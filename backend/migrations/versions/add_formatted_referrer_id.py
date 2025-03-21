"""Add formatted_referrer_id column

Revision ID: add_formatted_referrer_id
Revises: 
Create Date: 2025-03-15

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add new column
    op.add_column('referral_tree', sa.Column('formatted_referrer_id', sa.String(50), nullable=True))
    
    # Update the new column with formatted values based on referrer_id
    op.execute("""
    UPDATE referral_tree 
    SET formatted_referrer_id = CONCAT('AL', LPAD(referrer_id, 7, '0'))
    WHERE referrer_id IS NOT NULL
    """)

def downgrade():
    # Remove the column if needed
    op.drop_column('referral_tree', 'formatted_referrer_id')