import { Switch, Route, Redirect } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeContext";
import NotFound from "@/pages/not-found";

// Components
import Layout from "@/components/Layout";

// Pages
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import FlaggedPosts from "@/pages/FlaggedPosts";
import Settings from "@/pages/Settings";
import Sources from "@/pages/Sources";
import { useUser } from "@/hooks/use-auth";

// Protected Route Wrapper
function ProtectedRoute({ component: Component }: { component: React.ComponentType }) {
  const user = useUser();

  if (!user) {
    return <Redirect to="/" />;
  }

  return (
    <Layout>
      <Component />
    </Layout>
  );
}

function Router() {
  const user = useUser();

  return (
    <Switch>
      {/* Public Route */}
      <Route path="/">
        {user ? <Redirect to="/dashboard" /> : <Login />}
      </Route>

      {/* Protected Routes */}
      <Route path="/dashboard">
        <ProtectedRoute component={Dashboard} />
      </Route>
      
      <Route path="/dashboard/posts">
        <ProtectedRoute component={FlaggedPosts} />
      </Route>
      
      <Route path="/dashboard/settings">
        <ProtectedRoute component={Settings} />
      </Route>
      
      <Route path="/dashboard/sources">
        <ProtectedRoute component={Sources} />
      </Route>

      {/* Fallback */}
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="system" storageKey="vigilis-theme">
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
