
smoketest_medcat_service() {
    local localhost_name="$1"
    local docker_compose_file="$2"

    if [ -z "$localhost_name" ] || [ -z "$docker_compose_file" ]; then
        echo "Invalid arguments. Usage: health_check <localhost_name> <docker_compose_file>" >&2
        return 1
    fi

    API="http://${localhost_name}:5555/api/info"

    MAX_RETRIES=12
    RETRY_DELAY=5
    COUNT=0

    while [ $COUNT -lt $MAX_RETRIES ]; do
    echo "Checking service health on $API (Attempt $((COUNT+1))/$MAX_RETRIES)"
    sleep $RETRY_DELAY
    IS_READY=$(curl -s -o /dev/null -w "%{http_code}" $API)

    if [ "$IS_READY" = "200" ]; then
        echo "Service is ready!"
        break
    else
        echo "Attempt $((COUNT+1))/$MAX_RETRIES: Not ready (HTTP $IS_READY)."
        docker compose -f ${DOCKER_COMPOSE_FILE} logs
        COUNT=$((COUNT+1))
    fi
    done

    if [ $COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Service did not become ready after $MAX_RETRIES attempts."
    exit 1
    fi

    cat <<EOF
-----------------------------------------------------------------
MedCATService running on http://${LOCALHOST_NAME}:5555/
-----------------------------------------------------------------
EOF

}