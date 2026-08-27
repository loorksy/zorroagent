import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { DownloadPage } from "../pages/DownloadPage";
import "../i18n";

test("download page links to apk", () => {
  render(
    <MemoryRouter>
      <DownloadPage />
    </MemoryRouter>,
  );
  const link = screen.getByRole("link", { name: /zorro\.apk/i });
  expect(link).toHaveAttribute("href", "/zorro.apk");
});
