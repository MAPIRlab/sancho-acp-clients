# ACP TCP Stdio Bridge

Este directorio contiene un **puente stdio-a-TCP** (`stdio-to-TCP bridge`) para el servidor Sancho ACP. Dado que muchos clientes y editores (como `acp-ui` u otras herramientas de integración) solo soportan la comunicación con agentes ACP a través de la entrada/salida estándar (stdio), esta herramienta se comunica localmente por pipes stdin/stdout y redirige de forma bidireccional los datos hacia el socket de red TCP donde corre el servidor principal `sancho_acp` en el robot.

## Estructura del Repositorio

- `acp_tcp_stdio_adapter.py`: Script de Python nativo (sin dependencias externas) que redirige bidireccionalmente los flujos de `stdin` y del Socket TCP.
- `run_acp_tcp_stdio_adapter.sh`: Script bash de lanzamiento optimizado para resolver rutas relativas de ejecución y aislar el entorno de Python de posibles colisiones.
- `test_adapter.py`: Suite de pruebas unitarias automatizadas que comprueba el correcto funcionamiento del puente localmente.
- `.env`: Archivo de configuración opcional para valores por defecto (host y puerto).

## Configuración en el Cliente (acp-ui)

Para añadir el agente en el cliente **acp-ui** (PC local), debes editar o crear el archivo de configuración en `~/.config/acp-ui/agents.json` e incluir la definición del agente:

```json
{
  "agents": {
    "Sancho ACP Agent": {
      "command": "/ruta/a/tu/repositorio/sancho_acp_clients/acp_tcp_stdio_bridge/run_acp_tcp_stdio_adapter.sh",
      "args": [
        "--host", "sancho.isa.uma.es",
        "--port", "9100",
        "--connect-retries", "120",
        "--retry-delay", "0.5"
      ],
      "env": {}
    }
  }
}
```

## Pruebas de Funcionamiento

### Pruebas Unitarias Locales
Puedes ejecutar la suite de pruebas unitarias locales con:
```bash
python3 test_adapter.py
```

### Ejecución Manual desde Consola
Para probar que el adaptador logra conectar directamente contra el robot remoto:
```bash
./run_acp_tcp_stdio_adapter.sh --host sancho.isa.uma.es --port 9100 --connect-retries 5 --retry-delay 0.5 --verbose < /dev/null
```

---

## Solución de Problemas (Troubleshooting)

### 1. Error de Python en AppImage (`Fatal Python error: init_fs_encoding`)
- **Problema:** Al lanzar el agente desde `acp-ui` se cerraba inmediatamente arrojando el error `ModuleNotFoundError: No module named 'encodings'`.
- **Causa:** El AppImage de `acp-ui` inyecta variables de entorno `PYTHONHOME` y `PYTHONPATH` que apuntan a su montaje interno temporal. Cuando el script intentaba llamar al `python3` del sistema, este heredaba esas rutas erróneas y fallaba al cargar sus módulos base.
- **Solución:** El script `run_acp_tcp_stdio_adapter.sh` ya limpia estas variables haciendo `unset PYTHONHOME` y `unset PYTHONPATH` antes de lanzar Python, aislando la ejecución y permitiendo al intérprete funcionar correctamente con la librería estándar de tu sistema operativo.

### 2. Error en el Cliente (`Agent not found: <UUID>`)
- **Problema:** `acp-ui` muestra el error de que no encuentra el agente por su identificador UUID.
- **Causa:** La base de datos local y la caché de Tauri/localstorage en `acp-ui` se corrompen debido a intentos de conexión fallidos anteriores, manteniendo mapeados de UUID obsoletos en lugar de leer el archivo físico.
- **Solución:**
  1. Cierra completamente `acp-ui`.
  2. Limpia la carpeta de configuración y el local storage de Tauri ejecutando:
     ```bash
     rm -rf ~/.config/acp-ui/ ~/.local/share/formulahendry.acp-ui/
     ```
  3. Crea de nuevo el directorio de configuración:
     ```bash
     mkdir -p ~/.config/acp-ui/
     ```
  4. Vuelve a guardar el archivo `agents.json` con la configuración deseada y abre de nuevo `acp-ui`.
