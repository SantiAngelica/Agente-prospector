# 🤖 Agente Prospector de Negocios

Agente de IA que busca comercios locales en Google Maps, analiza sus websites y genera mensajes personalizados para ofrecer servicios de tecnología.

---

## ¿Qué hace?

1. **Busca** comercios en Google Maps según tu ciudad y tipos de negocio
2. **Extrae** teléfono, website, tipo de comercio y link de Maps
3. **Analiza** la calidad del website (si tienen): SSL, mobile-friendly, errores
4. **Genera** con Claude AI un mensaje personalizado para cada comercio
5. **Exporta** todo a un CSV listo para usar

---

## Instalación

### Requisitos previos
- Python 3.9+
- API Key de Anthropic ([obtener aquí](https://console.anthropic.com))

### Pasos

```bash
# 1. Dar permisos al instalador
chmod +x instalar.sh

# 2. Ejecutar instalador
./instalar.sh

# 3. Configurar API Key
export ANTHROPIC_API_KEY='sk-ant-...'

# 4. Activar entorno virtual
source venv/bin/activate

# 5. Ejecutar el agente
python agente.py
```

---

## Configuración (`config.md`)

Editá el archivo `config.md` para personalizar la búsqueda:

| Parámetro | Descripción | Ejemplo |
|---|---|---|
| `lugar_busqueda` | Ciudad o zona a buscar | `"Rosario, Santa Fe"` |
| `limite_lugares` | Máximo de comercios | `20` |
| `tipos_comercio` | Lista de rubros | `restaurantes`, `bares` |
| `tu_nombre` | Tu nombre para los mensajes | `"Juan Pérez"` |
| `tu_empresa` | Tu empresa | `"TechSolutions"` |
| `tu_email` | Tu email de contacto | `"juan@tech.com"` |
| `archivo_salida` | Nombre del CSV | `"prospectos.csv"` |

---

## Estructura del CSV de salida

| Columna | Descripción |
|---|---|
| nombre | Nombre del comercio |
| tipo | Tipo de negocio (restaurante, bar, etc.) |
| link_maps | URL de Google Maps |
| telefono | Teléfono extraído |
| email | Email (si se encontró) |
| website | Sitio web propio |
| tiene_web | Sí / No |
| calidad_web | Buena / Regular / Mejorable / Sin web |
| errores_web | Problemas detectados en el sitio |
| mensaje_personalizado | Mensaje generado por Claude AI |
| fecha_prospectado | Fecha y hora del relevamiento |

---

## Uso avanzado

```bash
# Usar un config personalizado
python agente.py mi-ciudad.md

# Ver el browser mientras trabaja (debug)
# Cambiar en agente.py: headless=False
```

---

## Ejemplo de mensaje generado

> **Para: Pizzería El Hornito**
>
> Hola! Vi la Pizzería El Hornito en Maps y noté que no tienen web propia. ¿Sabían que con una landing page sencilla podrían recibir pedidos online y aparecer primero en Google cuando alguien busca pizza en su zona? 
>
> Trabajo con negocios locales creando sitios web, sistemas de pedidos y hasta agentes de IA que atienden consultas por WhatsApp automáticamente.
>
> ¿Les gustaría que charlemos? Juan - TechSolutions - +54 9 11 XXXX-XXXX

---

>[!IMPORTANT]
> El agente respeta los tiempos de carga de Google Maps para no ser bloqueado
>[!TIP]
> Podés editar `config.md` sin tocar código Python
>[!TIP]
> Los mensajes son únicos para cada comercio gracias a Claude AI
