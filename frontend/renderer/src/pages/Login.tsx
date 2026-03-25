import { useState } from "react";
import { useLogin } from "@/hooks/use-auth";
import { ShieldAlert, ArrowRight, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Card } from "@/components/ui/card";
import { useTheme } from "@/components/ThemeContext";
import logoTextDark from "@/assets/Logo_text_dark.png";
import logoTextLight from "@/assets/Logo_text_dark.png";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const loginMutation = useLogin();
  const { toast } = useToast();
  const { theme } = useTheme();
  const logoSrc = theme === "dark" ? logoTextDark : logoTextLight;

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();

    loginMutation.mutate(
      { username, password },
      {
        onError: (error: any) => {
          let description = "Login failed. Please try again.";

          // Extract backend validation errors safely
          if (error.detail) {
            if (typeof error.detail === "string") {
              description = error.detail;
            } else if (Array.isArray(error.detail)) {
              description = error.detail.map((d: any) => d.msg).join(", ");
            }
          } else if (error.msg) {
            description = error.msg;
          }

          toast({
            variant: "destructive",
            title: "Login Failed",
            description,
          });
        },
      }
    );
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-0 left-0 w-96 h-96 bg-primary rounded-full mix-blend-multiply filter blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-accent rounded-full mix-blend-multiply filter blur-3xl animate-pulse delay-2000"></div>
      </div>

      <Card className="w-full max-w-sm p-8 shadow-lg border border-border/40 relative backdrop-blur-sm bg-card rounded-lg animate-in">
        <div className="flex flex-col items-center space-y-3">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-transparent rounded-md blur-lg"></div>
            <img
              src={logoSrc}
              alt="Vigilis"
              className="h-11 w-auto relative"
              draggable={false}
            />
          </div>
          <h1 className="text-2xl font-display font-bold text-center text-foreground">
            Welcome Back
          </h1>
          <p className="text-xs text-muted-foreground text-center">
            Secure content monitoring system
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4 mt-6">
          <div className="space-y-2">
            <Label htmlFor="username" className="text-sm font-medium text-foreground">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="text-sm bg-background border-border/30 focus-visible:ring-primary/30 transition-all py-2 text-foreground placeholder:text-muted-foreground"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-medium text-foreground">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="text-sm bg-background border-border/30 focus-visible:ring-primary/30 transition-all py-2 text-foreground placeholder:text-muted-foreground"
              required
            />
          </div>

          <Button
            type="submit"
            disabled={loginMutation.isPending}
            className="w-full bg-primary hover:bg-primary/90 text-white font-semibold shadow-md hover:shadow-lg transition-all py-2 h-auto mt-2"
          >
            {loginMutation.isPending ? (
              <Loader2 className="animate-spin h-4 w-4" />
            ) : (
              <span className="flex items-center justify-center gap-2">
                Sign In <ArrowRight className="h-4 w-4" />
              </span>
            )}
          </Button>
        </form>

        <p className="text-xs text-muted-foreground text-center mt-8 pt-6 border-t border-border/30">
          Powered by Vigilis Content Monitoring
        </p>
      </Card>
    </div>
  );
}
