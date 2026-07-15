from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.adapters.db.ai_system_repository import SqlAlchemyAISystemRepository
from app.adapters.db.audit_log_repository import SqlAlchemyAuditLogRepository
from app.adapters.db.model_card_repository import SqlAlchemyModelCardRepository
from app.adapters.db.pii_scan_repository import SqlAlchemyPIIScanRepository
from app.adapters.db.risk_assessment_repository import SqlAlchemyRiskAssessmentRepository
from app.adapters.db.user_repository import SqlAlchemyUserRepository
from app.adapters.http.openrouter_llm import OpenRouterLLM
from app.adapters.http.presidio_pii_scanner import PresidioPIIScanner
from app.application.use_cases.ai_system import (
    CreateAISystem,
    DeleteAISystem,
    GetAISystem,
    ListAISystems,
    UpdateAISystem,
)
from app.application.use_cases.audit_log import (
    GetResourceAuditLogs,
    ListAuditLogs,
    VerifyAuditLogIntegrity,
)
from app.application.use_cases.model_card import (
    CreateModelCard,
    GenerateModelCardSections,
    ListModelCards,
    PublishModelCard,
    UpdateModelCard,
)
from app.application.use_cases.pii_scan import GetPIIScan, ListPIIScans, ScanFile, ScanText
from app.application.use_cases.risk_assessment import (
    AssessRisk,
    GetQuestionnaire,
    ListRiskAssessments,
)
from app.application.use_cases.user import AuthenticateUser, CreateUser, UpdateUser
from app.database import DbSession
from app.domain.ai_system.ports import AISystemRepository
from app.domain.audit_log.ports import AuditLogPort
from app.domain.model_card.ports import LLMPort, ModelCardRepository
from app.domain.pii_scan.ports import PIIScannerPort, PIIScanRepository
from app.domain.risk_assessment.ports import RiskAssessmentRepository
from app.domain.user.ports import UserRepository


def get_audit_log_port(db: DbSession) -> AuditLogPort:
    return SqlAlchemyAuditLogRepository(db)


AuditLogPortDep = Annotated[AuditLogPort, Depends(get_audit_log_port)]


def get_list_audit_logs_use_case(audit_logs: AuditLogPortDep) -> ListAuditLogs:
    return ListAuditLogs(audit_logs)


ListAuditLogsDep = Annotated[ListAuditLogs, Depends(get_list_audit_logs_use_case)]


def get_resource_audit_logs_use_case(audit_logs: AuditLogPortDep) -> GetResourceAuditLogs:
    return GetResourceAuditLogs(audit_logs)


GetResourceAuditLogsDep = Annotated[GetResourceAuditLogs, Depends(get_resource_audit_logs_use_case)]


def get_verify_audit_log_integrity_use_case(
    audit_logs: AuditLogPortDep,
) -> VerifyAuditLogIntegrity:
    return VerifyAuditLogIntegrity(audit_logs)


VerifyAuditLogIntegrityDep = Annotated[
    VerifyAuditLogIntegrity, Depends(get_verify_audit_log_integrity_use_case)
]


def get_ai_system_repository(db: DbSession) -> AISystemRepository:
    return SqlAlchemyAISystemRepository(db)


AISystemRepositoryDep = Annotated[AISystemRepository, Depends(get_ai_system_repository)]


def get_risk_assessment_repository(db: DbSession) -> RiskAssessmentRepository:
    return SqlAlchemyRiskAssessmentRepository(db)


RiskAssessmentRepositoryDep = Annotated[
    RiskAssessmentRepository, Depends(get_risk_assessment_repository)
]


def get_questionnaire_use_case() -> GetQuestionnaire:
    return GetQuestionnaire()


GetQuestionnaireDep = Annotated[GetQuestionnaire, Depends(get_questionnaire_use_case)]


def get_assess_risk_use_case(
    ai_systems: AISystemRepositoryDep,
    risk_assessments: RiskAssessmentRepositoryDep,
    audit_logs: AuditLogPortDep,
) -> AssessRisk:
    return AssessRisk(ai_systems, risk_assessments, audit_logs)


AssessRiskDep = Annotated[AssessRisk, Depends(get_assess_risk_use_case)]


def get_list_risk_assessments_use_case(
    risk_assessments: RiskAssessmentRepositoryDep,
) -> ListRiskAssessments:
    return ListRiskAssessments(risk_assessments)


ListRiskAssessmentsDep = Annotated[ListRiskAssessments, Depends(get_list_risk_assessments_use_case)]


def get_create_ai_system_use_case(
    ai_systems: AISystemRepositoryDep, audit_logs: AuditLogPortDep
) -> CreateAISystem:
    return CreateAISystem(ai_systems, audit_logs)


CreateAISystemDep = Annotated[CreateAISystem, Depends(get_create_ai_system_use_case)]


def get_get_ai_system_use_case(ai_systems: AISystemRepositoryDep) -> GetAISystem:
    return GetAISystem(ai_systems)


GetAISystemDep = Annotated[GetAISystem, Depends(get_get_ai_system_use_case)]


def get_list_ai_systems_use_case(ai_systems: AISystemRepositoryDep) -> ListAISystems:
    return ListAISystems(ai_systems)


ListAISystemsDep = Annotated[ListAISystems, Depends(get_list_ai_systems_use_case)]


