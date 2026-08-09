# 上线部署说明

这个项目是 Vue 3 前端 + FastAPI 后端 + MySQL 数据库。仓库里已提供一套 Docker Compose 配置，适合部署到一台 Linux 云服务器，Nginx 会同时提供前端页面，并把 `/api`、`/uploads` 转发到后端。

## 部署目标

```text
浏览器 -> Nginx(前端静态资源)
              |
              +-- /api, /uploads -> FastAPI -> MySQL
```

数据库和上传图片都使用 Docker volume 持久化，重启容器不会丢数据。

## 1. 准备服务器

需要一台 Linux 服务器，并安装：

- Docker Engine
- Docker Compose v2（一般安装 Docker 时会一起安装）
- 一个已解析到服务器 IP 的域名（如果要 HTTPS 就必须有）

服务器安全组或云防火墙需要放行 `80` 端口；如果域名使用 HTTPS，还需要放行 `443`。

既然预算选择 **2 核 2G**，这套项目可以跑，但一定要先加 swap，避免 Docker 构建或 MySQL 启动时内存不足。仓库配置已把 Node 构建内存限制在 1.5G、MySQL 缓冲池调成 256M、后端改为单 worker。

购买建议：

- 地域：选离你的用户最近的区域。服务器在大陆时，绑定域名必须完成 ICP 备案；不想备案可以选中国香港或新加坡地域。
- 系统镜像：选 Ubuntu 22.04 或 Ubuntu 24.04 LTS。
- 带宽：轻量服务器带宽普遍不高，小规模使用 3-5Mbps 可以接受，正式对外访问建议配合 CDN。
- 防火墙：在阿里云控制台和安全组里放行 `22`、`80`、`443` 端口。

### 安装 Docker

连接服务器后执行：

```bash
free -h
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

确认 swap 已生效：

```bash
free -h
```

然后再安装 Docker：

```bash
curl -fsSL https://get.docker.com | bash -s docker
systemctl enable --now docker
docker --version
docker compose version
```

如果安装脚本网络不稳定，也可以在购买服务器时选择阿里云提供的 Docker 应用镜像。

## 2. 上传代码

在服务器上拉取或上传项目到任意目录，例如：

```bash
ssh root@服务器IP
```

然后克隆仓库：

```bash
git clone https://github.com/zifu7/AI_mental_health_talk.git
cd vite-project
```

如果使用宝塔面板或 SFTP，请上传整个项目目录，并确认 `docker-compose.yml`、`frontend/`、`backend/` 都在同一层。

注意：当前仓库本地还有未提交改动。如果走 Git 部署，需要先把改动提交并推送到 GitHub，否则服务器拉取到的是旧代码。

在本机项目目录里提交并推送：

```bash
git add -A
git commit -m "准备上线部署"
git pull origin master --rebase
git push origin master
```

## 3. 创建生产环境变量

```bash
cp .env.example .env
```

然后编辑 `.env`：

```dotenv
MYSQL_PASSWORD=换成强密码
SECRET_KEY=用 openssl rand -hex 32 生成
DEEPSEEK_API_KEY=你的 DeepSeek Key
PORT=80
```

`SECRET_KEY` 生成命令：

```bash
openssl rand -hex 32
```

注意：不要把你的真实 `.env`、`backend/.env` 提交到 Git。当前 `backend/.env` 里的 SECRET_KEY 还是默认值，且里面放了开发用 DeepSeek Key，上线前必须换成服务器专用密钥。

数据库密码建议只使用字母和数字，避免 `@ : / ? #` 等需要 URL 编码的字符。如果本地 MySQL 已经积累数据，上线前先在本地导出，部署完成后再导入到新 MySQL 容器。

## 4. 启动

在项目根目录执行：

```bash
docker compose up -d --build
```

首次启动会拉取 MySQL/Nginx 镜像并构建前后端，需要几分钟。

查看状态：

```bash
docker compose ps
```

检查健康检查：

```bash
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

验证服务：

```bash
curl http://127.0.0.1/health
```

正常会返回：

```json
{"status":"ok"}
```

浏览器打开 `http://服务器IP`，能注册、登录、创建会话并收到 AI 回复，就说明已经上线。

## 5. 绑定域名和 HTTPS

### 方式一：服务器上已有 Nginx

先把 `.env` 里的 `PORT` 改为 `8080`，然后重新启动：

```bash
docker compose up -d
```

在宿主机 Nginx 配置里反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
```

再使用 certbot 申请证书：

```bash
sudo certbot --nginx -d your-domain.com
```

### 方式二：服务器上有 Caddy

同样把 `PORT` 改为 `8080`，然后配置：

```caddyfile
your-domain.com {
    reverse_proxy 127.0.0.1:8080
}
```

Caddy 会自动申请和续期 HTTPS 证书。

## 6. 更新版本

```bash
cd 项目目录
git pull
docker compose up -d --build
```

## 7. 数据备份

备份数据库：

```bash
docker compose exec mysql sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" psychology_db' > psychology_db_$(date +%Y%m%d).sql
```

备份上传图片：

```bash
docker run --rm -v psychology-ai_uploads_data:/data -v "$PWD":/backup alpine tar czf /backup/uploads_$(date +%Y%m%d).tar.gz -C /data .
```

恢复上传图片前，请先确认卷名和备份内容，避免覆盖错误。

## 8. 常见问题

- 页面能打开但接口 502：先看 `docker compose logs backend`，最常见原因是 MySQL 还没就绪或 `.env` 数据库密码不一致。
- DeepSeek 请求失败：确认 `.env` 里的 `DEEPSEEK_API_KEY` 有效，并查看 `docker compose logs backend`。
- 上传图片打不开：确认访问的是 `/uploads/...`，且 `VITE_FILE_BASE_URL` 在构建时保持为空。
- 改了 `.env` 后没生效：`.env` 对镜像构建参数不生效，需要重新构建前端：`docker compose up -d --build frontend`。

## 9. 可选：不使用 Docker 直接部署

如果不使用 Docker，也可以在一台服务器上安装 Python、Node.js、Nginx、MySQL，然后分别执行：

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
cd frontend
npm ci
VITE_FILE_BASE_URL= npm run build
```

再把 `frontend/dist` 指向 Nginx，并把 `/api`、`/uploads` 反向代理到 `127.0.0.1:8000`。
