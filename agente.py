#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║           AGENTE PROSPECTOR DE NEGOCIOS                 ║
║     Powered by Claude AI + Playwright Browser           ║
╚══════════════════════════════════════════════════════════╝

Busca comercios locales y genera mensajes personalizados
para ofrecer servicios de sistemas y tecnología.
"""

import asyncio
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import yaml
from playwright.async_api import async_playwright

# ─── Colores para consola ───────────────────────────────
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════╗
║           🤖 AGENTE PROSPECTOR DE NEGOCIOS              ║
║        Powered by Claude AI + Playwright                ║
╚══════════════════════════════════════════════════════════╝
{Colors.END}""")

def print_step(step, msg):
    print(f"{Colors.BLUE}[{step}]{Colors.END} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}  → {msg}{Colors.END}")

# ─── Cargar configuración desde config.md ───────────────
def load_config(config_path="config.md"):
    """Parsea el archivo config.md con los parámetros."""
    config = {
        "lugar_busqueda": "Buenos Aires, Argentina",
        "limite_lugares": 10,
        "tipos_comercio": ["restaurantes", "bares", "tiendas"],
        "archivo_salida": "prospectos.csv",
        "idioma_mensajes": "español",
        "tu_nombre": "Tu Nombre",
        "tu_empresa": "Tu Empresa",
        "tu_email": "tu@email.com",
        "tu_telefono": "+54 9 11 XXXX-XXXX",
        "tu_web": "https://tu-sitio.com",
        "servicios": [
            "Landing pages profesionales",
            "Sistemas de gestión interna",
            "E-commerce",
            "Agentes de IA para atención al cliente",
        ]
    }
    
    if not os.path.exists(config_path):
        print_warning(f"No se encontró {config_path}, usando valores por defecto.")
        return config
    
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extraer bloque YAML del markdown
    yaml_blocks = re.findall(r'```yaml\n(.*?)```', content, re.DOTALL)
    
    # Parsear líneas key: value directas
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if ':' in line and not line.startswith('#') and not line.startswith('-'):
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip().strip('"').strip("'")
                if key in config and value:
                    if key == "limite_lugares":
                        try:
                            config[key] = int(value)
                        except:
                            pass
                    else:
                        config[key] = value
    
    # Parsear listas (líneas que empiezan con -)
    current_key = None
    list_values = []
    for line in lines:
        stripped = line.strip()
        if ':' in stripped and not stripped.startswith('-') and not stripped.startswith('#'):
            if current_key and list_values:
                config[current_key] = list_values
            parts = stripped.split(':', 1)
            current_key = parts[0].strip()
            list_values = []
        elif stripped.startswith('- ') and current_key:
            list_values.append(stripped[2:].strip())
    
    if current_key and list_values:
        config[current_key] = list_values
    
    return config

# ─── Cliente Anthropic ───────────────────────────────────
def get_claude_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print_error("No se encontró ANTHROPIC_API_KEY en las variables de entorno.")
        print_info("Ejecutá: export ANTHROPIC_API_KEY='tu-api-key'")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)

# ─── Búsqueda en Google Maps con Playwright ─────────────
async def aceptar_cookies(page):
    """Intenta aceptar el banner de cookies de Google si aparece."""
    try:
        for selector in [
            'button[aria-label*="Aceptar"]',
            'button[aria-label*="Accept"]',
            'form[action*="consent"] button',
            '#L2AGLb',  # ID clásico del botón "Acepto" de Google
        ]:
            btn = await page.query_selector(selector)
            if btn:
                await btn.click()
                await asyncio.sleep(1)
                return
    except:
        pass

