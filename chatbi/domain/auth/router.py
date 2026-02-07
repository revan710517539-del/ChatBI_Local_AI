"""Auth Domain Router - API 端点"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from loguru import logger

from chatbi.dependencies import (
    AsyncSessionDep,
    RepositoryDependency,
    get_current_user,
)
from chatbi.domain.auth.dtos import (
    CreateUserDTO,
    LoginDTO,
    TokenResponse,
    UpdateUserDTO,
    UserDTO,
)
from chatbi.domain.auth.models import User
from chatbi.domain.auth.repository import (
    AsyncUserRepository,
    AsyncUserSessionRepository,
)
from chatbi.domain.auth.service import AuthService
from chatbi.exceptions import UnauthorizedError, ValidationError

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# 依赖注入
UserRepoDep = RepositoryDependency(AsyncUserRepository)
UserSessionRepoDep = RepositoryDependency(AsyncUserSessionRepository)


def get_auth_service(
    user_repo: AsyncUserRepository = Depends(UserRepoDep),
    session_repo: AsyncUserSessionRepository = Depends(UserSessionRepoDep),
) -> AuthService:
    """获取认证服务"""
    return AuthService(user_repo, session_repo)


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    credentials: LoginDTO, auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录接口

    **请求参数**:
    - username: 用户名
    - password: 密码

    **返回**:
    - access_token: 访问令牌（有效期 30 分钟）
    - refresh_token: 刷新令牌（有效期 7 天）
    - token_type: 令牌类型（bearer）
    - expires_in: 访问令牌有效期（秒）
    """
    try:
        token_pair = await auth_service.login(
            credentials.username, credentials.password
        )
        return TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
        )
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse, summary="刷新访问令牌")
async def refresh_token(
    refresh_token: str, auth_service: AuthService = Depends(get_auth_service)
):
    """
    刷新访问令牌接口

    **请求参数**:
    - refresh_token: 刷新令牌

    **返回**:
    - access_token: 新的访问令牌
    - refresh_token: 新的刷新令牌
    """
    try:
        token_pair = await auth_service.refresh_token(refresh_token)
        return TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
        )
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", summary="用户登出")
async def logout(
    authorization: str = Header(None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    用户登出接口（清除 Refresh Token）

    **请求头**:
    - Authorization: Bearer <refresh_token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header"
        )

    refresh_token = authorization.split(" ")[1]
    try:
        await auth_service.logout(refresh_token)
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )


@router.get("/me", response_model=UserDTO, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息

    **需要鉴权**: 是

    **返回**:
    - user_id: 用户 ID
    - username: 用户名
    - email: 邮箱
    - is_active: 是否激活
    - is_admin: 是否管理员
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    return UserDTO(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.post(
    "/users",
    response_model=UserDTO,
    summary="创建用户",
    dependencies=[Depends(get_current_user)],
)
async def create_user(
    dto: CreateUserDTO,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    创建用户（仅管理员）

    **需要鉴权**: 是（管理员）

    **请求参数**:
    - username: 用户名
    - email: 邮箱
    - password: 密码
    - is_admin: 是否管理员（默认 false）
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    try:
        user = await auth_service.create_user(dto)
        return UserDTO(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/users/{user_id}",
    response_model=UserDTO,
    summary="更新用户",
    dependencies=[Depends(get_current_user)],
)
async def update_user(
    user_id: str,
    dto: UpdateUserDTO,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    更新用户（管理员可更新任何用户，普通用户只能更新自己）

    **需要鉴权**: 是

    **请求参数**:
    - email: 邮箱（可选）
    - password: 密码（可选）
    - is_active: 是否激活（可选，仅管理员）
    - is_admin: 是否管理员（可选，仅管理员）
    """
    from uuid import UUID

    try:
        target_user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
        )

    # 权限检查：管理员可更新任何用户，普通用户只能更新自己
    if not current_user.is_admin and current_user.user_id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    # 非管理员不能修改 is_active 和 is_admin
    if not current_user.is_admin:
        if dto.is_active is not None or dto.is_admin is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required to modify user status",
            )

    try:
        user = await auth_service.update_user(target_user_id, dto)
        return UserDTO(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/users/{user_id}",
    summary="删除用户",
    dependencies=[Depends(get_current_user)],
)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    删除用户（仅管理员）

    **需要鉴权**: 是（管理员）
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    from uuid import UUID

    try:
        target_user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
        )

    # 不能删除自己
    if current_user.user_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    success = await auth_service.delete_user(target_user_id)
    if success:
        return {"message": "User deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
