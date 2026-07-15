import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Request, status

from app.composition import (
    CreateModelCardDep,
    GenerateModelCardSectionsDep,
    ListModelCardsDep,
    PublishModelCardDep,
    UpdateModelCardDep,
)
from app.core.dependencies import CurrentUser, ReviewerOrAbove
from app.core.rate_limiter import limiter
from app.models.model_card import ModelCard
from app.models.user import User
from app.schemas.model_card import ModelCardCreate, ModelCardList, ModelCardOut, ModelCardUpdate

router = APIRouter(prefix="/model-cards", tags=["Model Cards"])


@router.get("/{system_id}", response_model=ModelCardList)
async def list_model_cards(
    system_id: uuid.UUID,
    current_user: CurrentUser,
    use_case: ListModelCardsDep,
) -> ModelCardList:
    items, total = await use_case.execute(system_id)
    return ModelCardList(items=[ModelCardOut.model_validate(i) for i in items], total=total)


@router.post("/{system_id}", response_model=ModelCardOut, status_code=status.HTTP_201_CREATED)
async def create_model_card(
    system_id: uuid.UUID,
    body: ModelCardCreate,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
    use_case: CreateModelCardDep,
) -> ModelCard:
    return await use_case.execute(system_id, body.model_dump(), actor=current_user)


@router.patch("/{card_id}", response_model=ModelCardOut)
async def update_model_card(
    card_id: uuid.UUID,
    body: ModelCardUpdate,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
    use_case: UpdateModelCardDep,
) -> ModelCard:
    return await use_case.execute(card_id, body.model_dump(exclude_none=True), actor=current_user)


@router.post("/{card_id}/publish", response_model=ModelCardOut)
async def publish_model_card(
    card_id: uuid.UUID,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
    use_case: PublishModelCardDep,
) -> ModelCard:
    return await use_case.execute(card_id, actor=current_user)


@router.post("/{system_id}/generate", response_model=dict[str, Any])
@limiter.limit("5/minute")
async def generate_sections(
    request: Request,
    system_id: uuid.UUID,
    current_user: CurrentUser,
    _reviewer: Annotated[User, ReviewerOrAbove],
    use_case: GenerateModelCardSectionsDep,
) -> dict[str, str]:
    return await use_case.execute(system_id)
