# Fast-forward-only updater. Local runtime data is never overwritten by Git updates.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'Windows-Loopback.ps1')
Set-Location $root
try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw '未安装 Git。请安装 Git for Windows 后重试。'
    }
    & git -C $root rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) { throw '当前目录不是 Git 克隆仓库。请按照 README 的一次性迁移方法，从 GitHub 克隆后再使用更新按钮。' }
    $top = (& git -C $root rev-parse --show-toplevel).Trim()
    if ($LASTEXITCODE -ne 0 -or ([System.IO.Path]::GetFullPath($top).TrimEnd('\','/') -ine [System.IO.Path]::GetFullPath($root).TrimEnd('\','/'))) {
        throw '请在 VPS Deploy Panel 仓库根目录执行更新。'
    }
    $origin = (& git -C $root remote get-url origin).Trim()
    if ($LASTEXITCODE -ne 0 -or $origin -notmatch '(^https://github\.com/(slobys|Berg-E5)/netdeploy-ai(\.git)?$|^git@github\.com:(slobys|Berg-E5)/netdeploy-ai(\.git)?$)') {
        throw 'origin 不是本项目仓库（slobys/netdeploy-ai 或 Berg-E5/netdeploy-ai），已停止更新以防误操作。'
    }
    $branch = (& git -C $root branch --show-current).Trim()
    if ($branch -ne 'main') { throw '自动更新仅支持 main 分支，其他分支请手动更新。' }
    if ((& git -C $root status --porcelain --untracked-files=normal)) {
        throw '检测到未提交的代码变更；为避免覆盖，已停止更新。请先提交、暂存或备份修改。'
    }
    if (-not (Test-VPSDeployPanelPortAvailable)) { throw '本机 8787 无法绑定。请先停止使用该端口的服务，再更新本面板。' }
    & git -C $root fetch --prune origin main
    if ($LASTEXITCODE -ne 0) { throw 'GitHub 拉取失败，未修改本地代码。' }
    $localHead = (& git -C $root rev-parse HEAD).Trim()
    $remoteHead = (& git -C $root rev-parse refs/remotes/origin/main).Trim()
    if ($localHead -eq $remoteHead) {
        Write-Host '[VPS Deploy Panel] 已是最新版，无需更新。' -ForegroundColor Green
        exit 0
    }
    & git -C $root merge-base --is-ancestor $localHead $remoteHead
    if ($LASTEXITCODE -ne 0) {
        & git -C $root merge-base --is-ancestor $remoteHead $localHead
        if ($LASTEXITCODE -eq 0) {
            Write-Host '[VPS Deploy Panel] 本地包含尚未发布的提交，继续启动本地版本。' -ForegroundColor Green
            exit 0
        }
        throw '本地和远程提交出现分叉，已停止更新，禁止强制覆盖。'
    }

    $dataPath = Join-Path $root 'data'
    if (Test-Path $dataPath) {
        $backupRoot = Join-Path $root 'backups'
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $archive = Join-Path $backupRoot "netdeploy-data-$stamp.zip"
        Compress-Archive -Path $dataPath -DestinationPath $archive -ErrorAction Stop
        Write-Host "[VPS Deploy Panel] 旧数据已备份到 $archive"
    }
    & git -C $root merge --ff-only origin/main
    if ($LASTEXITCODE -ne 0) { throw 'Git fast-forward 更新失败，未强制覆盖本地改动。' }
    Write-Host '[VPS Deploy Panel] 更新成功，.env、data/、secrets/ 均保留原样。' -ForegroundColor Green
    Write-Host '[VPS Deploy Panel] 现在可以双击 Start-VPSDeployPanel.bat 启动。'
} catch {
    Write-Host "[VPS Deploy Panel] 更新中止：$($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
