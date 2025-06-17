#!/bin/bash

JENKINS_HOME="/var/lib/docker/volumes/jenkins_home/_data"

echo "🚀 Limpiando workspace (código y artefactos temporales)..."
sudo rm -rf "$JENKINS_HOME/workspace/"*

echo "🧹 Limpiando builds antiguos (resultados de builds anteriores)..."
sudo find "$JENKINS_HOME/jobs/" -type d -name builds -exec rm -rf {}/* \;

echo "🗑️ Limpiando logs de Jenkins..."
sudo rm -rf "$JENKINS_HOME/logs/"*

echo "🧽 Limpiando cachés temporales (si existen)..."
sudo rm -rf "$JENKINS_HOME/caches/"*

echo "✅ Limpieza completada. Espacio liberado."

# Opcional: muestra espacio libre después de limpieza
df -h "$JENKINS_HOME"
