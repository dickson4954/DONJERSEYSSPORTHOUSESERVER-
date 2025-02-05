"""empty message

Revision ID: c8c063962bc0
Revises: 52b8b887d2a7
Create Date: 2025-02-02 16:52:13.678290

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8c063962bc0'
down_revision = '52b8b887d2a7'
branch_labels = None
depends_on = None


def upgrade():
    # Add size_type column as nullable
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('size_type', sa.String(length=50), nullable=True))

def downgrade():
    # Optionally, remove size_type column if downgrading
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_column('size_type')

    # ### end Alembic commands ###