async def buscar_en_maps(lugar, tipos_comercio, limite, headless=True):
    """Busca comercios en Google Maps y extrae información básica."""
    resultados = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="es-AR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        # Ocultar que es un browser automatizado
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        for tipo in tipos_comercio:
            if len(resultados) >= limite:
                break

            restante = limite - len(resultados)
            print_step("MAPS", f"Buscando '{tipo}' en '{lugar}'...")

            query = f"{tipo} en {lugar}"
            url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

            try:
                # ── Carga con 'load' (mucho más rápido que networkidle) ──
                await page.goto(url, wait_until="load", timeout=45000)

                # Aceptar cookies si aparece el banner
                await aceptar_cookies(page)

                # Esperar a que aparezca la lista de resultados
                try:
                    await page.wait_for_selector(
                        '[role="feed"], [role="article"], div[jsaction*="mouseover"]',
                        timeout=15000
                    )
                except:
                    print_warning(f"  No apareció la lista para '{tipo}', continuando...")
                    continue

                await asyncio.sleep(2)

                # ── Scroll dentro del panel de resultados ──────────────
                feed = await page.query_selector('[role="feed"]')
                for _ in range(8):
                    if feed:
                        await feed.evaluate("el => el.scrollBy(0, 600)")
                    else:
                        await page.keyboard.press("End")
                    await asyncio.sleep(1.2)

                # ── Extraer tarjetas ───────────────────────────────────
                items = await page.query_selector_all('[role="article"]')
                if not items:
                    # Fallback: selector alternativo
                    items = await page.query_selector_all('div[jsaction*="mouseover"][class]')

                print_info(f"Encontrados {len(items)} resultados para '{tipo}'")

                for item in items[:restante]:
                    try:
                        # Nombre  (varios selectores en cascada)
                        nombre = ""
                        for sel in [
                            '[class*="fontHeadlineSmall"]',
                            'a[aria-label]',
                            'h3',
                            'span[class*="HlvSq"]',
                        ]:
                            el = await item.query_selector(sel)
                            if el:
                                txt = (await el.inner_text()).strip()
                                if txt:
                                    nombre = txt
                                    break
                        if not nombre:
                            aria = await item.get_attribute("aria-label")
                            nombre = aria.strip() if aria else ""

                        # Link de Maps
                        link = ""
                        for sel in ['a[href*="/maps/place"]', 'a[href*="google.com/maps"]', 'a[href*="@"]']:
                            el = await item.query_selector(sel)
                            if el:
                                href = await el.get_attribute("href")
                                if href:
                                    link = href if href.startswith("http") else f"https://www.google.com{href}"
                                    break

                        # Dirección / metadata
                        direccion = ""
                        meta_els = await item.query_selector_all('[class*="fontBodyMedium"], [class*="W4Efsd"]')
                        for el in meta_els:
                            txt = (await el.inner_text()).strip()
                            if txt and len(txt) > 5 and not txt.replace(".", "").replace(",", "").replace(" ", "").isdigit():
                                if "\n" in txt:
                                    txt = txt.split("\n")[0]
                                direccion = txt[:120]
                                break

                        if nombre and link and not any(r["nombre"] == nombre for r in resultados):
                            resultados.append({
                                "nombre": nombre,
                                "link_maps": link,
                                "tipo": tipo,
                                "direccion": direccion,
                                "website": "",
                                "telefono": "",
                                "email": "",
                            })
                            print_success(f"  [{len(resultados)}/{limite}] {nombre}")

                        if len(resultados) >= limite:
                            break

                    except Exception:
                        continue

            except Exception as e:
                print_error(f"Error buscando '{tipo}': {e}")
                continue

        await browser.close()

    return resultados[:limite]

