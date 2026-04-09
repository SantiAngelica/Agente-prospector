#!/bin/bash
# ╔══════════════════════════════════════════════════════╗
# ║     INSTALADOR - Agente Prospector de Negocios      ║
# ╚══════════════════════════════════════════════════════╝

set -e

GREEN='\033[0;32m'
CYAN='\033[0;96m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║     🤖 INSTALANDO AGENTE PROSPECTOR                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar Python
echo -e "${GREEN}[1/5]${NC} Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 no encontrado. Instalalo desde https://python.org${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "  ✓ ${PYTHON_VERSION} detectado"

# Crear entorno virtual
echo -e "${GREEN}[2/5]${NC} Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "  ✓ Entorno virtual creado"
else
    echo -e "  ✓ Entorno virtual ya existe"
fi

# Activar venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Instalar dependencias
echo -e "${GREEN}[3/5]${NC} Instalando dependencias Python..."
pip install --quiet --upgrade pip
pip install --quiet anthropic playwright pyyaml
echo -e "  ✓ anthropic, playwright, pyyaml instalados"

# Instalar Playwright browsers
echo -e "${GREEN}[4/5]${NC} Instalando Chromium para Playwright..."
playwright install chromium
playwright install-deps chromium 2>/dev/null || true
echo -e "  ✓ Chromium instalado"

# Verificar API key
echo -e "${GREEN}[5/5]${NC} Verificando API Key de Anthropic..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}  ⚠ ANTHROPIC_API_KEY no está configurada${NC}"
    echo ""
    echo -e "  Para configurarla, ejecutá:"
    echo -e "  ${CYAN}export ANTHROPIC_API_KEY='tu-api-key-aqui'${NC}"
    echo ""
    echo -e "  Obtenela en: https://console.anthropic.com"
else
    echo -e "  ✓ API Key detectada"
fi

echo ""
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ INSTALACIÓN COMPLETADA${NC}"
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Próximos pasos:${NC}"
echo ""
echo -e "  1. Editá ${CYAN}config.md${NC} con tu ciudad y parámetros"
echo -e "  2. Configurá tu API Key:"
echo -e "     ${CYAN}export ANTHROPIC_API_KEY='sk-ant-...'${NC}"
echo -e "  3. Ejecutá el agente:"
echo -e "     ${CYAN}source venv/bin/activate${NC}"
echo -e "     ${CYAN}python agente.py${NC}"
echo ""
echo -e "  📄 Los resultados se guardarán en ${CYAN}prospectos.csv${NC}"
echo ""
