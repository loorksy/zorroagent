Capacitor Android packaging for Zorro.

`npx cap sync android` after `npm run build`.
Production APK: `CAPACITOR_SERVER_URL=https://zorro.lork.cloud npx cap sync android`
then `assembleDebug` via `scripts/build-android-apk.sh` (docker image; SDK not installed into other apps).

A signed Play Store APK is NOT produced (no keystore).
Unsigned debug APK is served at https://zorro.lork.cloud/zorro.apk — enable Install unknown apps.
