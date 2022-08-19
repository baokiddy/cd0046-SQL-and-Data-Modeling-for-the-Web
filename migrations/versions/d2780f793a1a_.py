"""empty message

Revision ID: d2780f793a1a
Revises: f5d30cc35c13
Create Date: 2022-08-16 21:25:52.456993

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2780f793a1a'
down_revision = 'f5d30cc35c13'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('website_link', sa.String(length=500), nullable=True))
    op.add_column('Venue', sa.Column('website_link', sa.String(length=500), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'website_link')
    op.drop_column('Artist', 'website_link')
    # ### end Alembic commands ###
