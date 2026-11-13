# VPS Deploy Panel

**用网页管理 VPS、部署自己项目的工具。**

添加服务器、核对 SSH 指纹、检查环境、生成部署方案、审批执行 —— 全程在浏览器里完成。

> **当前为 Alpha 测试版**，请先在可以备份或重装的 VPS 上试用。

[📖 在线使用文档](https://berg-e5.github.io/netdeploy-ai/) · [🚀 安装教程](https://berg-e5.github.io/netdeploy-ai/installation.html) · [❓ 常见问题](https://berg-e5.github.io/netdeploy-ai/troubleshooting.html) · [💬 反馈问题](https://github.com/Berg-E5/netdeploy-ai/issues)

## 我的项目

| 项目 | 源码 | 部署内容 |
| --- | --- | --- |
| **物流报价系统** | [Berg-E5/logistics-quote](https://github.com/Berg-E5/logistics-quote) | systemd 单元 + nginx 反代 + 可选证书；装完是空站，需后台上传报价表才有价格 |
| **音乐解锁工具** | [Berg-E5/music-unlock](https://github.com/Berg-E5/music-unlock) | 静态文件 + nginx 反代 + 可选证书；解密在浏览器里跑，文件不上传 |

两个项目排在首页最前面，部署流程和下面其它项目完全一致 —— 详见 [自建项目：物流报价系统 / 音乐解锁工具](#自建项目物流报价系统--音乐解锁工具)。

## 通用项目

面板也内置了一批常用开源项目：3X-UI、S-UI、sing-box、Hysteria2、wg-easy、Dockge Apps、Hiddify Manager。


## 主要功能

- **VPS 管理**：添加服务器、SSH 密码/密钥连接、核对主机指纹。
- **向导式部署**：自动检查运行环境，确认安装方案后再执行，并显示进度和日志。
- **HTTPS 证书**：3X-UI、S-UI 可自动申请 IP/域名证书，也可交给 NPM 统一管理 HTTPS。
- **端口管理**：管理 VPS 上的 UFW 规则，提供常见云厂商安全组入口。
- **自定义界面**：多种主题颜色、明暗模式和阅读字号。
- **Codex AI（可选）**：使用自己的 ChatGPT 账号，通过自然语言查询任务、打开面板页面、生成待审批部署方案或分析安装日志，无需另填 API Key。

## 内置的通用项目

| 项目 | 当前支持情况 |
| --- | --- |
| **3X-UI** | 自动安装，支持 IP/域名 HTTPS 或 NPM 统一 SSL；NPM 模式可提供公网 HTTP 管理地址 |
| **S-UI** | 自动安装，支持 IP / 域名 HTTPS |
| **sing-box** | 自动安装内核，服务端配置需自行完成 |
| **wg-easy** | Docker Compose 自动部署，需完成首次设置 |
| **[Dockge Apps](https://github.com/slobys/dockge-apps)** | 二开应用中心（NPM、IT-Tools、MyIP）；缺 Docker 可使用官方一键脚本，管理端口随机或自定义；新安装默认公网 IP 直连，执行前需确认风险 |
| **Hysteria2** | 提供部署引导，暂不支持一键安装 |
| **Hiddify Manager** | 专用 Ubuntu VPS 上审批执行官网一键安装（Beta），在任务中打开管理面板完成官方快速设置 |

## 自建项目：物流报价系统 / 音乐解锁工具

这两个是 Berg 自己维护的项目，按面板的目录机制接进来，首页排在最前面。

| 项目 | 源码 | 部署内容 |
| --- | --- | --- |
| **物流报价系统** | [Berg-E5/logistics-quote](https://github.com/Berg-E5/logistics-quote) | systemd 单元 + nginx 反代 + 可选 HTTPS 证书 + 首次启动随机 admin 账号 |
| **音乐解锁工具** | [Berg-E5/music-unlock](https://github.com/Berg-E5/music-unlock) | 静态文件 + nginx 反代 + 可选 HTTPS 证书；无常驻服务 |

### 完整部署流程

1. **录入 VPS** —— 填主机地址和 SSH 凭据。面板只保存主机信息，密码不进面板数据库（走系统钥匙串）。
2. **核对 SSH 指纹** —— 面板扫到的指纹必须和云控制台或服务器上**独立算出来的**指纹核对一致，确认后才写进 known_hosts。**软件不会自动信任任何指纹。**
3. **环境预检** —— 只读扫描：系统版本、架构、是否 root、磁盘、systemd、`ss`、80/443 是否被占、目标项目是否已经装过。
4. **生成部署计划** —— 5 步：核对环境 → 装依赖 → 下载固定 commit 并校验 SHA-256 → 执行安装 → 验收。每一步的脚本都能逐条看。
5. **审批执行** —— 审批时**会再跑一次预检**，环境变了当场拦住，不会闷头往下装。
6. **看结果** —— 每一步的输出都在任务日志里。

### 安全底线

- 固定到具体 commit，**不追 main 分支** —— 主分支随时会变，不能直接执行。
- 下载后落盘再校验 `install.sh` 的 SHA-256，**不匹配立刻中止**；不做 `curl | bash` 管道。
- 执行的是仓库里已审阅的 `install.sh`，不是远程一键脚本。
- 端口被占、目标项目已装过 → **直接阻断，不覆盖**。
- nginx 会 `enable` + `restart` 并确认在运行；验收会真的 `curl` 打 80 端口、**带 Host 头走自己的 vhost**，只看 `nginx -t` 不算数。

### 两个项目各自的要点

**物流报价系统**

- 部署目标是 **GitHub 公开源码**，装完是**空站**：没有账号数据、没有报价表。
- 装完进 `/admin`，首次启动随机生成 admin 密码并打印在部署日志里（之后可用 `node server/user.js passwd admin` 重置）。
- 在后台「整表导入」上传报价表 xlsx，约 2～3 分钟生成全部价格，前台立即可用。
- 想要「装完就有数据」就走带数据的发布包安装（`deploy/install-remote.sh`），那条路会带上现有账号和费率。
- 不会覆盖已存在的 `quote-server` 服务；后端端口 8792 被占会自动往后挑，挑好的端口写在 `data/port` 里。

**音乐解锁工具**

- 纯静态站，解密在浏览器 Worker 里跑，**文件不上传服务器**。
- 服务器只放静态文件和 nginx 配置，没有后端、没有数据库、不装常驻服务。

### 已知边界

- 只支持 Debian/Ubuntu 的 root VPS，需要 systemd 和 `ss`。
- 80/443 必须空闲（面板要独占这两个端口做反代和证书签发）。
- 域名要先解析到这台 VPS，否则证书签发会失败 —— 可以先勾「跳过 HTTPS 证书申请」用 HTTP 先验证。
- 面板是 **Alpha**，请先在能备份或重装的 VPS 上试。

### 推回 GitHub

这台开发机直连 `github.com:443` 会被 reset，`git push` 走不通，但 `api.github.com` 是通的。
所以仓库自带了一个走 API 的推送脚本（效果和 `git push` 一样）：

```bash
python scripts/push_github_api.py                      # 推 main
python scripts/push_github_api.py --repo 用户名/仓库名    # 换仓库
python scripts/push_github_api.py --dry-run             # 只看会传什么
```

它上传的是 **git 索引里的原始 blob**（用 `git cat-file` 取），不是工作区文件 ——
Windows 上 `core.autocrlf=true` 时工作区是 CRLF、索引里是 LF，
传工作区文件会让远端存成 CRLF，shell 脚本在 Linux 上会报 `bad interpreter`。

前提是本机装了 `gh` 并登录过（`gh auth login`），token 从 `gh auth token` 取，不落在文件里。


### 相对上游的改动

| 改动 | 说明 |
| --- | --- |
| 新增两个自建项目 | 目录驱动，固定 commit + SHA-256 校验，接同一套审批与验收流程 |
| Windows SSH 执行 | 系统里没有可执行的 OpenSSH 客户端时（只有 WindowsApps 里的副本），自动改走 Paramiko 密钥认证；主机密钥固定用同一份 known_hosts，语义不变 |
| nginx 自启 | 安装脚本原来只 `reload` nginx，对「装了但没启动」的服务无效，站点会打不开；改为 `enable` + `restart` 并确认在运行 |
| 验收判定 | 原来只跑 `nginx -t`，配置语法通过但服务没起来也会判通过；现在会确认 nginx 在跑，并用带 Host 头的 `curl` 打到自己的 vhost |
| 验收端口 | 端口不再写死 8792，改为读安装脚本写下的 `data/port` |
| 域名校验 | 补上连续点、段首段尾横线、单段超 63 字符等非法域名的拦截 |


## IPv6 VPS 支持（3X-UI / S-UI）

- 添加服务器时可填写 **公网 IPv4 或 IPv6**（例如 `2606:4700:4700::1111`，**不要加方括号**），连接过程保持 SSH 指纹核验、密码/密钥认证与部署审批。支持纯 IPv6 和双栈 VPS；连接地址由用户选择。
- **SSH 指纹排查**：Windows `Test-NetConnection -ComputerName IPv6 -Port 22` 的 `TcpTestSucceeded=True` 只代表 TCP 端口可达，不能证明 sshd 正常协商。若步骤 2 扫描失败，可以在 PowerShell 执行 `ssh-keyscan -6 -T 15 -p 22 IPv6` 区分 SSH 协议异常与扫描超时。NetDeploy 会区分 Banner、算法和连接中断，仅对临时 Banner/握手中断在未认证阶段有限重试；扫描返回的指纹仍须去云厂商控制台独立核对，软件绝不自动信任。
- **3X-UI**：IPv6 VPS 可选择本机 SSH 隧道、NPM 反向代理或内置自动 HTTPS。IP 证书采用约 160 小时的短有效期配置和独立 Certbot 续期；域名 HTTPS 要求 DNS AAAA 正确。HTTPS 成功会显示 `https://[IPv6]:端口/路径`（域名证书则显示域名 URL）；NPM 模式仍保持明确的公网明文 HTTP 风险提示。
- **S-UI**：IPv6 VPS 同样可选择本机 SSH 隧道、NPM 或自动 HTTPS。签发并校验证书后才开放管理端口 2095；**订阅端口 2096 始终仅监听本机 `127.0.0.1`**。HTTPS 失败会尝试恢复本机监听；异常服务不会回退成公网明文 HTTP。
- **自动证书检查**：IPv6 签发前验证目标地址确实分配给 VPS；若使用域名，则要求其全部 AAAA 记录指向当前 IPv6。Certbot 使用 IPv6 TCP 80 接受 HTTP-01 挑战，签发后校验可信证书链、IPv6 TLS 监听和本机公网 IPv6 连接。IPv6 IP 证书使用独立 Certbot 每四小时检查续期；域名使用系统 Certbot 定时器。
- **上线前仍需实机验收**：UFW 必须启用 IPv6（活跃时 `/etc/default/ufw` 的 `IPV6=yes`），云厂商 IPv6 安全组需独立放行 TCP 80 和管理端口、限制管理来源；本机 curl 验证不等于已从外部网络验证。IPv6 ACME 自动化虽已有模拟测试，尚未在真实 IPv6 VPS/Let’s Encrypt 生产环境实测；建议先用可重装的测试 VPS 试用。IPv4 原流程不变。

## Windows 快速开始（推荐）

先安装 [Git for Windows](https://git-scm.com/downloads/win) 和 [Python 3.12+](https://www.python.org/downloads/windows/)（需包含 `py` 启动器）。

打开 **PowerShell**，依次执行：

```powershell
git clone https://github.com/Berg-E5/netdeploy-ai.git
cd netdeploy-ai
.\QuickStart-VPSDeployPanel.bat
```

启动后在浏览器访问 **http://127.0.0.1:8787**。Windows 本机模式首次启动可自动登录。

**以后启动或更新：** 双击项目文件夹中的 `QuickStart-VPSDeployPanel.bat`。面板正在运行时会直接打开网页。停止面板后再次双击会检查更新、备份本地数据并在后台启动。需要在终端查看输出或用 `Ctrl+C` 停止时，可单独运行 `Start-VPSDeployPanel.bat`。

## 使用 ChatGPT 订阅连接 Codex（可选）

**Windows 默认原生模式（无需 Docker）**：只需安装 Git 和 Python。运行 `QuickStart-VPSDeployPanel.bat` 后，后台自动创建专用 Python 环境并安装官方 Codex SDK，**不启动 Docker Desktop、WSL 或 Codex 桌面软件**。首次下载 SDK 的 Windows 运行组件可能需要一些时间，后台「Codex AI」可显示进度。连接自己的 ChatGPT 账号并完成首次设备码授权后，正常重启会复用登录状态（登录失效时需重新授权）。

旧的 `Enable-Codex-Windows.bat` 入口也会进入原生启动流程。请用普通 Windows 用户权限启动面板。

原生 Worker 仅监听 `127.0.0.1:8789`，使用 `%LOCALAPPDATA%\VPSDeployPanel\codex-native` 下的独立工作区、SDK 环境与登录目录；不会把面板的 SSH 密码、管理员令牌或数据库路径传给 Worker。Windows 原生沙箱开启 `prefer_mxc`，只读诊断禁止提权审批；**但同一 Windows 用户下的进程隔离不等于 Docker / 独立用户的强隔离**。请在可信的本机使用，不要把后台公开到互联网。

如需关闭自动启动，在本机 `.env` 添加 `VPSDEPLOY_CODEX_AUTO_START=0`；不影响其他 VPS 管理功能。之前安装的 Docker 版 Worker 不会被自动卸载或清除数据，但 Windows 默认不再调用它。

**Docker / NAS 启动**：在项目私有 `.env` 中设置至少 24 位随机 `VPSDEPLOY_WORKER_TOKEN`（与管理员令牌不同），然后运行 `docker compose --profile ai up -d --build`。现有主程序不会把 SSH 密钥、数据库或 Docker Socket 挂载进 AI Worker。

进入后台左侧 **Codex AI** → **使用 ChatGPT 账号连接**，在浏览器打开官方验证页并输入一次性设备代码。设备码登录需要在 ChatGPT 安全设置中启用。授权后，可以输入「最近哪些部署失败了」或「为东京 VPS 生成 S-UI 部署方案」。使用面板中的 VPS 完整名称和项目名称，面板会自动只读预检并打开方案，由你审阅后确认执行。自动方案中的 3X-UI、S-UI 和 Dockge Apps 采用 SSH 隧道访问。自定义端口、证书或公网模式可打开部署向导设置。查看具体安装失败原因时，可以在对应任务中点击 **AI 只读排障**。

登录凭据分别保存在 Windows 原生 Worker 的专属 `CODEX_HOME` 或 Docker/NAS Worker 的私有 `codex-auth` 卷中，退出登录可清除授权。面板指令会将输入文字、服务器名称、近期任务状态和项目名称等摘要发送给 Codex。使用「AI 只读排障」时会另外发送脱敏的日志摘录和基本系统信息。请勿在指令、名称或日志中填写凭据。ChatGPT 套餐额度有限，个人登录仅供本人使用。

## 如何部署软件？

1. 点击 **添加 VPS**，填写服务器地址和 SSH 登录信息。
2. 核对 **SSH 主机指纹**，检查服务器环境。
3. 打开 **项目中心**，选择要安装的软件。
4. 查看安装方案、确认执行，最后查看结果。

Docker / NAS 用户可参考 [Docker 部署教程](https://berg-e5.github.io/netdeploy-ai/installation.html#docker)。各项目的具体要求见 [部署文档](https://berg-e5.github.io/netdeploy-ai/deployments.html)。

## 使用前请注意

- 安装任务需要相应的系统权限；部分项目要求 Debian / Ubuntu、Docker 或指定端口。
- 本面板默认只供本机访问，**不要把管理端口直接暴露到公网**。
- SSH 主机指纹必须通过可信渠道核对；证书签发还需正确的 IP / 域名及防火墙规则。
- 项目尚在测试阶段，自动化测试通过不等于所有 VPS 环境都已实机验收。

## 开源协议与致谢

本项目基于 **[slobys/netdeploy-ai](https://github.com/slobys/netdeploy-ai)** 开发（上游 MIT 协议），
原作者版权声明与许可全文保留在 [LICENSE](LICENSE)。

在上游基础上，我做了这些改动：

- 新增 **物流报价系统** 和 **音乐解锁工具** 两个自建项目，排在首页最前。
- 修掉 Windows 下没有可用 OpenSSH 客户端时 SSH 执行失败（改走 Paramiko 密钥认证）。
- 修掉安装脚本只 `reload` nginx 导致「装了但没启动」时站点打不开（改为 `enable` + `restart` 并确认在运行）。
- 验收从「只看 `nginx -t`」改为「确认 nginx 在跑 + 带 Host 头真实请求自己的 vhost」。
- 安装脚本端口改为自动挑选并写入 `data/port`，重装时沿用原端口不再漂移。
- 收紧域名校验（连续点、段首段尾横线、单段超 63 字符）。
- 品牌与文档改为本项目自己的版本。

**开源协议：** [MIT License](LICENSE)