# ─── Revisar website del comercio ───────────────────────
async def revisar_website(url, page):
    """Analiza la calidad del website de un comercio."""
    resultado = {
        "tiene_web": False,
        "url_web": "",
        "errores": [],
        "calidad": "Sin web",
        "observaciones": ""
    }
    
    if not url:
        return resultado
    
    try:
        resultado["tiene_web"] = True
        resultado["url_web"] = url
        
        response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        
        if not response or response.status >= 400:
            resultado["errores"].append(f"HTTP {response.status if response else 'sin respuesta'}")
            resultado["calidad"] = "Error de carga"
            return resultado
        
        await asyncio.sleep(2)
        
        # Verificaciones de calidad
        checks = []
        
        # ¿Es mobile-friendly?
        meta_viewport = await page.query_selector('meta[name="viewport"]')
        if meta_viewport:
            checks.append("responsive")
        else:
            resultado["errores"].append("Sin meta viewport (no mobile-friendly)")
        
        # ¿Tiene SSL?
        if url.startswith("https"):
            checks.append("SSL")
        else:
            resultado["errores"].append("Sin HTTPS")
        
        # ¿Tiene título?
        title = await page.title()
        if title and len(title) > 3:
            checks.append("título")
        else:
            resultado["errores"].append("Sin título de página")
        
        # ¿Carga rápido? (ya cargó en el timeout)
        checks.append("carga OK")
        
        # ¿Tiene formulario de contacto?
        forms = await page.query_selector_all('form')
        if forms:
            checks.append("formulario")
        
        # ¿Tiene botón WhatsApp/contacto?
        wa_link = await page.query_selector('a[href*="wa.me"], a[href*="whatsapp"]')
        if wa_link:
            checks.append("WhatsApp")
        
        # Calidad general
        if len(resultado["errores"]) == 0:
            resultado["calidad"] = "Buena"
        elif len(resultado["errores"]) <= 1:
            resultado["calidad"] = "Regular"
        else:
            resultado["calidad"] = "Mejorable"
        
        resultado["observaciones"] = f"OK: {', '.join(checks)}" if checks else "Sin características destacadas"
        
    except Exception as e:
        resultado["errores"].append(f"Error de acceso: {str(e)[:50]}")
        resultado["calidad"] = "Inaccesible"
    
    return resultado

# ─── Obtener detalles del lugar en Maps ─────────────────
async def obtener_detalles_maps(lugar, page):
    """Visita el link de Maps y extrae teléfono, website, etc."""
    detalles = {
        "telefono": "",
        "website": "",
        "email": "",
        "horarios": "",
    }
    
    try:
        await page.goto(lugar["link_maps"], wait_until="load", timeout=45000)
        await aceptar_cookies(page)

        # Esperar a que cargue el panel de detalle
        try:
            await page.wait_for_selector(
                'button[data-item-id], a[href^="tel:"], h1, [aria-label*="Información"]',
                timeout=12000
            )
        except:
            pass

        await asyncio.sleep(2)

        # ── Teléfono ──────────────────────────────────────────
        for sel in [
            'a[href^="tel:"]',
            'button[data-item-id*="phone"]',
            '[aria-label*="Teléfono"]',
        ]:
            el = await page.query_selector(sel)
            if el:
                href = await el.get_attribute("href") or ""
                text = (await el.inner_text()).strip()
                detalles["telefono"] = href.replace("tel:", "") if href.startswith("tel:") else text
                if detalles["telefono"]:
                    break

        if not detalles["telefono"]:
            content = await page.content()
            phones = re.findall(r'(?:\+?54[\s\-]?)?(?:11|[2-9]\d{2,3})[\s\-]?\d{4}[\s\-]?\d{4}', content)
            if phones:
                detalles["telefono"] = phones[0].strip()

        # ── Website ───────────────────────────────────────────
        for sel in [
            'a[data-item-id*="authority"]',
            'a[aria-label*="Sitio web"]',
            'a[aria-label*="sitio"]',
        ]:
            el = await page.query_selector(sel)
            if el:
                href = await el.get_attribute("href") or ""
                if href.startswith("http") and "google" not in href:
                    detalles["website"] = href
                    break

        # ── Horarios ──────────────────────────────────────────
        for sel in ['[aria-label*="horario"]', '[class*="MkV9"] table']:
            el = await page.query_selector(sel)
            if el:
                detalles["horarios"] = (await el.inner_text())[:100]
                break

    except Exception:
        pass

    return detalles

