import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "./components/Shell";
import { AskPage } from "./pages/AskPage";
import { TodayPage } from "./pages/TodayPage";
import { BuildPage } from "./pages/BuildPage";
import { ChartPage } from "./pages/ChartPage";
import { RecommendationDetailPage, RecommendationsPage } from "./pages/RecommendationsPage";
import { ExposurePage, WatchlistPage } from "./pages/WatchlistExposure";
import { AccountPage } from "./pages/AccountPage";
import { StrategiesPage, StrategyNewPage, StrategyOptimizePage, StrategyVersionsPage } from "./pages/StrategiesPages";
import { BotDetailPage, BotLivePage, BotsPage, DemoPage, HistoryPage, MemoryPage, ReviewPage } from "./pages/BotsPages";
import { LoginPage, SettingsPage } from "./pages/SettingsLogin";
import { DownloadPage } from "./pages/DownloadPage";
import { token } from "./lib/api";

function Guard({ children }: { children: React.ReactNode }) {
  if (!token()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/download" element={<DownloadPage />} />
        <Route
          element={
            <Guard>
              <Shell />
            </Guard>
          }
        >
          <Route path="/" element={<AskPage />} />
          <Route path="/today" element={<TodayPage />} />
          <Route path="/build" element={<BuildPage />} />
          <Route path="/chart/:symbol?" element={<ChartPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/recommendations/:id" element={<RecommendationDetailPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
          <Route path="/exposure" element={<ExposurePage />} />
          <Route path="/account" element={<AccountPage />} />
          <Route path="/strategies" element={<StrategiesPage />} />
          <Route path="/strategies/new" element={<StrategyNewPage />} />
          <Route path="/strategies/:id/optimize" element={<StrategyOptimizePage />} />
          <Route path="/strategies/:id/versions" element={<StrategyVersionsPage />} />
          <Route path="/demo" element={<DemoPage />} />
          <Route path="/bots" element={<BotsPage />} />
          <Route path="/bots/:id" element={<BotDetailPage />} />
          <Route path="/bots/:id/live" element={<BotLivePage />} />
          <Route path="/memory" element={<MemoryPage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
