from __future__ import annotations

import uuid
from typing import Annotated, Any

import httpx
import structlog
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, ReviewerOrAbove
from app.core.rate_limiter import limiter
from app.database import DbSession
from app.models.ai_system import AISystem
from app.models.model_card import ModelCard
from app.models.risk_assessment import RiskAssessment
from app.models.user import User
from app.schemas.model_card import ModelCardCreate, ModelCardList, ModelCardOut, ModelCardUpdate
from app.services import audit_logger
from app.services import model_card_generator as generator

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/model-cards", tags=["Model Cards"])


@router.get("/{system_id}", response_model=ModelCardList)
async def list_model_cards(
    system_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ModelCardList:
    result = await db.execute(
        select(ModelCard)
        .where(ModelCard.ai_system_id == system_id)
        .order_by(ModelCard.created_at.desc())
    )
    items = list(result.scalars().all())
    return ModelCardList(items=items, total=len(items))


@router.post("/{system_id}", response_model=ModelCardOut, status_code=status.HTTP_201_CREATED)
async def create_model_card(
    system_id: uuid.UUID,
    body: ModelCardCreate,
    db: DbSession,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
) -> ModelCard:
    system = await db.get(AISystem, system_id)
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Système IA introuvable")

    card = ModelCard(
        **body.model_dump(),
        ai_system_id=system_id,
        created_by=current_user.id,
    )
    db.add(card)
    await db.flush()

    await audit_logger.log_action(
        db,
        actor=current_user,
        action="model_card.created",
        resource_type="model_card",
        resource_id=card.id,
        input_payload={"system_id": str(system_id)},
    )
    log.info("model_card_created", card_id=str(card.id), system_id=str(system_id))
    return card


@router.patch("/{card_id}", response_model=ModelCardOut)
async def update_model_card(
    card_id: uuid.UUID,
    body: ModelCardUpdate,
    db: DbSession,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
) -> ModelCard:
    card = await db.get(ModelCard, card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model card introuvable")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(card, field, value)

    await db.flush()
    await audit_logger.log_action(
        db,
        actor=current_user,
        action="model_card.updated",
        resource_type="model_card",
        resource_id=card_id,
        input_payload=update_data,
    )
    return card


@router.post("/{card_id}/publish", response_model=ModelCardOut)
async def publish_model_card(
    card_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
) -> ModelCard:
    card = await db.get(ModelCard, card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model card introuvable")

    from app.models.model_card import ModelCardStatus

    card.status = ModelCardStatus.PUBLISHED
    card.reviewed_by = current_user.id
    await db.flush()

    await audit_logger.log_action(
        db,
        actor=current_user,
        action="model_card.published",
        resource_type="model_card",
        resource_id=card_id,
    )
    return card


@router.post("/{system_id}/generate", response_model=dict[str, Any])
@limiter.limit("5/minute")
async def generate_sections(
    request: Request,
    system_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
) -> dict[str, Any]:
    """Auto-génère les sections textuelles via OpenRouter LLM."""
    system = await db.get(AISystem, system_id)
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Système IA introuvable")

    # Récupère le dernier assessment
    result = await db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.ai_system_id == system_id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(1)
    )
    assessment = result.scalar_one_or_none()

    async with httpx.AsyncClient() as client:
        sections = await generator.generate_sections(client, system, assessment)

    if not sections:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Génération LLM indisponible. Vérifiez la clé OPENROUTER_API_KEY.",
        )

    return sections
