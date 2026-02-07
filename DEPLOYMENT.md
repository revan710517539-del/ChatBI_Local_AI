# ChatBI 部署指南

## 本地开发指南

### 开发环境要求

**必须本地安装**:
- **Python**: 3.11+ （后端服务）
- **Node.js**: 22+ （前端服务）
- **Docker**: 20.10+ 和 Docker Compose 2.0+ （中间件容器）
- **包管理器**: 
  - uv (Python依赖管理)
  - pnpm (Node.js依赖管理)

**通过 Docker Compose 运行**（无需本地安装）:
- PostgreSQL 14+ （应用数据库）
- Redis 7+ （缓存）
- Qdrant 1.12+ （向量数据库，用于 MDL 语义层）
- Cube.js （OLAP 引擎）

### 一键启动开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/chatbi.git
cd chatbi

# 2. 安装开发工具（Python + Node.js + Docker）
# macOS
brew install uv node@22

# Linux - 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Linux - 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证 Docker 已安装
docker --version
docker compose version

# 3. 运行开发环境初始化
make install        # 或 just install

# 4. 启动所有中间件（Docker Compose）
make docker up      # 或 just docker up
# 这将启动: PostgreSQL, Redis, Qdrant, Cube.js 及其依赖

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 设置 LLM_API_KEY

# 6. 运行数据库迁移
uv run python -m chatbi.migrations.manage_migrations upgrade

# 7. 启动开发服务器
# 终端1: 启动后端
make dev-server     # 或 just dev-server

# 终端2: 启动前端
make dev-client     # 或 just dev-client
```

访问：
- **前端开发服务器**: http://localhost:8001 （本地 Node.js）
- **后端API**: http://localhost:8000 （本地 Python）
- **API文档**: http://localhost:8000/docs
- **PostgreSQL** (Docker): localhost:15432 (chatbi/12345)
- **Redis** (Docker): localhost:16379
- **Qdrant** (Docker): localhost:6333 (HTTP), localhost:6334 (gRPC)
- **Cube.js** (Docker): localhost:4000

---

### 详细开发流程

#### 步骤 1: 安装依赖

**Python依赖（后端）**:
```bash
# 使用 uv 安装（推荐，比 pip 快 10-100 倍）
uv sync

# 或使用 Makefile
make install-python
```

**Node.js依赖（前端）**:
```bash
# 使用 pnpm
pnpm install

# 或使用 Makefile
make install-client
```

#### 步骤 2: 启动基础设施（全部在 Docker 中）

```bash
# 启动所有中间件容器
cd docker
docker compose up -d

# 检查所有服务状态
docker compose ps

# 查看特定服务日志
docker compose logs -f postgres   # PostgreSQL
docker compose logs -f redis      # Redis
docker compose logs -f qdrant     # Qdrant 向量数据库
docker compose logs -f cube_api   # Cube.js
```

**容器服务端口映射** (宿主机 → 容器)：
- **PostgreSQL**: `localhost:15432` → 5432
- **Redis**: `localhost:16379` → 6379
- **Qdrant HTTP**: `localhost:6333` → 6333
- **Qdrant gRPC**: `localhost:6334` → 6334
- **Cube.js API**: `localhost:4000` → 4000

**说明**: 所有中间件都在 Docker 容器中运行，无需本地安装。前后端服务直接连接到 `localhost` 的映射端口。

#### 步骤 3: 数据库初始化

```bash
# 自动创建数据库和表结构
uv run python -m chatbi.migrations.manage_migrations upgrade

# 查看迁移状态
uv run python -m chatbi.migrations.manage_migrations status

# 创建新迁移
uv run python -m chatbi.migrations.manage_migrations create "add new feature"
```

**手动初始化（可选）**:
```bash
# 方式1: 通过宿主机连接（需要本地安装 psql 客户端）
psql -h localhost -p 15432 -U chatbi -d chatbi

# 方式2: 通过 Docker 容器连接（推荐，无需本地安装）
docker compose -f docker/compose.yml exec postgres psql -U chatbi -d chatbi

# 导入初始数据
\i setup_db.sql
```

#### 步骤 4: 运行开发服务器

**后端（FastAPI）**:
```bash
# 方式1: 使用 Makefile（推荐）
make dev-server

