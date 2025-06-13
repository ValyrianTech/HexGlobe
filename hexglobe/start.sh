#!/bin/bash
set -e

# Check if we should start in shell mode
if [ "$1" = "shell" ]; then
    echo "Starting shell..."
    exec /bin/bash
else
    # Default: start supervisord to run backend and frontend services
    echo "Starting HexGlobe services..."
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
fi
