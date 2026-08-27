import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useDesk } from "../store";

export function BuildPage() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const open = useDesk((s) => s.openModal);
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">{t("nav.build")}</h1>
      <div className="grid md:grid-cols-3 gap-4">
        <button className="rounded-xl border border-line bg-card p-6 text-start touch-target" onClick={() => nav("/strategies/new")}>
          <h2 className="font-medium">{t("buttons.library")}</h2>
          <p className="text-sm text-muted-fg mt-2">{t("build.libraryHint")}</p>
        </button>
        <button className="rounded-xl border border-line bg-card p-6 text-start" onClick={() => open("convert")}>
          <h2 className="font-medium">{t("buttons.convertBot")}</h2>
          <p className="text-sm text-muted-fg mt-2">{t("build.convertHint")}</p>
        </button>
        <button className="rounded-xl border border-line bg-card p-6 text-start" onClick={() => open("draw")}>
          <h2 className="font-medium">{t("buttons.drawIdea")}</h2>
          <p className="text-sm text-muted-fg mt-2">{t("build.drawHint")}</p>
        </button>
      </div>
      <p className="text-sm text-muted-fg">{t("build.demoNote")}</p>
    </div>
  );
}
