import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LangSwitch } from "./SettingsLogin";

const APK_HREF = "/zorro.apk";

export function DownloadPage() {
  const { t } = useTranslation();
  return (
    <div className="max-w-lg mx-auto mt-16 space-y-4 px-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">{t("download.title")}</h1>
        <LangSwitch />
      </div>
      <p className="text-sm text-muted-fg">{t("download.lead")}</p>
      <a
        className="inline-flex min-h-11 items-center justify-center rounded liquid-metal px-4 py-2"
        href={APK_HREF}
        download="zorro.apk"
      >
        {t("download.button")}
      </a>
      <h2 className="text-sm font-medium pt-2">{t("download.stepsTitle")}</h2>
      <ol className="list-decimal ps-5 space-y-2 text-sm">
        <li>{t("download.step1")}</li>
        <li>{t("download.step2")}</li>
        <li>{t("download.step3")}</li>
        <li>{t("download.step4")}</li>
      </ol>
      <p className="text-xs text-muted-fg">{t("download.note")}</p>
      <p className="text-sm">
        <Link className="underline" to="/login">
          {t("nav.login")}
        </Link>
      </p>
    </div>
  );
}
