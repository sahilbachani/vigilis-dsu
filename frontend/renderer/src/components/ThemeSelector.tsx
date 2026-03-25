import { useTheme } from "@/components/ThemeContext";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Palette } from "lucide-react";

const colorThemes = [
  { id: "default", name: "Default", color: "bg-blue-600" },
  { id: "blue", name: "Blue", color: "bg-cyan-500" },
  { id: "green", name: "Green", color: "bg-emerald-600" },
];

export function ThemeSelector() {
  const { colorScheme, setColorScheme } = useTheme();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-8 w-8 text-sidebar-foreground/70 hover:text-sidebar-foreground"
          title="Color Theme"
          data-testid="button-theme-selector"
        >
          <Palette className="h-4 w-4" />
          <span className="sr-only">Color Theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-48">
        <DropdownMenuLabel className="text-xs font-semibold">Color Theme</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {colorThemes.map((theme) => (
          <DropdownMenuItem
            key={theme.id}
            onClick={() => setColorScheme(theme.id as any)}
            className="flex items-center justify-between cursor-pointer"
            data-testid={`menu-theme-${theme.id}`}
          >
            <div className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${theme.color}`} />
              <span>{theme.name}</span>
            </div>
            {colorScheme === theme.id && (
              <span className="text-primary font-bold">✓</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
