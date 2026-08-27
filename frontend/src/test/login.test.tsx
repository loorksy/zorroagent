import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { LoginPage } from "../pages/SettingsLogin";
import "../i18n";

test("login form has labels, operator email, and download link", () => {
  render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );
  expect(screen.getByText(/Email/i)).toBeInTheDocument();
  expect(screen.getByDisplayValue("loorksy@gmail.com")).toBeInTheDocument();
  expect(screen.getByText(/Download Android/i)).toBeInTheDocument();
  expect(screen.getByText(/Personal analysis/i)).toBeInTheDocument();
});
