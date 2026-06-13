#!/bin/bash
set -e

setup_env() {
    if [ ! -f .env ]; then
        if [ -f env.example ]; then
            cp env.example .env
        else
            echo "Error: env.example not found."
            exit 1
        fi
    fi

    if [ -t 0 ]; then
        if ! grep -q "GEMINI_API_KEY=" .env || grep -q "GEMINI_API_KEY=api_key" .env || grep -q "GEMINI_API_KEY=$" .env; then
            read -p "Enter Gemini API Key: " api_key
            if grep -q "GEMINI_API_KEY=" .env; then
                sed -i "s/^GEMINI_API_KEY=.*/GEMINI_API_KEY=$api_key/" .env
            else
                echo "GEMINI_API_KEY=$api_key" >> .env
            fi
        fi

        if ! grep -q "POSTGRES_USER=" .env || grep -q "POSTGRES_USER=$" .env; then
            read -p "Enter Postgres User (default: postgres): " pg_user
            pg_user=${pg_user:-postgres}
            if grep -q "POSTGRES_USER=" .env; then
                sed -i "s/^POSTGRES_USER=.*/POSTGRES_USER=$pg_user/" .env
            else
                echo "POSTGRES_USER=$pg_user" >> .env
            fi
        fi

        if ! grep -q "POSTGRES_PASSWORD=" .env || grep -q "POSTGRES_PASSWORD=$" .env; then
            read -p "Enter Postgres Password (default: postgres): " pg_pass
            pg_pass=${pg_pass:-postgres}
            if grep -q "POSTGRES_PASSWORD=" .env; then
                sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$pg_pass/" .env
            else
                echo "POSTGRES_PASSWORD=$pg_pass" >> .env
            fi
        fi
        
        echo "Environment setup complete."
    else
        echo "Error: Cannot prompt in non-interactive shell."
        exit 1
    fi
}

start_app() {
    if [ ! -f .env ]; then
        echo "Error: .env file missing. Run ./start.sh --setup first."
        exit 1
    fi
    docker compose up -d --build
    echo "App started. Logs: docker compose logs -f"
}

stop_app() {
    docker compose down
    echo "App stopped."
}

show_help() {
    echo "Usage: ./start.sh [FLAG]"
    echo "Flags:"
    echo "  --setup   Interactively setup the .env file"
    echo "  --start   Start the application"
    echo "  --stop    Stop the application"
}

if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

case "$1" in
    --setup)
        setup_env
        ;;
    --start)
        start_app
        ;;
    --stop)
        stop_app
        ;;
    *)
        show_help
        exit 1
        ;;
esac
