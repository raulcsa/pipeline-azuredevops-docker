# Pipeline CI/CD con Docker y Azure DevOps

> Proyecto de aprendizaje de nivel intermedio — automatización completa del ciclo de vida de una aplicación Python en contenedores, desde el commit hasta producción en Azure.

---

## Índice

1. [¿Qué es este proyecto?](#1-qué-es-este-proyecto)
2. [Arquitectura y flujo del pipeline](#2-arquitectura-y-flujo-del-pipeline)
3. [Tecnologías utilizadas](#3-tecnologías-utilizadas)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Prerequisitos](#5-prerequisitos)
6. [Paso 1 — La aplicación Python](#6-paso-1--la-aplicación-python)
7. [Paso 2 — El Dockerfile](#7-paso-2--el-dockerfile)
8. [Paso 3 — Configurar Azure](#8-paso-3--configurar-azure)
9. [Paso 4 — Configurar Azure DevOps](#9-paso-4--configurar-azure-devops)
10. [Paso 5 — El pipeline YAML](#10-paso-5--el-pipeline-yaml)
11. [Paso 6 — Aprobaciones y entornos](#11-paso-6--aprobaciones-y-entornos)
12. [Verificación end-to-end](#12-verificación-end-to-end)
13. [Conceptos clave aprendidos](#13-conceptos-clave-aprendidos)
14. [Recursos adicionales](#14-recursos-adicionales)

---

## 1. ¿Qué es este proyecto?

Este proyecto implementa un **pipeline de integración y entrega continua (CI/CD)** para una aplicación web Python usando Docker y Azure DevOps.

El objetivo es que cada vez que un desarrollador hace `git push`, el sistema automáticamente:

1. **Construye** la aplicación dentro de un contenedor Docker
2. **Ejecuta los tests** para detectar errores antes de llegar a producción
3. **Publica la imagen** en un registro privado de Azure (ACR)
4. **Despliega** la nueva versión en Azure App Service tras una aprobación manual

### ¿Por qué es útil esto?

Sin CI/CD, el proceso de desplegar código es manual, lento y propenso a errores. Con este pipeline, el proceso es reproducible, auditado y mucho más seguro: **el código roto nunca llega a producción**.

---

## 2. Arquitectura y flujo del pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUJO COMPLETO                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Developer                                                      │
│     │                                                           │
│     │  git push → main                                          │
│     ▼                                                           │
│  Azure DevOps (trigger automático)                              │
│     │                                                           │
│     ├─── ETAPA CI ─────────────────────────────────────────┐   │
│     │    1. docker build  →  imagen construida              │   │
│     │    2. pytest tests  →  3 tests ✓ / error ✗ (para)    │   │
│     │    3. docker push   →  imagen en ACR con tag único    │   │
│     └────────────────────────────────────────────────────── ┘   │
│     │                                                           │
│     ├─── ETAPA CD ─────────────────────────────────────────┐   │
│     │    4. ⏸ Espera aprobación manual (email al equipo)   │   │
│     │    5. Deploy imagen:N → Azure App Service             │   │
│     │    6. curl /health   → 200 OK ✓                       │   │
│     └────────────────────────────────────────────────────── ┘   │
│     │                                                           │
│     ▼                                                           │
│  https://mi-app.azurewebsites.net  ← app en producción         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

<!-- 📸 CAPTURA SUGERIDA: Vista general del pipeline en Azure DevOps mostrando las dos etapas CI y CD -->

---

## 3. Tecnologías utilizadas

| Tecnología | Rol en el proyecto | Por qué |
|---|---|---|
| **Python + Flask** | La aplicación web | Framework minimalista, ideal para APIs |
| **pytest** | Tests automáticos | Estándar de facto en Python |
| **Docker** | Empaquetado en contenedor | Garantiza que funciona igual en todos los entornos |
| **Azure Container Registry (ACR)** | Almacén privado de imágenes | Registro privado integrado con el resto de Azure |
| **Azure App Service** | Servidor donde corre la app | PaaS gestionado, sin administrar VMs |
| **Azure DevOps Pipelines** | Orquestador del CI/CD | Integración nativa con Azure y repositorio Git |
| **YAML** | Definición del pipeline | El pipeline como código — versionado en Git |

---

## 4. Estructura del repositorio

```
mi-app-cicd/
├── app.py                  ← API Flask con 3 rutas (/, /health, /suma)
├── test_app.py             ← Tests automáticos con pytest
├── requirements.txt        ← Dependencias Python con versiones fijadas
├── Dockerfile              ← Receta para construir el contenedor
├── azure-pipelines.yml     ← Definición del pipeline CI/CD
└── .gitignore              ← Archivos a ignorar por Git
```

---

## 5. Prerequisitos

### Herramientas locales

- [Docker](https://www.docker.com/products/docker-desktop/) — para construir y probar contenedores en local
- [Azure CLI](https://aka.ms/installazurecliwindows) — para crear recursos en Azure desde la terminal
- [Git](https://git-scm.com/) — control de versiones
- [Python 3.11+](https://www.python.org/) — para ejecutar la app en local si es necesario
- [VS Code](https://code.visualstudio.com/) — editor recomendado

### Cuentas cloud necesarias

- **Azure** — regístrate en [portal.azure.com](https://portal.azure.com) (200€ de crédito gratuito para nuevas cuentas)
- **Azure DevOps** — regístrate en [dev.azure.com](https://dev.azure.com) (gratis para equipos pequeños)

### Verificar instalaciones

```bash
docker --version    
az --version        
git --version       
python --version    

# Iniciar sesión en Azure (abre el navegador)
az login
```

---

## 6. Paso 1 — La aplicación Python

La aplicación es una API REST minimalista con Flask. Tiene tres rutas:

- `GET /` — devuelve un JSON de bienvenida con la versión y el entorno
- `GET /health` — ruta de health check, usada por el pipeline para verificar que el despliegue funcionó
- `GET /suma/<a>/<b>` — suma dos números, usada para demostrar lógica testeable

### `app.py`

```python
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'mensaje': 'Hola desde el contenedor Docker!',
        'version': '1.0.0',
        'entorno': os.getenv('ENTORNO', 'local')
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/suma/<int:a>/<int:b>')
def suma(a, b):
    return jsonify({'resultado': a + b})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### `test_app.py`

Los tests son fundamentales: si alguno falla, el pipeline se detiene y no despliega nada.

```python
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b'Hola' in res.data

def test_health(client):
    res = client.get('/health')
    assert res.status_code == 200

def test_suma(client):
    res = client.get('/suma/3/4')
    data = res.get_json()
    assert data['resultado'] == 7
```

### `requirements.txt`

```
flask==3.0.3
pytest==8.2.0
```

> **¿Por qué fijar versiones exactas (`==`)?** Para garantizar que el contenedor construido hoy es idéntico al que se construirá en seis meses. Sin versiones fijas, una actualización de librería podría romper el pipeline sin que nadie haya cambiado código.

### Probar en local antes de dockerizar

```bash
pip install -r requirements.txt
python app.py
# Abrir http://localhost:5000/health
```

---

## 7. Paso 2 — El Dockerfile

El Dockerfile es la "receta" que convierte el código Python en una imagen Docker ejecutable en cualquier entorno.

```dockerfile
# Imagen base oficial de Python — versión slim reduce el tamaño ~80%
FROM python:3.12-slim AS base

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements PRIMERO
# Si el código cambia pero no las dependencias, Docker reutiliza esta capa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Variables de entorno
ENV FLASK_ENV=production
ENV ENTORNO=produccion

# Puerto que expone la aplicación (solo informativo)
EXPOSE 5000

# Comando de arranque
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
```

### Probar el contenedor en local

```bash
# Construir la imagen
docker build -t mi-app:local .

# Ejecutar el contenedor
docker run -p 5000:5000 mi-app:local

# Verificar que funciona
curl http://localhost:5000/health

# Ejecutar los tests dentro del contenedor
docker run --rm mi-app:local python -m pytest test_app.py -v
```

<img width="1203" height="206" alt="image" src="https://github.com/user-attachments/assets/c5852df8-4765-414f-979e-cdbf2bacbe96" />


---

## 8. Paso 3 — Configurar Azure

Necesitamos crear dos recursos principales en Azure:

- **Azure Container Registry (ACR)** — registro privado donde el pipeline almacena las imágenes Docker
- **Azure App Service** — el servidor gestionado donde correrá la aplicación en producción

### Crear recursos con Azure CLI

```bash
# 1. Resource Group — agrupa y organiza todos los recursos del proyecto
az group create \
  --name rg-miapp-cicd \
  --location westeurope

# 2. Azure Container Registry
az acr create \
  --resource-group rg-miapp-cicd \
  --name miappcicdacr \
  --sku Basic

# 3. Habilitar acceso admin (necesario para que el pipeline pueda hacer push)
az acr update \
  --name miappcicdacr \
  --admin-enabled true

# 4. Ver las credenciales del ACR (guárdalas, las necesitarás en DevOps)
az acr credential show --name miappcicdacr

# 5. App Service Plan (servidor Linux subyacente)
az appservice plan create \
  --name plan-miapp \
  --resource-group rg-miapp-cicd \
  --is-linux \
  --sku B1

# 6. Web App configurada para correr contenedores Docker
az webapp create \
  --resource-group rg-miapp-cicd \
  --plan plan-miapp \
  --name mi-app-cicd-demo \
  --deployment-container-image-name miappcicdacr.azurecr.io/mi-app:latest
```

<img width="1679" height="568" alt="image" src="https://github.com/user-attachments/assets/a593aa4a-b197-49f6-99bd-e018695257e1" />


> **Nota:** Los nombres de ACR y Web App deben ser **únicos globalmente**. Si obtienes error de nombre en uso, añade un sufijo numérico: `miappcicdacr2025`.

---

## 9. Paso 4 — Configurar Azure DevOps

### Crear el proyecto

1. Ve a [dev.azure.com](https://dev.azure.com) e inicia sesión
2. Haz clic en **+ New project** → nombre: `mi-app-cicd` → Visibility: Private → **Create**



### Subir el código al repositorio

```bash
# Dentro de la carpeta del proyecto
git add .
git commit -m "feat: app Python + Dockerfile + pipeline inicial"
git remote add origin https://dev.azure.com/TU-ORG/mi-app-cicd/_git/mi-app-cicd
git push -u origin main
```
<img width="1679" height="701" alt="image" src="https://github.com/user-attachments/assets/a129e745-180d-45e3-bb18-e7f76857b0ac" />

### Crear las Service Connections

Las Service Connections son las credenciales que permiten al pipeline autenticarse con Azure y con el ACR. Sin ellas, el pipeline no puede subir imágenes ni desplegar.

#### Service Connection 1 — Azure Container Registry

1. En Azure DevOps: **Project Settings** (icono de engranaje, abajo izquierda)
2. Menú izquierdo → **Pipelines** → **Service connections** → **New service connection**
3. Tipo: **Docker Registry** → Next
4. Registry type: **Azure Container Registry**
5. Selecciona tu suscripción y el ACR `miappcicdacr`
6. Nombre de la conexión: `conexion-acr`
7. **Save**

<img width="477" height="785" alt="image" src="https://github.com/user-attachments/assets/e2ef7532-90b0-4590-adc8-f2b5c3b0b7bf" />


#### Service Connection 2 — Azure Resource Manager

1. **New service connection** → tipo: **Azure Resource Manager** → Next
2. Authentication method: **Service principal (automatic)**
3. Scope: **Subscription** → selecciona tu suscripción Azure
4. Nombre: `conexion-azure`
5. **Save**

<img width="474" height="888" alt="image" src="https://github.com/user-attachments/assets/809c99a3-3798-4503-96bc-f63f19d9aeec" />

<img width="1386" height="458" alt="image" src="https://github.com/user-attachments/assets/c0d37d3e-c03d-4f88-8c90-bab40b3dc97f" />



---

## 10. Paso 5 — El pipeline YAML

El archivo `azure-pipelines.yml` define todo el pipeline como código. Al estar en el repositorio, cualquier cambio al pipeline queda registrado en Git con su historial de cambios.

### `azure-pipelines.yml`

```yaml
# Trigger: ejecutar el pipeline ante cada push a main
trigger:
  branches:
    include:
      - main
  paths:
    exclude:
      - README.md

# Variables reutilizables en todo el pipeline
variables:
  acrName: 'miappcicdacr'
  acrLoginServer: 'miappcicdacr.azurecr.io'
  imageName: 'mi-app'
  imageTag: '$(Build.BuildId)'     # ID único por cada ejecución del pipeline
  webAppName: 'mi-app-cicd-demo'
  resourceGroup: 'rg-miapp-cicd'

stages:

  # ── ETAPA CI: construir, testear y publicar ──────────────────
  - stage: CI
    displayName: 'CI — Build, Test y Push'
    jobs:
      - job: BuildTestPush
        pool:
          vmImage: 'ubuntu-latest'   # Azure provisiona una VM limpia para cada build
        steps:

          # Autenticarse en el ACR
          - task: Docker@2
            displayName: 'Login en Azure Container Registry'
            inputs:
              command: login
              containerRegistry: 'conexion-acr'

          # Construir la imagen Docker
          - task: Docker@2
            displayName: 'Build de la imagen Docker'
            inputs:
              command: build
              dockerfile: 'Dockerfile'
              repository: '$(acrLoginServer)/$(imageName)'
              tags: |
                $(imageTag)
                latest

          # Ejecutar los tests dentro del contenedor
          # Si fallan → el pipeline se detiene aquí, no se publica nada
          - script: |
              docker run --rm \
                $(acrLoginServer)/$(imageName):$(imageTag) \
                python -m pytest test_app.py -v
            displayName: 'Ejecutar tests en el contenedor'

          # Si los tests pasan → publicar la imagen en el ACR
          - task: Docker@2
            displayName: 'Push imagen a ACR'
            inputs:
              command: push
              repository: '$(acrLoginServer)/$(imageName)'
              tags: |
                $(imageTag)
                latest

  # ── ETAPA CD: desplegar a producción ────────────────────────
  - stage: CD
    displayName: 'CD — Desplegar a producción'
    dependsOn: CI          # Solo se ejecuta si CI tuvo éxito completo
    condition: succeeded()
    jobs:
      - deployment: DeployApp
        environment: 'produccion'   # Aquí se configura la aprobación manual
        pool:
          vmImage: 'ubuntu-latest'
        strategy:
          runOnce:
            deploy:
              steps:

                # Actualizar la imagen en el App Service
                - task: AzureWebAppContainer@1
                  displayName: 'Actualizar contenedor en App Service'
                  inputs:
                    azureSubscription: 'conexion-azure'
                    appName: '$(webAppName)'
                    containers: '$(acrLoginServer)/$(imageName):$(imageTag)'

                # Verificar que la aplicación arrancó correctamente
                - script: |
                    echo "Esperando arranque de la app..."
                    sleep 30
                    curl -f https://$(webAppName).azurewebsites.net/health || exit 1
                    echo "Aplicacion en produccion correctamente"
                  displayName: 'Health check post-deploy'
```

### Conectar el pipeline en Azure DevOps

1. Menú izquierdo → **Pipelines** → **New pipeline**
2. Origen del código: **Azure Repos Git**
3. Selecciona el repositorio `mi-app-cicd`
4. Configuración: **Existing Azure Pipelines YAML file**
5. Selecciona `/azure-pipelines.yml` → **Continue** → **Run**

<!-- 📸 CAPTURA SUGERIDA: Pipeline ejecutándose en Azure DevOps, mostrando los pasos de la etapa CI en verde -->

<!-- 📸 CAPTURA SUGERIDA: Log detallado del paso "Ejecutar tests en el contenedor" mostrando "3 passed" -->

<!-- 📸 CAPTURA SUGERIDA: Azure Container Registry mostrando el repositorio "mi-app" con los tags de imagen -->

---

## 11. Paso 6 — Aprobaciones y entornos

Los Environments de Azure DevOps permiten pausar el pipeline antes de desplegar a producción hasta que alguien del equipo apruebe manualmente.

### Configurar la aprobación

1. En Azure DevOps → **Pipelines** → **Environments**
2. Haz clic en el environment **produccion** (se creó automáticamente al ejecutar el pipeline)
3. Icono de tres puntos `...` → **Approvals and checks**
4. **+ Add check** → selecciona **Approvals**
5. Añade tu usuario como aprobador → timeout: 24 horas → **Create**

<!-- 📸 CAPTURA SUGERIDA: Pantalla de "Approvals and checks" del environment "produccion" con el aprobador configurado -->

### ¿Qué ocurre en la próxima ejecución?

Cuando el pipeline llegue a la etapa CD:

1. Azure DevOps envía un **email de notificación** al aprobador
2. El pipeline queda **pausado** — puede esperar horas sin problema
3. El aprobador entra a Azure DevOps, revisa y hace clic en **Approve**
4. El despliegue continúa automáticamente

<!-- 📸 CAPTURA SUGERIDA: Banner de aprobación pendiente en Azure DevOps con el botón "Review" -->

<!-- 📸 CAPTURA SUGERIDA: Diálogo de aprobación con el botón "Approve" y campo de comentario -->

---

## 12. Verificación end-to-end

Una vez configurado todo, el flujo completo funciona así:

### Test básico

```bash
# 1. Hacer un cambio en la aplicación
# Edita app.py: cambia 'version': '1.0.0' por '1.1.0'

# 2. Commit y push — dispara el pipeline automáticamente
git add app.py
git commit -m "feat: actualizar a version 1.1.0"
git push origin main

# 3. Ir a Azure DevOps → Pipelines para ver la ejecución en tiempo real

# 4. Una vez desplegado, verificar en producción
curl https://mi-app-cicd-demo.azurewebsites.net/
curl https://mi-app-cicd-demo.azurewebsites.net/health
curl https://mi-app-cicd-demo.azurewebsites.net/suma/10/5
```

### Simular un fallo de tests (demostración de seguridad)

```python
# Añade esto a test_app.py y haz push:
def test_que_falla(client):
    assert 1 == 2  # Siempre falla
```

El pipeline fallará en la etapa de tests → **no se publicará ninguna imagen** → **nada llegará a producción**. Esta es la protección más importante del CI/CD.

<!-- 📸 CAPTURA SUGERIDA: Pipeline con la etapa CI en rojo por fallo de tests, y la etapa CD sin ejecutarse -->

### Verificar el historial de imágenes en el ACR

```bash
# Listar todas las imágenes publicadas
az acr repository show-tags \
  --name miappcicdacr \
  --repository mi-app \
  --orderby time_desc \
  --output table
```

<!-- 📸 CAPTURA SUGERIDA: Portal Azure → ACR → Repositorios, mostrando el listado de tags por build -->

---

## 13. Conceptos clave aprendidos

### CI — Integración Continua
Práctica de integrar cambios de código frecuentemente y verificarlos con tests automáticos. Detecta errores rápido, antes de que se acumulen.

### CD — Entrega Continua
Extensión del CI que automatiza el proceso de despliegue. El código que pasa los tests puede llegar a producción con mínima intervención manual.

### Docker y la inmutabilidad
Cada imagen tiene un tag único (el `BuildId`). Esto significa que siempre podemos volver a una versión anterior exacta, y que lo que se despliega en producción es exactamente lo mismo que se testó en CI.

### Infrastructure as Code (IaC)
El pipeline está definido en un archivo YAML que vive en el repositorio. Los cambios al pipeline tienen historial, se pueden revisar en PRs y se pueden revertir como cualquier otro cambio de código.

### Aprobaciones como control de calidad
La aprobación manual no es una limitación — es una decisión consciente de que alguien con contexto revise antes de afectar a usuarios reales.

---

## 14. Recursos adicionales

- [Documentación oficial Azure Pipelines](https://learn.microsoft.com/es-es/azure/devops/pipelines/)
- [Documentación Azure Container Registry](https://learn.microsoft.com/es-es/azure/container-registry/)
- [Documentación Azure App Service (contenedores)](https://learn.microsoft.com/es-es/azure/app-service/configure-custom-container)
- [Flask — documentación oficial](https://flask.palletsprojects.com/)
- [Docker — guía de buenas prácticas para Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [pytest — documentación oficial](https://docs.pytest.org/)

---

## Autor

Proyecto desarrollado como ejercicio de aprendizaje de Docker, CI/CD y Azure DevOps.

---

*Última actualización: Marzo 2026*