# ─── Generar mensaje con Claude ──────────────────────────
def generar_mensaje_claude(client, comercio, config):
    """Usa Claude para generar un mensaje personalizado para cada comercio."""
    
    servicios_str = "\n".join([f"- {s}" for s in config.get("servicios", [])])
    
    web_info = ""
    if comercio.get("tiene_web"):
        web_info = f"""
- Tiene website: {comercio.get('url_web', '')}
- Calidad del sitio: {comercio.get('calidad_web', 'N/A')}
- Problemas detectados: {', '.join(comercio.get('errores_web', [])) or 'Ninguno detectado'}
"""
    else:
        web_info = "- No tiene sitio web propio"
    
    prompt = f"""Sos un experto en ventas de soluciones tecnológicas para PyMEs y negocios locales.
Tenés que redactar un mensaje CORTO, PERSONALIZADO y PERSUASIVO para contactar a este comercio y ofrecerle servicios de tecnología.

DATOS DEL COMERCIO:
- Nombre: {comercio['nombre']}
- Tipo: {comercio['tipo']}
- Ubicación: {config['lugar_busqueda']}
{web_info}

SERVICIOS QUE OFRECÉS:
{servicios_str}

TU INFORMACIÓN:
- Nombre: {config['tu_nombre']}
- Empresa: {config['tu_empresa']}
- Contacto: {config['tu_email']} | {config['tu_telefono']}

INSTRUCCIONES:
1. El mensaje debe ser para WhatsApp o email, informal pero profesional
2. Máximo 150 palabras
3. Mencioná específicamente el nombre del comercio
4. Basate en el tipo de negocio para personalizar la propuesta (ej: para restaurante → menú digital, reservas online)
5. Si tiene web con problemas, mencioná que podrías mejorársela
6. Si no tiene web, enfocate en que podría conseguir más clientes con una
7. Terminá con un CTA claro (llamada a la acción)
8. Escribí SOLO el mensaje, sin explicaciones adicionales
9. En español argentino, tuteo"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Hola! Soy {config['tu_nombre']} de {config['tu_empresa']}. Vi que tienen {comercio['nombre']} y me gustaría contarles sobre soluciones tecnológicas que podrían ayudarlos a crecer. ¿Tienen un momento? {config['tu_telefono']}"

# ─── Guardar en CSV ──────────────────────────────────────
def guardar_csv(registros, archivo_salida):
    """Guarda todos los registros en un archivo CSV."""
    campos = [
        "nombre",
        "tipo",
        "link_maps",
        "telefono",
        "email",
        "website",
        "tiene_web",
        "calidad_web",
        "errores_web",
        "observaciones_web",
        "mensaje_personalizado",
        "fecha_prospectado"
    ]
    
    with open(archivo_salida, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        
        for r in registros:
            row = {
                "nombre": r.get("nombre", ""),
                "tipo": r.get("tipo", ""),
                "link_maps": r.get("link_maps", ""),
                "telefono": r.get("telefono", ""),
                "email": r.get("email", ""),
                "website": r.get("website", ""),
                "tiene_web": "Sí" if r.get("tiene_web") else "No",
                "calidad_web": r.get("calidad_web", "Sin web"),
                "errores_web": " | ".join(r.get("errores_web", [])),
                "observaciones_web": r.get("observaciones_web", ""),
                "mensaje_personalizado": r.get("mensaje_personalizado", ""),
                "fecha_prospectado": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            writer.writerow(row)
    
    print_success(f"CSV guardado: {archivo_salida} ({len(registros)} registros)")

# ─── MAIN ────────────────────────────────────────────────
async def main():
    print_header()
    
    # Cargar config
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.md"
    print_step("CONFIG", f"Cargando configuración desde {config_path}...")
    config = load_config(config_path)
    
    print_info(f"Lugar: {config['lugar_busqueda']}")
    print_info(f"Límite: {config['limite_lugares']} lugares")
    print_info(f"Tipos: {', '.join(config['tipos_comercio'][:3])}...")
    print_info(f"Salida: {config['archivo_salida']}")
    print()
    
    # Inicializar Claude
    print_step("CLAUDE", "Conectando con Claude AI...")
    client = get_claude_client()
    print_success("Conexión establecida")
    print()
    
    # Fase 1: Búsqueda en Maps
    print_step("FASE 1", "🗺️  Buscando comercios en Google Maps...")
    print("─" * 55)
    
    comercios = await buscar_en_maps(
        lugar=config["lugar_busqueda"],
        tipos_comercio=config["tipos_comercio"],
        limite=config["limite_lugares"],
        headless=True  # Cambiar a False para ver el browser
    )
    
    if not comercios:
        print_error("No se encontraron comercios. Verificá la conexión a internet.")
        sys.exit(1)
    
    print()
    print_success(f"Total encontrados: {len(comercios)} comercios")
    print()
    
    # Fase 2: Obtener detalles y revisar websites
    print_step("FASE 2", "🔍 Obteniendo detalles y revisando websites...")
    print("─" * 55)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="es-AR"
        )
        page = await context.new_page()
        
        for i, comercio in enumerate(comercios, 1):
            print_step(f"{i}/{len(comercios)}", f"Analizando: {comercio['nombre']}")
            
            # Detalles de Maps
            detalles = await obtener_detalles_maps(comercio, page)
            comercio.update(detalles)
            
            # Revisar website si tiene
            if comercio.get("website"):
                print_info(f"Revisando web: {comercio['website'][:50]}...")
                web_info = await revisar_website(comercio["website"], page)
                comercio["tiene_web"] = web_info["tiene_web"]
                comercio["url_web"] = web_info["url_web"]
                comercio["calidad_web"] = web_info["calidad"]
                comercio["errores_web"] = web_info["errores"]
                comercio["observaciones_web"] = web_info["observaciones"]
                print_info(f"Calidad web: {web_info['calidad']}")
            else:
                comercio["tiene_web"] = False
                comercio["calidad_web"] = "Sin web"
                comercio["errores_web"] = []
                comercio["observaciones_web"] = ""
            
            await asyncio.sleep(1)
        
        await browser.close()
    
    print()
    
    # Fase 3: Generar mensajes con Claude
    print_step("FASE 3", "✍️  Generando mensajes personalizados con Claude...")
    print("─" * 55)
    
    for i, comercio in enumerate(comercios, 1):
        print_step(f"{i}/{len(comercios)}", f"Redactando para: {comercio['nombre']}")
        comercio["mensaje_personalizado"] = generar_mensaje_claude(client, comercio, config)
        print_success(f"  Mensaje generado ({len(comercio['mensaje_personalizado'])} chars)")
        time.sleep(0.5)  # Rate limiting
    
    print()
    
    # Fase 4: Guardar CSV
    print_step("FASE 4", f"💾 Guardando resultados en {config['archivo_salida']}...")
    print("─" * 55)
    guardar_csv(comercios, config["archivo_salida"])
    
    # Resumen final
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}{'═'*55}")
    print("  ✅ PROCESO COMPLETADO")
    print(f"{'═'*55}{Colors.END}")
    print_info(f"Comercios prospectados: {len(comercios)}")
    print_info(f"Con website: {sum(1 for c in comercios if c.get('tiene_web'))}")
    print_info(f"Sin website: {sum(1 for c in comercios if not c.get('tiene_web'))}")
    print_info(f"Con teléfono: {sum(1 for c in comercios if c.get('telefono'))}")
    print_info(f"Archivo generado: {config['archivo_salida']}")
    print()

if __name__ == "__main__":
    asyncio.run(main())
