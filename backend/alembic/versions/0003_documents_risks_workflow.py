"""v0.3 documents risks workflow
Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa
revision='0003';down_revision='0002';branch_labels=None;depends_on=None

def upgrade():
    doc_status=sa.Enum('DRAFT','IN_REVIEW','APPROVED','REJECTED',name='documentstatus');doc_status.create(op.get_bind(),checkfirst=True)
    risk_status=sa.Enum('OPEN','MITIGATION','CLOSED',name='riskstatus');risk_status.create(op.get_bind(),checkfirst=True)
    wf_entity=sa.Enum('DOCUMENT','RISK',name='workflowentity');wf_entity.create(op.get_bind(),checkfirst=True)
    op.create_table('documents',sa.Column('id',sa.String(36),primary_key=True),sa.Column('organization_id',sa.String(36),nullable=False,index=True),sa.Column('project_id',sa.String(36),sa.ForeignKey('projects.id',ondelete='CASCADE'),nullable=False),sa.Column('document_no',sa.String(100),nullable=False),sa.Column('title',sa.String(255),nullable=False),sa.Column('discipline',sa.String(80),nullable=False),sa.Column('revision',sa.String(20),nullable=False),sa.Column('status',doc_status,nullable=False),sa.Column('created_by',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint('organization_id','document_no','revision',name='uq_document_revision'))
    op.create_table('risks',sa.Column('id',sa.String(36),primary_key=True),sa.Column('organization_id',sa.String(36),nullable=False,index=True),sa.Column('project_id',sa.String(36),sa.ForeignKey('projects.id',ondelete='CASCADE'),nullable=False),sa.Column('title',sa.String(255),nullable=False),sa.Column('category',sa.String(80),nullable=False),sa.Column('probability',sa.Integer(),nullable=False),sa.Column('impact',sa.Integer(),nullable=False),sa.Column('score',sa.Integer(),nullable=False),sa.Column('mitigation',sa.Text()),sa.Column('owner',sa.String(160)),sa.Column('status',risk_status,nullable=False),sa.Column('created_by',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('closed_at',sa.DateTime(timezone=True)))
    op.create_table('workflow_events',sa.Column('id',sa.String(36),primary_key=True),sa.Column('organization_id',sa.String(36),nullable=False,index=True),sa.Column('entity_type',wf_entity,nullable=False),sa.Column('entity_id',sa.String(36),nullable=False),sa.Column('from_status',sa.String(80),nullable=False),sa.Column('to_status',sa.String(80),nullable=False),sa.Column('comment',sa.String(500)),sa.Column('actor_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))

def downgrade():
    op.drop_table('workflow_events');op.drop_table('risks');op.drop_table('documents');sa.Enum(name='workflowentity').drop(op.get_bind(),checkfirst=True);sa.Enum(name='riskstatus').drop(op.get_bind(),checkfirst=True);sa.Enum(name='documentstatus').drop(op.get_bind(),checkfirst=True)
