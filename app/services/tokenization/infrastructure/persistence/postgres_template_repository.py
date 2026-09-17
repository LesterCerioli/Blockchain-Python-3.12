from datetime import datetime, timezone

from sqlalchemy import select, update, func

from app.services.tokenization.domain.entities.business_rule import BusinessRule
from app.services.tokenization.domain.entities.template import Template
from app.services.tokenization.domain.entities.template_characteristics import TemplateCharacteristics
from app.services.tokenization.domain.entities.template_metadata import TemplateMetadata
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.entities.template_version import TemplateVersion
from app.services.tokenization.domain.entities.token_model import TokenModel
from app.services.tokenization.domain.interfaces.template_repository import ITemplateRepository
from app.services.tokenization.infrastructure.persistence.database import TokenizationDatabase
from app.services.tokenization.infrastructure.persistence.models import TokenizationTemplateModel


class PostgresTemplateRepository(ITemplateRepository):
    """PostgreSQL template repository using SQLAlchemy 2.0 async."""

    def __init__(self, database: TokenizationDatabase) -> None:
        self._db = database

    def _row_to_entity(self, row: TokenizationTemplateModel) -> Template:
        return Template(
            template_id=str(row.id),
            name=row.name,
            description=row.description,
            category=row.category,
            strategy=row.strategy,
            token_standard=row.token_standard,
            status=TemplateStatus(row.status),
            version=TemplateVersion(
                major=row.version_major,
                minor=row.version_minor,
                patch=row.version_patch,
            ),
            metadata=TemplateMetadata(**(row.metadata or {})),
            characteristics=TemplateCharacteristics(**(row.characteristics or {})),
            token_model=TokenModel(**(row.token_model or {})),
            business_rules=[BusinessRule(**r) for r in (row.business_rules or [])],
            created_at=row.created_at.isoformat() if row.created_at else "",
            updated_at=row.updated_at.isoformat() if row.updated_at else "",
            created_by=row.created_by,
            approved_by=row.approved_by,
            approved_at=row.approved_at.isoformat() if row.approved_at else None,
        )

    async def get_by_id(self, template_id: str) -> Template | None:
        async with self._db.session() as session:
            result = await session.execute(
                select(TokenizationTemplateModel).where(
                    TokenizationTemplateModel.id == template_id
                )
            )
            row = result.scalar_one_or_none()
            return self._row_to_entity(row) if row else None

    async def get_by_name(self, name: str) -> Template | None:
        async with self._db.session() as session:
            result = await session.execute(
                select(TokenizationTemplateModel).where(
                    func.lower(TokenizationTemplateModel.name) == name.lower()
                )
            )
            row = result.scalar_one_or_none()
            return self._row_to_entity(row) if row else None

    async def create(self, template: Template) -> None:
        async with self._db.session() as session:
            model = TokenizationTemplateModel(
                id=template.template_id,
                name=template.name,
                description=template.description,
                category=template.category,
                strategy=template.strategy,
                token_standard=template.token_standard,
                status=template.status.value,
                version_major=template.version.major,
                version_minor=template.version.minor,
                version_patch=template.version.patch,
                metadata=template.metadata.model_dump(),
                characteristics=template.characteristics.model_dump(),
                token_model=template.token_model.model_dump(),
                business_rules=[r.model_dump() for r in template.business_rules],
                created_by=template.created_by,
                approved_by=template.approved_by,
                approved_at=datetime.fromisoformat(template.approved_at) if template.approved_at else None,
                created_at=datetime.fromisoformat(template.created_at),
                updated_at=datetime.fromisoformat(template.updated_at),
            )
            session.add(model)

    async def update(self, template: Template) -> None:
        async with self._db.session() as session:
            await session.execute(
                update(TokenizationTemplateModel)
                .where(TokenizationTemplateModel.name == template.name)
                .values(
                    description=template.description,
                    category=template.category,
                    strategy=template.strategy,
                    token_standard=template.token_standard,
                    status=template.status.value,
                    version_major=template.version.major,
                    version_minor=template.version.minor,
                    version_patch=template.version.patch,
                    metadata=template.metadata.model_dump(),
                    characteristics=template.characteristics.model_dump(),
                    token_model=template.token_model.model_dump(),
                    business_rules=[r.model_dump() for r in template.business_rules],
                    approved_by=template.approved_by,
                    approved_at=datetime.fromisoformat(template.approved_at) if template.approved_at else None,
                    updated_at=datetime.now(timezone.utc),
                )
            )

    async def delete(self, template_id: str) -> None:
        async with self._db.session() as session:
            await session.execute(
                select(TokenizationTemplateModel).where(
                    TokenizationTemplateModel.id == template_id
                )
            )

    async def list_all(self) -> list[Template]:
        async with self._db.session() as session:
            result = await session.execute(select(TokenizationTemplateModel))
            return [self._row_to_entity(row) for row in result.scalars().all()]

    async def list_by_status(self, status: TemplateStatus) -> list[Template]:
        async with self._db.session() as session:
            result = await session.execute(
                select(TokenizationTemplateModel).where(
                    TokenizationTemplateModel.status == status.value
                )
            )
            return [self._row_to_entity(row) for row in result.scalars().all()]

    async def list_by_category(self, category: str) -> list[Template]:
        async with self._db.session() as session:
            result = await session.execute(
                select(TokenizationTemplateModel).where(
                    func.lower(TokenizationTemplateModel.category) == category.lower()
                )
            )
            return [self._row_to_entity(row) for row in result.scalars().all()]

    async def list_by_strategy(self, strategy: str) -> list[Template]:
        async with self._db.session() as session:
            result = await session.execute(
                select(TokenizationTemplateModel).where(
                    func.lower(TokenizationTemplateModel.strategy) == strategy.lower()
                )
            )
            return [self._row_to_entity(row) for row in result.scalars().all()]

    async def list_by_token_standard(self, standard: str) -> list[Template]:
        async with self._db.session() as session:
            result = await session.execute(
                select(TokenizationTemplateModel).where(
                    func.upper(TokenizationTemplateModel.token_standard) == standard.upper()
                )
            )
            return [self._row_to_entity(row) for row in result.scalars().all()]

    async def search(
        self,
        query: str | None = None,
        category: str | None = None,
        strategy: str | None = None,
        token_standard: str | None = None,
        status: TemplateStatus | None = None,
        tags: list[str] | None = None,
        industry: str | None = None,
    ) -> list[Template]:
        async with self._db.session() as session:
            stmt = select(TokenizationTemplateModel)

            if query is not None:
                q = f"%{query.lower()}%"
                stmt = stmt.where(
                    func.lower(TokenizationTemplateModel.name).like(q)
                    | func.lower(TokenizationTemplateModel.description).like(q)
                    | func.lower(TokenizationTemplateModel.category).like(q)
                    | func.lower(TokenizationTemplateModel.strategy).like(q)
                )

            if category is not None:
                stmt = stmt.where(
                    func.lower(TokenizationTemplateModel.category) == category.lower()
                )

            if strategy is not None:
                stmt = stmt.where(
                    func.lower(TokenizationTemplateModel.strategy) == strategy.lower()
                )

            if token_standard is not None:
                stmt = stmt.where(
                    func.upper(TokenizationTemplateModel.token_standard) == token_standard.upper()
                )

            if status is not None:
                stmt = stmt.where(
                    TokenizationTemplateModel.status == status.value
                )

            result = await session.execute(stmt)
            templates = [self._row_to_entity(row) for row in result.scalars().all()]

            if tags is not None:
                tag_set = {t.lower() for t in tags}
                templates = [
                    t for t in templates
                    if tag_set & {tag.lower() for tag in t.metadata.tags}
                ]

            if industry is not None:
                templates = [
                    t for t in templates
                    if t.characteristics.industry.lower() == industry.lower()
                ]

            return templates

    async def count(self) -> int:
        async with self._db.session() as session:
            result = await session.execute(select(func.count()))
            return result.scalar()