# 方式2: 直接运行
uv run uvicorn chatbi.main:app --reload --host 0.0.0.0 --port 8000

# 方式3: 使用 just
just dev-server
```

FastAPI 特性：
- 🔥 热重载：修改代码自动重启
- 📚 自动文档：http://localhost:8000/docs
- 🐛 调试模式：详细错误堆栈

**前端（Umi.js + React）**:
```bash
# 方式1: 使用 Makefile
make dev-client

# 方式2: 直接运行
cd web
pnpm dev

# 方式3: 使用 just
just dev-client
```

前端特性：
- ⚡️ HMR：热模块替换，修改立即生效
- 🎨 Ant Design X：企业级UI组件
- 📊 AVA：智能图表库

#### 步骤 5: 生成前端 API 类型

```bash
# 从 FastAPI OpenAPI 生成 TypeScript 类型
make gen-api        # 或 just gen-api

# 生成的文件位置：web/src/services/openapi/
```

**何时需要重新生成**：
- 添加/修改 API 路由
- 更改 Pydantic 模型
- 修改请求/响应结构

---

### 常用开发命令

#### Makefile 命令（推荐）

```bash
# 安装所有依赖
make install

# 启动开发环境
make dev            # 同时启动前后端

# 运行测试
make test           # Python 测试
make test-client    # 前端测试

# 代码检查
make lint           # Ruff + ESLint
make format         # 自动格式化

# 数据库操作
make migrate        # 运行迁移
make db-reset       # 重置数据库（危险！）

# 清理
make clean          # 清理缓存和构建产物
```

#### Just 命令（替代方案）

```bash
# 列出所有命令
just --list

# 开发常用
just install
just dev
just test
just lint
```

#### Python 开发命令

```bash
# 添加依赖
uv add <package>
uv add --dev <package>  # 开发依赖

# 运行脚本
uv run python script.py

# 进入虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 类型检查
uv run mypy chatbi/

# 测试覆盖率
uv run pytest --cov=chatbi tests/
```

#### 前端开发命令

```bash
cd web

# 添加依赖
pnpm add <package>
pnpm add -D <package>  # 开发依赖

# 类型检查
pnpm type-check

# 构建
pnpm build

# 预览生产构建
pnpm preview
```

---

### 开发工作流

#### 添加新功能

**1. 创建 Domain（DDD模式）**:
```bash
# 目录结构
chatbi/domain/<feature>/
├── __init__.py
├── models.py       # 领域模型（纯Python）
├── entities.py     # ORM模型（SQLAlchemy）
├── dtos.py         # API请求/响应模型（Pydantic）
├── repository.py   # 数据访问层
├── service.py      # 业务逻辑
└── router.py       # FastAPI路由
```

**2. 数据库迁移**:
```bash
# 创建迁移
uv run python -m chatbi.migrations.manage_migrations create "add feature tables"

# 编辑生成的迁移文件
# chatbi/migrations/versions/xxx_add_feature_tables.py

# 应用迁移
uv run python -m chatbi.migrations.manage_migrations upgrade
```

**3. 注册路由**:
```python
# chatbi/routers/__init__.py
from chatbi.domain.feature import FeatureRouter

api_router.include_router(FeatureRouter)
```

**4. 生成前端类型**:
```bash
make gen-api
```

**5. 编写测试**:
```python
# tests/test_feature.py
import pytest

async def test_create_feature(client):
    response = await client.post("/api/v1/features", json={...})
    assert response.status_code == 200
```

#### 添加新 Agent

**1. 创建 Agent 类**:
```python
# chatbi/agent/my_agent.py
from chatbi.agent.agent_base import AgentBase
from chatbi.agent.agent_message import AgentMessage

class MyAgent(AgentBase):
    def __init__(self, llm_provider, observer=None):
        super().__init__(name="MyAgent", llm_provider=llm_provider, observer=observer)
    
    async def replay(self, **kwargs) -> AgentMessage:
        # 实现逻辑
        pass
```

**2. 添加 Prompt 模板**:
```python
# chatbi/agent/prompts/my_prompt.py
def get_my_prompt(context: str) -> str:
    return f"""
    You are a...
    {context}
    """
