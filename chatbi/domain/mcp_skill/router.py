from __future__ import annotations

from fastapi import APIRouter, Query

from chatbi.domain.mcp_skill.dtos import (
    EmailConfigUpdateDTO,
    MCPServerCreateDTO,
    MCPServerUpdateDTO,
    SkillCreateDTO,
    SkillUpdateDTO,
    StrategyApprovalDTO,
    StrategyGenerateDTO,
    StrategyRefineDTO,
)
from chatbi.domain.mcp_skill.service import MCPSkillService
from chatbi.middleware.standard_response import StandardResponse

router = APIRouter(prefix="/api/v1/mcp-skill", tags=["MCP & Skills"])


@router.get("/mcp-servers")
async def list_mcp_servers() -> StandardResponse[list[dict]]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="MCP servers fetched", data=service.list_mcp_servers())


@router.post("/mcp-servers")
async def create_mcp_server(payload: MCPServerCreateDTO) -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="MCP server created", data=service.create_mcp_server(payload))


@router.put("/mcp-servers/{server_id}")
async def update_mcp_server(server_id: str, payload: MCPServerUpdateDTO) -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="MCP server updated", data=service.update_mcp_server(server_id, payload))


@router.delete("/mcp-servers/{server_id}")
async def delete_mcp_server(server_id: str) -> StandardResponse[dict]:
    service = MCPSkillService()
    service.delete_mcp_server(server_id)
    return StandardResponse(status="success", message="MCP server deleted", data={"id": server_id})


@router.get("/skills")
async def list_skills() -> StandardResponse[list[dict]]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="Skills fetched", data=service.list_skills())


@router.post("/skills")
async def create_skill(payload: SkillCreateDTO) -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="Skill created", data=service.create_skill(payload))


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: str, payload: SkillUpdateDTO) -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="Skill updated", data=service.update_skill(skill_id, payload))


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str) -> StandardResponse[dict]:
    service = MCPSkillService()
    service.delete_skill(skill_id)
    return StandardResponse(status="success", message="Skill deleted", data={"id": skill_id})


@router.get("/email-config")
async def get_email_config() -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="Email config fetched", data=service.get_email_config())


@router.put("/email-config")
async def update_email_config(payload: EmailConfigUpdateDTO) -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="Email config updated", data=service.update_email_config(payload))


@router.get("/strategies")
async def list_strategies(limit: int = Query(100, ge=1, le=500)) -> StandardResponse[list[dict]]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="Strategies fetched", data=service.list_strategies(limit=limit))


@router.post("/strategies/generate")
async def generate_strategy(payload: StrategyGenerateDTO) -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="Strategy generated", data=service.generate_strategy(payload))


@router.post("/strategies/{strategy_id}/send-email")
async def send_strategy_email(strategy_id: str) -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="Strategy email send triggered", data=service.send_strategy_email(strategy_id))


@router.post("/strategies/{strategy_id}/approve")
async def approve_strategy(strategy_id: str, payload: StrategyApprovalDTO) -> StandardResponse[dict]:
    service = MCPSkillService()
    approved = service.approve_strategy(strategy_id, payload.reply_text)
    if payload.execute and approved.get("approval", {}).get("reply_status") == "approved":
        approved = service.execute_strategy(strategy_id)
    return StandardResponse(status="success", message="Strategy approval handled", data=approved)


@router.post("/strategies/{strategy_id}/execute")
async def execute_strategy(strategy_id: str) -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(status="success", message="Strategy executed", data=service.execute_strategy(strategy_id))


@router.post("/strategies/{strategy_id}/refine")
async def refine_strategy(strategy_id: str, payload: StrategyRefineDTO) -> StandardResponse[dict]:
    service = MCPSkillService()
    return StandardResponse(
        status="success",
        message="Strategy refined with human-AI discussion",
        data=service.refine_strategy(
            strategy_id=strategy_id,
            discussion=payload.discussion,
            operator=payload.operator,
        ),
    )
