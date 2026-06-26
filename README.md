# Sancho ACP Clients

Este repositorio contiene un conjunto de clientes diseñados para interactuar con el agente cognitivo del robot móvil **Sancho** a través del protocolo **ACP (Agent Client Protocol)**.

## Clientes Disponibles

El repositorio está organizado en tres componentes principales:

### 1. [sancho_cli](sancho_cli/) (Cliente de Consola)
Un cliente en línea de comandos (CLI) interactivo basado en terminal.
* **Características**: Conexión TCP directa, soporte para entrada multilínea (usando `\`), visualización en tiempo real de los pensamientos (`💭`), planes y herramientas del agente, así como gestión interactiva de solicitudes de permisos.

### 2. [sancho_mobile](sancho_mobile/) (Cliente Móvil)
Una aplicación que simula la interfaz de un smartphone, desarrollada con **Flet** (Material Design 3 para Python).
* **Características**: Interfaz de chat moderna, visualización en flujo de pensamientos, tarjetas dinámicas para el estado de ejecución de herramientas y diálogos interactivos para autorizar o denegar acciones protegidas.

### 3. [acp_tcp_stdio_bridge](acp_tcp_stdio_bridge/) (Puente TCP-Stdio)
Un puente adaptador bidireccional entre la entrada/salida estándar (stdio) y sockets TCP de red.
* **Propósito**: Permite utilizar clientes ACP de código abierto que solo soportan comunicación por stdio (como **acp-ui**) a través de la red, redirigiendo de manera bidireccional los flujos de datos hacia el puerto TCP donde corre el servidor de Sancho.

---

## Requisitos Previos

Asegúrate de tener instalado Python 3 y un entorno virtual configurado en cada carpeta según se describe en sus respectivos READMEs.

Para probar la conexión general con el robot:
* Host por defecto: `sancho.isa.uma.es`
* Puerto por defecto: `9100`
