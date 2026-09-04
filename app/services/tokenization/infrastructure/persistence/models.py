from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TokenizationTemplateModel(Base):
    __tablename__ = "tokenization_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True)
    strategy = Column(String(64), nullable=False, index=True)
    token_standard = Column(String(16), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    version_major = Column(Integer, nullable=False, default=1)
    version_minor = Column(Integer, nullable=False, default=0)
    version_patch = Column(Integer, nullable=False, default=0)
    metadata = Column(JSON, nullable=True, server_default="{}")
    characteristics = Column(JSON, nullable=True, server_default="{}")
    token_model = Column(JSON, nullable=True, server_default="{}")
    business_rules = Column(JSON, nullable=True, server_default="[]")
    created_by = Column(String(128), nullable=False, default="system")
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
