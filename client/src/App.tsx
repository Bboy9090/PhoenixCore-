import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import GodViewDashboard from "./pages/GodViewDashboard";
import USBRecipeBuilder from "./pages/USBRecipeBuilder";
import DeploymentTracker from "./pages/DeploymentTracker";
import BootCampDriverManager from "./pages/BootCampDriverManager";
import MonitoringStatus from "./pages/MonitoringStatus";
import AdminDashboard from "./pages/AdminDashboard";

import NotificationCenter from "./pages/NotificationCenter";
import PhoenixRelayControls from "./pages/PhoenixRelayControls";
import ComponentsShowcase from "./pages/ComponentShowcase";

import DashboardLayout from "./components/DashboardLayout";

import Imaging from "./pages/Imaging";

function Router() {
  return (
    <Switch>
      <Route path={"/"} component={Home} />
      <Route path={"/god-view"} component={GodViewDashboard} />
      <Route path={"/recipe-builder"} component={USBRecipeBuilder} />
      <Route path={"/imaging"} component={Imaging} />
      <Route path={"/deployments"} component={DeploymentTracker} />
      <Route path={"/bootcamp"} component={BootCampDriverManager} />
      <Route path={"/relay"} component={PhoenixRelayControls} />
      <Route path={"/notifications"} component={NotificationCenter} />
      <Route path={"/monitoring"} component={MonitoringStatus} />
      <Route path={"/admin"} component={AdminDashboard} />
      <Route path={"/dev/showcase"} component={ComponentsShowcase} />
      <Route path={"/404"} component={NotFound} />
      {/* Final fallback route */}
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster />
          <DashboardLayout>
            <Router />
          </DashboardLayout>
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
