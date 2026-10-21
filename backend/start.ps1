$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "未找到 python 命令。请先安装 Python 3 并确保已加入 PATH。"
}

$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path -LiteralPath $envFile)) {
    throw "缺少 backend/.env。本机配置文件已由 .gitignore 忽略，请先按 backend/.env.example 创建并填写。"
}

Set-Location -LiteralPath $PSScriptRoot
python app.py
exit $LASTEXITCODE
