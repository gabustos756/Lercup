# Lercup 🎾 - MVP de Gestión de Torneos de Tenis

Este es un MVP (Mínimo Producto Viable) web desarrollado en Python para la organización, administración y gestión de torneos de tenis. Está construido bajo un enfoque **Server-Rendered (renderizado del lado servidor)** utilizando **FastAPI**, **Jinja2** para las vistas, **SQLModel** (que combina SQLAlchemy y Pydantic) para la base de datos y validaciones, y **Alembic** para las migraciones de esquema.

---

## 1. Alcance y Funcionalidades del MVP

El proyecto cubre las necesidades esenciales de administración deportiva en un portal web responsive:

- **Autenticación Segura**: Sistema de sesión basado en cookies seguras utilizando `SessionMiddleware` con contraseñas encriptadas mediante `passlib` (algoritmo bcrypt).
- **Perfiles Deportivos Enriquecidos**: Cada jugador dispone de datos de contacto, ciudad de residencia, URL de avatar y detalles técnicos (nivel de habilidad y mano hábil).
- **Cálculo Dinámico de Estadísticas**: Procesamiento automático y en tiempo real en la capa de servicios para calcular partidos jugados, partidos ganados, perdidos y porcentaje de victorias (*win rate*).
- **Gestión de Torneos (ABM)**: Creación de torneos indicando tipo de superficie (arcilla, césped, cemento, indoor) y estados del campeonato (borrador, activo, finalizado).
- **Historial y Registro de Partidos**: Los administradores pueden registrar los resultados de los partidos (scores en formato sets, ej. `6-4, 7-5`) asociando contrincantes y el ganador correspondiente.
- **Diseño Premium**: Interfaz moderna, limpia y sobria construida con Vanilla CSS y un diseño responsive móvil + desktop.
- **Arquitectura Preparada para SPA**: Estructura de controladores dividida para permitir la coexistencia de vistas HTML clásicas y respuestas en JSON REST API.

---

## 2. Estructura Completa del Proyecto

La base de código sigue un patrón arquitectónico por capas limpio y desacoplado:

```text
Lercup/
├── requirements.txt         # Dependencias de Python
├── .env.example             # Configuración de variables de entorno
├── alembic.ini              # Configuración del motor de migraciones
├── database.db              # Base de datos SQLite local (creada automáticamente)
├── README.md                # Esta guía
├── migrations/              # Archivos y revisiones de Alembic
└── app/
    ├── main.py              # Punto de entrada principal y configuración de FastAPI
    ├── core/                # Configuraciones core
    │   ├── config.py        # Configuración de entornos y variables (.env)
    │   ├── database.py      # Conexión, motor (engine) y sesiones de base de datos
    │   ├── security.py      # Utilidades de hashing y dependencias de autenticación
    │   └── templates.py     # Utilidades para renderizado y flash messages de Jinja2
    ├── models/              # Modelos ORM relacionales (SQLModel)
    │   ├── __init__.py      # Registro centralizado de modelos para Alembic
    │   ├── user.py          # Entidad de Usuarios y permisos
    │   ├── player_profile.py# Perfil deportivo multi-deporte asociado al usuario
    │   ├── tournament.py    # Entidad de Campeonatos
    │   ├── registration.py  # Inscripción de jugadores a torneos
    │   └── match.py         # Resultados de partidos y sets
    ├── schemas/             # Validadores de datos y tipados de entrada/salida (Pydantic)
    │   ├── user.py
    │   └── tournament.py
    ├── services/            # Lógica de negocio y consultas transaccionales
    │   ├── __init__.py      # Exportación de servicios
    │   ├── auth_service.py  # Registro, inicio de sesión y validación de hash
    │   ├── user_service.py  # ABM de usuarios y procesamiento de estadísticas
    │   └── tournament_service.py # Creación de torneos, fixtures e inscripciones
    ├── routes/              # Controladores de rutas de la aplicación
    │   ├── web/             # Rutas server-rendered que retornan HTML
    │   │   ├── home.py      # Dashboard principal
    │   │   ├── auth.py      # Flujo de login, registro y logout
    │   │   ├── users.py     # ABM web de usuarios y perfil
    │   │   └── tournaments.py# ABM web de torneos, inscripciones y partidos
    │   └── api/             # Rutas de uso futuro REST JSON (desacopladas)
    │       ├── __init__.py  # Enrutador raíz con prefijo `/api`
    │       ├── auth.py      # Autenticación JSON
    │       ├── users.py     # Listado y estadísticas JSON
    │       └── tournaments.py# Datos de torneos y partidos JSON
    ├── static/              # Recursos web estáticos
    │   ├── css/
    │   │   └── app.css      # Estilos premium del MVP
    │   └── js/
    │       └── app.js       # Interactividad (alertas, confirmaciones, menú móvil)
    └── templates/           # Vistas Jinja2 (HTML5)
        ├── base.html        # Plantilla base y navegación responsive
        ├── index.html       # Página de bienvenida / Inicio
        ├── auth/            # Vistas de autenticación (login, register)
        ├── users/           # Vistas de administración de usuarios y perfil deportivo
        └── tournaments/     # Vistas de campeonatos y registro de partidos
```