```

**3. 集成到 Pipeline**:
```python
# chatbi/pipelines/ask/ask_pipeline.py
from chatbi.agent.my_agent import MyAgent

self.my_agent = MyAgent(llm, observer=self.observer)
```

---

### 调试技巧

#### Python 调试

**使用 IPython 断点**:
```python
# 在代码中插入断点
import IPython; IPython.embed()
```

**使用 pdb**:
```python
import pdb; pdb.set_trace()
```

**查看日志**:
```bash
# 日志位置
tail -f runs/run.log

# 错误日志
tail -f runs/logs/error_*.log
```

**调整日志级别**:
```python
# .env
DEBUG=true

# 代码中
from loguru import logger
logger.debug("Detailed info")
logger.info("General info")
```

#### 前端调试

**React DevTools**:
```bash
# 安装浏览器扩展
# Chrome: https://chrome.google.com/webstore/detail/react-developer-tools
```

**查看 API 请求**:
```typescript
// web/src/services/request.ts
// 已配置请求/响应拦截器，自动打印到控制台
```

**Source Maps**:
- 开发模式默认启用
- 可在浏览器 DevTools 中调试 TypeScript 源码

#### 数据库调试

**查看 SQL 日志**:
```python
# .env
DB_ECHO=true  # 打印所有 SQL 语句
```

**手动查询**:
```bash
# 方式1: 通过 Docker 容器连接（推荐）
docker compose -f docker/compose.yml exec postgres psql -U chatbi -d chatbi

# 方式2: 本地 psql 客户端（需要单独安装）
psql -h localhost -p 15432 -U chatbi -d chatbi

# 查看所有表
\dt

# 查询数据
SELECT * FROM chat_sessions LIMIT 10;
```

**使用 pgAdmin（Web UI）**:
```bash
# 添加 pgAdmin 到 docker-compose.yml 或单独运行
docker run -d -p 5050:80 \
  --name pgadmin \
  --network chatbi_default \
  -e 'PGADMIN_DEFAULT_EMAIL=admin@example.com' \
  -e 'PGADMIN_DEFAULT_PASSWORD=admin' \
  dpage/pgadmin4

# 访问: http://localhost:5050
# 连接信息:
#   Host: postgres (容器内网络) 或 host.docker.internal (macOS/Windows)
#   Port: 5432
#   Database: chatbi
#   Username: chatbi
#   Password: 12345
```

---

### 代码质量

#### 运行 Linters

```bash
# Python（Ruff）
make lint           # 检查
make format         # 自动修复

# 手动运行
uv run ruff check chatbi/
uv run ruff format chatbi/

# TypeScript（ESLint）
cd web
pnpm lint
pnpm lint:fix
```

#### 运行测试

```bash
# 所有测试
make test

# 单个文件
uv run pytest tests/test_main.py

# 带覆盖率
uv run pytest --cov=chatbi --cov-report=html tests/

# 查看覆盖率报告
open htmlcov/index.html
```

#### 类型检查

```bash
# Python（MyPy）
uv run mypy chatbi/

# TypeScript
cd web
pnpm type-check
```

---

### 常见开发问题

**Q: 依赖安装失败**

A: 清理缓存重试：
```bash
# Python
rm -rf .venv
uv sync

# Node.js
cd web
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

**Q: 数据库连接失败**

A: 检查 Docker 容器状态：
```bash
# 查看所有中间件容器状态
docker compose -f docker/compose.yml ps

# 检查 PostgreSQL 容器日志
docker compose -f docker/compose.yml logs postgres

# 重启 PostgreSQL 容器
docker compose -f docker/compose.yml restart postgres

# 验证端口映射
netstat -an | grep 15432  # 或 lsof -i :15432

# 如果容器未启动，执行
cd docker && docker compose up -d postgres
```

**Q: 前端 API 类型不匹配**

A: 重新生成类型：
```bash
make gen-api
cd web
pnpm type-check
```

**Q: 热重载不工作**

A: 
- 后端：检查 `--reload` 参数
- 前端：检查 `webpack-dev-server` 配置
- 文件监视器限制：`ulimit -n 10240` (macOS/Linux)

**Q: 端口冲突**

