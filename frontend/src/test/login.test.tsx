import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { LoginPage } from "../pages/SettingsLogin";
import "../i18n";

test("login form has labels and disclaimer", () => {
  render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );
  expect(screen.getByText(/Email/i)).toBeInTheDocument();
  expect(screen.getByText(/Personal analysis/i)).toBeInTheDocument();
});
