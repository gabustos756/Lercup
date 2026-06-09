#!/bin/bash

# Exit on error
set -e

DB_NAME="lercup"
DB_USER="postgres"
DB_PASS="postgres"
DB_PORT="5432"

echo "================================================================="
echo "🎾 Lercup - Configuración de Base de Datos Local (PostgreSQL) 🎾"
echo "================================================================="
echo ""

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo "🐳 Docker detectado. Iniciando contenedor de PostgreSQL..."
    
    # Check if a container with the same name already exists
    if [ "$(docker ps -a -q -f name=lercup-postgres)" ]; then
        echo "🔄 Contenedor lercup-postgres existente detectado."
        if [ "$(docker ps -q -f name=lercup-postgres)" ]; then
            echo "✅ El contenedor ya se encuentra corriendo."
        else
            echo "▶️ Iniciando contenedor existente..."
            docker start lercup-postgres
        fi
    else
        echo "🚀 Creando y corriendo contenedor 'lercup-postgres'..."
        docker run --name lercup-postgres \
          -e POSTGRES_DB=$DB_NAME \
          -e POSTGRES_USER=$DB_USER \
          -e POSTGRES_PASSWORD=$DB_PASS \
          -p $DB_PORT:5432 \
          -d postgres:15-alpine
        echo "✅ Contenedor iniciado en el puerto $DB_PORT."
    fi
    
    echo ""
    echo "Conexión para tu archivo .env:"
    echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:$DB_PORT/$DB_NAME"
    echo ""
    echo "¡Listo! Puedes ejecutar tus migraciones ejecutando:"
    echo "  alembic upgrade head"
    echo ""
else
    echo "⚠️ Docker no detectado en el sistema."
    echo "Instrucciones para configuración manual de PostgreSQL:"
    echo ""
    echo "1. Asegúrate de tener PostgreSQL instalado y corriendo (ej. Postgres.app o 'brew services start postgresql')."
    echo "2. Conéctate a la consola de psql e inicializa la base de datos:"
    echo "   CREATE DATABASE $DB_NAME;"
    echo "3. Configura las credenciales correctas en tu archivo '.env':"
    echo "   DATABASE_URL=postgresql://<tu_usuario>:<tu_contraseña>@localhost:5432/$DB_NAME"
    echo "4. Luego ejecuta la migración inicial de Alembic:"
    echo "   alembic upgrade head"
    echo ""
fi
