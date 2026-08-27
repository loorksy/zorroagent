#!/usr/bin/env bash
# Build an unsigned debug APK that points at the live Zorro site.
# Intended to run on the isolated VPS tree (/opt/zorroagent) or a dedicated
# docker android-build — never writes SDK into other app directories.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PUBLIC_DIR="${ZORRO_PUBLIC_DIR:-$ROOT/public}"
SERVER_URL="${CAPACITOR_SERVER_URL:-https://zorro.lork.cloud}"
IMAGE_NAME="${ZORRO_ANDROID_IMAGE:-zorroagent-android-build:local}"

cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm ci
fi
npm run build
export CAPACITOR_SERVER_URL="$SERVER_URL"
npx cap sync android

cd "$ROOT"
if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to assemble the APK (Android SDK is not installed on the host)." >&2
  echo "Install docker, or run this script on the VPS under /opt/zorroagent." >&2
  exit 2
fi

docker build -t "$IMAGE_NAME" -f "$ROOT/deploy/android-build.Dockerfile" "$ROOT/deploy"
docker run --rm \
  --name zorroagent-android-build \
  -v "$ROOT/frontend:/src" \
  -w /src/android \
  -e ANDROID_HOME=/opt/android-sdk \
  -e ANDROID_SDK_ROOT=/opt/android-sdk \
  "$IMAGE_NAME" \
  ./gradlew assembleDebug --no-daemon

APK_SRC="$ROOT/frontend/android/app/build/outputs/apk/debug/app-debug.apk"
if [[ ! -f "$APK_SRC" ]]; then
  echo "Gradle did not produce $APK_SRC" >&2
  exit 3
fi
mkdir -p "$PUBLIC_DIR"
cp -f "$APK_SRC" "$PUBLIC_DIR/zorro.apk"
chmod 644 "$PUBLIC_DIR/zorro.apk"
echo "APK ready: $PUBLIC_DIR/zorro.apk"
ls -lh "$PUBLIC_DIR/zorro.apk"