A: 修改端口：
```bash
# 后端
uvicorn chatbi.main:app --port 8001

# 前端
cd web
PORT=3000 pnpm dev
```

---

### 推荐 IDE 配置

#### VS Code

**推荐扩展**:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "streetsidesoftware.code-spell-checker"
  ]
}
```

**工作区设置** (`.vscode/settings.json`):
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  }
}
```

#### PyCharm

1. **配置 Python 解释器**: 
   - Settings → Project → Python Interpreter
   - 添加本地解释器 → `.venv/bin/python`

2. **启用 Ruff**:
   - Settings → Tools → Ruff
   - 勾选 "Run Ruff on save"

3. **配置运行配置**:
   - Run → Edit Configurations
   - 添加 "Python" → Script path: `.venv/bin/uvicorn`
   - Parameters: `chatbi.main:app --reload`

---

## 快速开始

### 方式一：一键部署脚本（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/chatbi.git
cd chatbi

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，至少设置：
#   - LLM_API_KEY (必须)
#   - JWT_SECRET_KEY (生产环境必须修改)

# 3. 运行部署脚本
./deploy.sh
```

部署成功后访问：
- **前端**: http://localhost:8080
- **API文档**: http://localhost:8080/api/docs
- **默认管理员**: admin / admin123

---

### 方式二：手动部署

#### 前置条件
- Docker 20.10+
- Docker Compose 2.0+

#### 步骤

**1. 准备环境变量**
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```bash
# 必须配置
LLM_API_KEY=sk-your-api-key-here
JWT_SECRET_KEY=your-strong-secret-key-here

# 可选配置
DB_PASSWORD=your-secure-password
REQUIRE_AUTH=true  # 生产环境建议开启
```

**2. 构建镜像**
```bash
docker build -t chatbi:latest .
```

**3. 启动服务**
```bash
cd docker
docker compose up -d
```

**4. 检查状态**
```bash
# 查看所有服务
docker compose ps

# 查看应用日志
docker compose logs -f chatbi-app

# 健康检查
curl http://localhost:8080/api/health
```

---

## 架构说明

### 单容器架构
ChatBI 采用单容器双进程架构，一个容器内同时运行：
- **Nginx** (Port 80): 静态文件托管 + API反向代理
- **FastAPI** (Port 8000): 后端API服务

```
┌─────────────────────────────────┐
│   Docker Container (chatbi-app) │
│  ┌──────────┐    ┌──────────┐  │
│  │  Nginx   │◄───┤ FastAPI  │  │
│  │  :80     │    │ :8000    │  │
│  └─────┬────┘    └──────────┘  │
└────────┼──────────────────────┘
         │
    :8080 (外部端口)
```

### 服务依赖
```
chatbi-app
  ├── postgres (数据库)
  ├── redis (缓存)
  └── cube_api (OLAP引擎)
      ├── cube_refresh_worker
      ├── cubestore_router
      ├── cubestore_worker_1
      └── cubestore_worker_2
```

---

## 环境变量说明

### 必须配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | LLM API密钥 | `sk-xxx` |
| `JWT_SECRET_KEY` | JWT签名密钥（生产必改） | `random-64-char-string` |

### 数据库配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_HOST` | `postgres` | 数据库地址 |
| `DB_PORT` | `5432` | 数据库端口 |
| `DB_NAME` | `chatbi` | 数据库名 |
| `DB_USER` | `chatbi` | 数据库用户 |
| `DB_PASSWORD` | `12345` | 数据库密码（生产必改） |

### 认证配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `JWT_ALGORITHM` | `HS256` | JWT算法 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access Token有效期（分钟） |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh Token有效期（天） |
| `REQUIRE_AUTH` | `false` | 是否强制鉴权（生产建议`true`） |

### LLM配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_PROVIDER` | `openai` | 提供商：openai/tongyi/deepseek |
| `LLM_BASE_URL` | OpenAI官方 | API端点 |
| `LLM_MODEL` | `gpt-3.5-turbo` | 模型名称 |

---

## 运维操作

### 查看日志
```bash
# 所有服务
docker compose -f docker/compose.yml logs -f

# 仅应用
docker compose -f docker/compose.yml logs -f chatbi-app

# 仅数据库
docker compose -f docker/compose.yml logs -f postgres
```

