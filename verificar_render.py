import httpx
import asyncio
from datetime import datetime

# Colores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

async def verificar_servicio(nombre, url):
    """Verifica el health check de un servicio"""
    print(f"\n{BLUE}Verificando {nombre}...{RESET}")
    print(f"URL: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Intentar health check
            response = await client.get(f"{url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"{GREEN}✓ {nombre} está funcionando correctamente{RESET}")
                print(f"  Status: {data.get('status', 'N/A')}")
                print(f"  Service: {data.get('service', 'N/A')}")
                return True
            else:
                print(f"{RED}✗ {nombre} respondió con código {response.status_code}{RESET}")
                return False
                
    except httpx.TimeoutException:
        print(f"{YELLOW}⚠ {nombre} está tardando mucho (puede estar 'despertando' del sleep mode){RESET}")
        print(f"{YELLOW}  Espera 30-60 segundos y vuelve a intentar{RESET}")
        return False
    except Exception as e:
        print(f"{RED}✗ Error al conectar con {nombre}: {str(e)}{RESET}")
        return False

async def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}VERIFICACIÓN DE SERVICIOS EN RENDER{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # IMPORTANTE: Reemplaza estas URLs con las URLs reales de tus servicios en Render
    servicios = {
        "API Gateway": "https://TU-API-GATEWAY.onrender.com",
        "Users Service": "https://TU-USERS-SERVICE.onrender.com",
        "Events Service": "https://TU-EVENTS-SERVICE.onrender.com",
        "Reports Service": "https://TU-REPORTS-SERVICE.onrender.com"
    }
    
    print(f"\n{YELLOW}IMPORTANTE: Actualiza las URLs en este script con tus URLs reales de Render{RESET}")
    print(f"{YELLOW}Busca la sección 'servicios' y reemplaza las URLs{RESET}")
    
    resultados = []
    for nombre, url in servicios.items():
        if "TU-" in url:
            print(f"\n{RED}✗ {nombre}: URL no configurada{RESET}")
            resultados.append(False)
        else:
            resultado = await verificar_servicio(nombre, url)
            resultados.append(resultado)
            await asyncio.sleep(1)  # Pequeña pausa entre requests
    
    # Resumen
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}RESUMEN{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    exitosos = sum(resultados)
    total = len(resultados)
    
    if exitosos == total:
        print(f"{GREEN}✓ Todos los servicios ({exitosos}/{total}) están funcionando correctamente{RESET}")
        print(f"\n{GREEN}¡Listo para continuar con el despliegue del frontend!{RESET}")
    else:
        print(f"{YELLOW}⚠ {exitosos}/{total} servicios funcionando{RESET}")
        print(f"\n{YELLOW}Revisa los servicios que fallaron en Render Dashboard{RESET}")
        print(f"{YELLOW}Verifica que las variables de entorno estén configuradas correctamente{RESET}")

if __name__ == "__main__":
    asyncio.run(main())
