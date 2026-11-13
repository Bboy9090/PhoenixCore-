#!/usr/bin/env bash
# build_linux_package.sh — AppDir and Linux bundle packager for BobFWTools Studio
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist_linux"
APPDIR="${DIST_DIR}/BobFWTools.AppDir"

echo "==> Building Linux Package Structure for BobFWTools Studio..."
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/metainfo"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/512x512/apps"
mkdir -p "${APPDIR}/etc/udev/rules.d"
mkdir -p "${APPDIR}/usr/lib/bobfwtools"

# Copy python source files from windows_deploy/BobFWTools (clean self-contained source)
if [ -d "${ROOT_DIR}/windows_deploy/BobFWTools" ]; then
    cp -R "${ROOT_DIR}/windows_deploy/BobFWTools/"* "${APPDIR}/usr/lib/bobfwtools/"
fi

cp "${SCRIPT_DIR}/com.bobbyblanco.bobfwtools.desktop" "${APPDIR}/usr/share/applications/"
cp "${SCRIPT_DIR}/com.bobbyblanco.bobfwtools.desktop" "${APPDIR}/"
if [ -f "${SCRIPT_DIR}/com.bobbyblanco.bobfwtools.metainfo.xml" ]; then
    cp "${SCRIPT_DIR}/com.bobbyblanco.bobfwtools.metainfo.xml" "${APPDIR}/usr/share/metainfo/"
fi
if [ -f "${SCRIPT_DIR}/99-bobfwtools-devices.rules" ]; then
    cp "${SCRIPT_DIR}/99-bobfwtools-devices.rules" "${APPDIR}/etc/udev/rules.d/"
fi
cp "${ROOT_DIR}/store_packaging/bob_fw_tools_icon.svg" "${APPDIR}/usr/share/icons/hicolor/scalable/apps/bob-fw-tools.svg"
cp "${ROOT_DIR}/store_packaging/bob_fw_tools_icon.svg" "${APPDIR}/bob-fw-tools.svg"
if [ -f "${ROOT_DIR}/bobbys-workshop/Resources/AppIcon_1024.png" ]; then
    sips -z 512 512 "${ROOT_DIR}/bobbys-workshop/Resources/AppIcon_1024.png" --out "${APPDIR}/usr/share/icons/hicolor/512x512/apps/bob-fw-tools.png" >/dev/null 2>&1 || cp "${ROOT_DIR}/bobbys-workshop/Resources/AppIcon_1024.png" "${APPDIR}/usr/share/icons/hicolor/512x512/apps/bob-fw-tools.png"
    cp "${APPDIR}/usr/share/icons/hicolor/512x512/apps/bob-fw-tools.png" "${APPDIR}/.DirIcon"
else
    cp "${ROOT_DIR}/store_packaging/bob_fw_tools_icon.svg" "${APPDIR}/.DirIcon"
fi

# AppRun launcher script
cat << 'EOF' > "${APPDIR}/AppRun"
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/bobfwtools:${PYTHONPATH:-}"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required to run BobFWTools Studio." >&2
    exit 1
fi

exec python3 "${HERE}/usr/lib/bobfwtools/main.py" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

cat << 'EOF' > "${APPDIR}/usr/bin/bobfwtools"
#!/usr/bin/env bash
exec /usr/bin/env python3 /usr/lib/bobfwtools/main.py "$@"
EOF
chmod +x "${APPDIR}/usr/bin/bobfwtools"

cd "${DIST_DIR}"
tar -czf "BobFWTools-Linux-Universal.tar.gz" -C "${DIST_DIR}" "BobFWTools.AppDir"
echo "[✓] Linux Universal AppDir and BobFWTools-Linux-Universal.tar.gz created in ${DIST_DIR}"
