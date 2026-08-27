# Isolated Android SDK + Gradle image for Zorro APK builds.
# Do not reuse this image for other host apps. SDK lives inside the image, not /opt/aichart etc.
FROM eclipse-temurin:17-jdk-jammy

ENV ANDROID_HOME=/opt/android-sdk \
    ANDROID_SDK_ROOT=/opt/android-sdk \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget unzip git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# commandlinetools-linux; pin a known zip.
RUN mkdir -p ${ANDROID_HOME}/cmdline-tools \
    && wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/cmd.zip \
    && unzip -q /tmp/cmd.zip -d /tmp \
    && mv /tmp/cmdline-tools ${ANDROID_HOME}/cmdline-tools/latest \
    && rm /tmp/cmd.zip

ENV PATH=${PATH}:${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools:${ANDROID_HOME}/build-tools/34.0.0

RUN yes | sdkmanager --licenses >/dev/null \
    && sdkmanager --install "platforms;android-34" "build-tools;34.0.0" "platform-tools"

WORKDIR /src