def get_update_ai_system_use_case(
    ai_systems: AISystemRepositoryDep, audit_logs: AuditLogPortDep
) -> UpdateAISystem:
    return UpdateAISystem(ai_systems, audit_logs)


UpdateAISystemDep = Annotated[UpdateAISystem, Depends(get_update_ai_system_use_case)]


def get_delete_ai_system_use_case(
    ai_systems: AISystemRepositoryDep, audit_logs: AuditLogPortDep
) -> DeleteAISystem:
    return DeleteAISystem(ai_systems, audit_logs)


DeleteAISystemDep = Annotated[DeleteAISystem, Depends(get_delete_ai_system_use_case)]


def get_pii_scan_repository(db: DbSession) -> PIIScanRepository:
    return SqlAlchemyPIIScanRepository(db)


PIIScanRepositoryDep = Annotated[PIIScanRepository, Depends(get_pii_scan_repository)]


def get_pii_scanner_port() -> PIIScannerPort:
    return PresidioPIIScanner()


PIIScannerPortDep = Annotated[PIIScannerPort, Depends(get_pii_scanner_port)]


def get_scan_text_use_case(
    pii_scans: PIIScanRepositoryDep, scanner: PIIScannerPortDep, audit_logs: AuditLogPortDep
) -> ScanText:
    return ScanText(pii_scans, scanner, audit_logs)


ScanTextDep = Annotated[ScanText, Depends(get_scan_text_use_case)]


def get_scan_file_use_case(
    pii_scans: PIIScanRepositoryDep, scanner: PIIScannerPortDep, audit_logs: AuditLogPortDep
) -> ScanFile:
    return ScanFile(pii_scans, scanner, audit_logs)


ScanFileDep = Annotated[ScanFile, Depends(get_scan_file_use_case)]


def get_list_pii_scans_use_case(pii_scans: PIIScanRepositoryDep) -> ListPIIScans:
    return ListPIIScans(pii_scans)


ListPIIScansDep = Annotated[ListPIIScans, Depends(get_list_pii_scans_use_case)]


def get_get_pii_scan_use_case(pii_scans: PIIScanRepositoryDep) -> GetPIIScan:
    return GetPIIScan(pii_scans)


GetPIIScanDep = Annotated[GetPIIScan, Depends(get_get_pii_scan_use_case)]


def get_user_repository(db: DbSession) -> UserRepository:
    return SqlAlchemyUserRepository(db)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_authenticate_user_use_case(users: UserRepositoryDep) -> AuthenticateUser:
    return AuthenticateUser(users)


AuthenticateUserDep = Annotated[AuthenticateUser, Depends(get_authenticate_user_use_case)]


def get_create_user_use_case(users: UserRepositoryDep, audit_logs: AuditLogPortDep) -> CreateUser:
    return CreateUser(users, audit_logs)


CreateUserDep = Annotated[CreateUser, Depends(get_create_user_use_case)]


def get_update_user_use_case(users: UserRepositoryDep, audit_logs: AuditLogPortDep) -> UpdateUser:
    return UpdateUser(users, audit_logs)


UpdateUserDep = Annotated[UpdateUser, Depends(get_update_user_use_case)]


def get_model_card_repository(db: DbSession) -> ModelCardRepository:
    return SqlAlchemyModelCardRepository(db)


ModelCardRepositoryDep = Annotated[ModelCardRepository, Depends(get_model_card_repository)]


def get_llm_port() -> LLMPort:
    return OpenRouterLLM()


LLMPortDep = Annotated[LLMPort, Depends(get_llm_port)]


def get_create_model_card_use_case(
    model_cards: ModelCardRepositoryDep,
    ai_systems: AISystemRepositoryDep,
    audit_logs: AuditLogPortDep,
) -> CreateModelCard:
    return CreateModelCard(model_cards, ai_systems, audit_logs)


CreateModelCardDep = Annotated[CreateModelCard, Depends(get_create_model_card_use_case)]


def get_list_model_cards_use_case(model_cards: ModelCardRepositoryDep) -> ListModelCards:
    return ListModelCards(model_cards)


ListModelCardsDep = Annotated[ListModelCards, Depends(get_list_model_cards_use_case)]


def get_update_model_card_use_case(
    model_cards: ModelCardRepositoryDep, audit_logs: AuditLogPortDep
) -> UpdateModelCard:
    return UpdateModelCard(model_cards, audit_logs)


UpdateModelCardDep = Annotated[UpdateModelCard, Depends(get_update_model_card_use_case)]


def get_publish_model_card_use_case(
    model_cards: ModelCardRepositoryDep, audit_logs: AuditLogPortDep
) -> PublishModelCard:
    return PublishModelCard(model_cards, audit_logs)


PublishModelCardDep = Annotated[PublishModelCard, Depends(get_publish_model_card_use_case)]


def get_generate_model_card_sections_use_case(
    ai_systems: AISystemRepositoryDep,
    risk_assessments: RiskAssessmentRepositoryDep,
    llm: LLMPortDep,
) -> GenerateModelCardSections:
    return GenerateModelCardSections(ai_systems, risk_assessments, llm)


GenerateModelCardSectionsDep = Annotated[
    GenerateModelCardSections, Depends(get_generate_model_card_sections_use_case)
]