---

## 3. Conexión a Base de Datos y Configuración

El proyecto utiliza **SQLModel** (con SQLAlchemy por debajo) para manejar la base de datos de manera transparente y agnóstica.

> [!IMPORTANT]
> **Estrategia de Motores de Base de Datos:**
> - **Entorno Local (Desarrollo):** Se utiliza **SQLite** (`sqlite:///database.db`) para agilizar el desarrollo local y las pruebas sin necesidad de levantar servicios de bases de datos externas.
> - **Entorno de Producción / Staging:** Se utiliza **PostgreSQL** mediante la configuración de `DATABASE_URL` en el entorno o archivo `.env`. SQLModel/SQLAlchemy abstrae el acceso para que el backend funcione indistintamente con ambos motores.

### Variables de Entorno (`.env`)
Configura el archivo `.env` en la raíz del proyecto para definir qué motor de base de datos utilizar:

```env
ENV=development
SECRET_KEY=clave_secreta_para_las_cookies_de_sesion
DATABASE_URL=sqlite:///database.db
```

- **SQLite (Local):** Por defecto se inicializa con SQLite (`sqlite:///database.db`). Excelente para pruebas e iteración inmediata.
- **PostgreSQL (Producción):** Para producción, define la cadena de conexión estándar en tu archivo `.env`:
  ```env
  DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/nombre_bd
  ```

Las dependencias e inicialización de las tablas de base de datos se manejan a través de `app/core/database.py`.

---

## 4. Entidades y Modelos de Datos

```mermaid
erDiagram
    USER {
        int id PK
        string email UK
        string hashed_password
        string full_name
        string city
        string avatar_url
        bool is_admin
        string role
        datetime created_at
    }
    PLAYER_PROFILE {
        int id PK
        int user_id FK
        string sport
        string skill_level
        string hand_preference
        string notes
        datetime created_at
    }
    TOURNAMENT {
        int id PK
        string name
        string description
        datetime start_date
        datetime end_date
        string surface
        string status
        int creator_id FK
        string sport
        datetime created_at
    }
    TOURNAMENT_REGISTRATION {
        int id PK
        int tournament_id FK
        int user_id FK
        datetime registered_at
        string status
    }
    MATCH {
        int id PK
        int tournament_id FK
        int player1_id FK
        int player2_id FK
        int winner_id FK
        string score
        datetime match_date
    }

    USER ||--o{ PLAYER_PROFILE : "has"
    USER ||--o{ TOURNAMENT : "creates"
    USER ||--o{ TOURNAMENT_REGISTRATION : "subscribes"
    TOURNAMENT ||--o{ TOURNAMENT_REGISTRATION : "contains"
    TOURNAMENT ||--o{ MATCH : "includes"
    USER ||--o{ MATCH : "competes in"
```

### Detalle de Modelos (ORM):
1. **`User`** (`app/models/user.py`):
   - Almacena las credenciales, el estado administrativo (`is_admin`) y el rol (`role`).
   - Los roles disponibles son:
     - `admin`: Superadministrador con acceso total a la gestión de usuarios y torneos.
     - `tournament_admin`: Organizador de torneos con permiso para crear/editar torneos y registrar marcadores de partidos.
     - `player`: Jugador regular (por defecto), con permisos para ver resultados, inscribirse en torneos y editar su propio perfil.
   - Posee relaciones de cascada (`all, delete-orphan`) con `PlayerProfile` y `TournamentRegistration`.
