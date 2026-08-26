"""v0.2 evidence audit notifications
Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa
revision='0002'; down_revision='0001'; branch_labels=None; depends_on=None

def upgrade():
    evidence_entity=sa.Enum('INSPECTION','NCR','PUNCH',name='evidenceentity'); evidence_entity.create(op.get_bind(),checkfirst=True)
    op.create_table('evidence',sa.Column('id',sa.String(36),primary_key=True),sa.Column('organization_id',sa.String(36),nullable=False,index=True),sa.Column('project_id',sa.String(36),sa.ForeignKey('projects.id',ondelete='CASCADE'),nullable=False),sa.Column('entity_type',evidence_entity,nullable=False),sa.Column('entity_id',sa.String(36),nullable=False),sa.Column('file_name',sa.String(255),nullable=False),sa.Column('stored_name',sa.String(255),nullable=False,unique=True),sa.Column('content_type',sa.String(120)),sa.Column('size_bytes',sa.Integer(),nullable=False,server_default='0'),sa.Column('uploaded_by',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('audit_logs',sa.Column('id',sa.String(36),primary_key=True),sa.Column('organization_id',sa.String(36),nullable=False),sa.Column('actor_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('action',sa.String(80),nullable=False),sa.Column('entity_type',sa.String(80),nullable=False),sa.Column('entity_id',sa.String(36),nullable=False),sa.Column('summary',sa.String(500),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('notifications',sa.Column('id',sa.String(36),primary_key=True),sa.Column('organization_id',sa.String(36),nullable=False),sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('title',sa.String(160),nullable=False),sa.Column('message',sa.String(500),nullable=False),sa.Column('entity_type',sa.String(80)),sa.Column('entity_id',sa.String(36)),sa.Column('is_read',sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))

def downgrade():
    op.drop_table('notifications');op.drop_table('audit_logs');op.drop_table('evidence');sa.Enum(name='evidenceentity').drop(op.get_bind(),checkfirst=True)