### 重启服务
```bash
# 重启应用
docker compose -f docker/compose.yml restart chatbi-app

# 重启所有服务
docker compose -f docker/compose.yml restart
```

### 停止服务
```bash
docker compose -f docker/compose.yml down

# 同时删除数据卷（危险操作！）
docker compose -f docker/compose.yml down -v
```

### 更新部署
```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker build -t chatbi:latest .

# 3. 重启服务
docker compose -f docker/compose.yml up -d chatbi-app
```

### 数据库迁移
```bash
# 进入容器
docker exec -it chatbi-app bash

# 执行迁移
cd /app
.venv/bin/python -m chatbi.migrations.manage_migrations upgrade
```

---

## 测试验证

### M1 验收测试
```bash
# 安装测试依赖
uv sync

# 运行测试
uv run python tests/test_m1_acceptance.py
```

测试覆盖：
- ✅ 健康检查
- ✅ 用户登录（admin/admin123）
- ✅ JWT鉴权
- ✅ API前缀统一（/api/v1）
- ✅ 限流功能

---

## 故障排查

### 容器无法启动
```bash
# 查看详细错误
docker compose -f docker/compose.yml logs chatbi-app

# 常见原因：
# 1. 端口冲突：检查8080端口是否被占用
# 2. 数据库连接失败：确认postgres服务正常
# 3. 构建失败：检查Dockerfile中的依赖安装
```

### 前端404
```bash
# 检查静态文件是否存在
docker exec -it chatbi-app ls -la /app/static

# 如果为空，检查构建日志
docker build -t chatbi:latest . --progress=plain
```

### API返回500
```bash
# 检查FastAPI日志
docker compose -f docker/compose.yml logs chatbi-app | grep ERROR

# 常见原因：
# 1. 数据库连接失败
# 2. 环境变量未设置
# 3. LLM API调用失败
```

### 认证失败
```bash
# 检查JWT配置
docker exec -it chatbi-app env | grep JWT

# 验证用户是否存在
docker exec -it chatbi-postgres psql -U chatbi -d chatbi -c "SELECT * FROM users;"
```

---

## 生产部署建议

### 安全配置
1. **修改默认密码**
   ```bash
   DB_PASSWORD=<strong-password>
   JWT_SECRET_KEY=<64-char-random-string>
   ```

2. **启用HTTPS**
   - 使用Nginx反向代理添加SSL终止
   - 或使用Traefik/Caddy自动HTTPS

3. **限制网络访问**
   ```yaml
   # docker-compose.yml
   services:
     postgres:
       ports: []  # 移除端口映射，仅内部访问
   ```

4. **启用强制认证**
   ```bash
   REQUIRE_AUTH=true
   ```

### 性能优化
1. **增加Worker数量**
   ```conf
   # docker/supervisord.conf
   command=/app/.venv/bin/uvicorn chatbi.main:app --host 127.0.0.1 --port 8000 --workers 4
   ```

2. **启用Redis缓存**
   ```bash
   CACHE_TYPE=redis
   REDIS_URL=redis://redis:6379/0
   ```

3. **数据库连接池**
   ```bash
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   ```

### 监控告警
- 集成Prometheus指标导出
- 配置Grafana可视化
- 设置健康检查告警

---

## 常见问题

**Q: 如何修改默认管理员密码？**

A: 登录后调用更新用户API：
```bash
curl -X PUT http://localhost:8080/api/v1/auth/users/<user_id> \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"password": "new-password"}'
```

**Q: 如何添加新用户？**

A: 使用管理员账号调用创建用户API：
```bash
curl -X POST http://localhost:8080/api/v1/auth/users \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user1",
    "email": "user1@example.com",
    "password": "password123",
    "is_admin": false
  }'
```

**Q: 如何备份数据？**

A: 
```bash
# 备份数据库
docker exec chatbi-postgres pg_dump -U chatbi chatbi > backup.sql

# 恢复数据库
docker exec -i chatbi-postgres psql -U chatbi chatbi < backup.sql
```

---

## 支持与反馈

- **Issue**: https://github.com/your-org/chatbi/issues
- **文档**: https://docs.chatbi.example.com
- **邮件**: support@chatbi.example.com
