"""empty message

Revision ID: b0813338cfb9
Revises: 
Create Date: 2023-04-27 10:07:26.390377

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b0813338cfb9"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "roles",
                sa.Enum("USER", "PROVIDER", "REGISTRAR", name="roles"),
                server_default="USER",
                nullable=False,
            )
        )
        batch_op.create_unique_constraint(None, ["id"])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="unique")
        batch_op.drop_column("roles")

    # ### end Alembic commands ###