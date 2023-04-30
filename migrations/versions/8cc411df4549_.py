"""empty message

Revision ID: 8cc411df4549
Revises: 3af601e14526
Create Date: 2023-04-30 15:34:57.666166

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8cc411df4549"
down_revision = "3af601e14526"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("signals", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_spot", sa.Boolean(), nullable=False))

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("api_secret", sa.String(length=100), nullable=True)
        )
        batch_op.alter_column(
            "api_key",
            existing_type=sa.VARCHAR(length=160),
            type_=sa.String(length=100),
            existing_nullable=True,
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "api_key",
            existing_type=sa.String(length=100),
            type_=sa.VARCHAR(length=160),
            existing_nullable=True,
        )
        batch_op.drop_column("api_secret")

    with op.batch_alter_table("signals", schema=None) as batch_op:
        batch_op.drop_column("is_spot")

    # ### end Alembic commands ###