2. **`PlayerProfile`** (`app/models/player_profile.py`):
   - Atributos: `sport` (por defecto "tennis"), `skill_level` (beginner, intermediate, advanced) y `hand_preference` (right, left).
   - Clave única compuesta en (`user_id`, `sport`) para evitar perfiles duplicados del mismo deporte por usuario.
3. **`Tournament`** (`app/models/tournament.py`):
   - Campos de vigencia (`start_date`, `end_date`), superficie de juego (`surface`: clay, grass, hard, indoor) y estado (`status`: draft, ongoing, finished).
4. **`TournamentRegistration`** (`app/models/registration.py`):
   - Registro de inscripciones de usuarios. Clave única compuesta en (`tournament_id`, `user_id`).
5. **`Match`** (`app/models/match.py`):
   - Referencia al torneo y a los dos contrincantes (`player1_id`, `player2_id`).
   - Identifica opcionalmente al ganador (`winner_id`) y el marcador del partido (`score`, ej: `6-2, 6-4`).

---

## 5. Páginas y Vistas Disponibles (HTML Server-Rendered)

- **Inicio / Dashboard (`/`)**: Muestra un listado de los torneos activos e históricos, detallando fechas, superficies y estados.
- **Login (`/auth/login`)**: Formulario limpio de inicio de sesión con alertas de error o éxito.
- **Registro (`/auth/register`)**: Formulario para nuevos jugadores. Crea automáticamente un perfil de tenis por defecto.
- **Listado de Usuarios (`/users`)**: Tabla administrativa que muestra los jugadores con sus avatares, ciudades, roles y acciones de administración (Editar / Eliminar).
- **Creación / Edición de Usuarios (`/users/create` y `/users/edit/{id}`)**: Formulario unificado para modificar datos personales y técnicos (habilidad, mano hábil) del jugador.
- **Detalle de Perfil (`/users/profile/{id}`)**: Tarjeta con avatar, ciudad y estadísticas completas de rendimiento (victorias, derrotas, win rate) junto a su historial cronológico de partidos.
- **Edición de Mi Perfil (`/users/profile/edit`)**: Formulario de autoservicio que permite al propio jugador actualizar sus datos personales (nombre, ciudad, avatar, contraseña) y características de juego (nivel de habilidad y mano hábil) sin necesidad de intervención de un administrador.
- **Detalle de Torneo (`/tournaments/detail/{id}`)**: Información del campeonato con la lista de jugadores inscritos y el panel para agregar partidos con su puntuación.

---

## 6. Instalación y Ejecución de la Aplicación

### Paso 1: Configurar Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows usa: venv\Scripts\activate
```

### Paso 2: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Configurar Entorno
Crea tu archivo `.env` a partir de la plantilla:
```bash
cp .env.example .env
```

### Paso 4: Aplicar Migraciones
El sistema utiliza Alembic para sincronizar los esquemas relacionales.
```bash
alembic upgrade head
```

### Paso 5: Arrancar el Servidor
Inicia la aplicación utilizando `uvicorn`. El servidor arrancará localmente en el **puerto 8000**:
```bash
python -m uvicorn app.main:app --reload
```
Accede al portal web abriendo [http://127.0.0.1:8000](http://127.0.0.1:8000) en tu navegador.

*Nota: No se requiere ningún paso de build (ej. Webpack o Vite) para el frontend, ya que se sirve de forma directa mediante archivos estáticos Vanilla CSS/JS (`/static/`) renderizados en el servidor por Jinja2.*

---

## 7. Guía de Escalabilidad y Futuro Desacoplamiento

El backend está diseñado bajo principios de Clean Architecture y separación estricta de capas:

1. **Migración a Frontend Separado (SPA)**:
   - Los servicios en `app/services/` encapsulan toda la lógica de negocio y base de datos.
   - Las rutas del módulo `/api/` en `app/routes/api/` ya se encuentran expuestas y configuradas. Para migrar a React/Vue/Angular, simplemente expanda las operaciones JSON REST correspondientes dentro de estas rutas y cambie la autenticación web a un token JWT/Bearer.
2. **Soporte para Otros Deportes**:
   - Para añadir deportes como "Padel" o "Squash", simplemente registre el deporte en la columna `sport` de `PlayerProfile` y `Tournament`. Toda la lógica de cálculo de estadísticas relacionales en `UserService` se mantendrá intacta y aislada.
