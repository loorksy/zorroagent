import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { BuildPage } from "../pages/BuildPage";
import "../i18n";

test("build exposes three creation paths", () => {
  render(
    <MemoryRouter>
      <BuildPage />
    </MemoryRouter>,
  );
  expect(screen.getByText(/From library/i)).toBeInTheDocument();
  expect(screen.getByText(/Convert to bot/i)).toBeInTheDocument();
  expect(screen.getByText(/Draw \/ describe idea/i)).toBeInTheDocument();
});
