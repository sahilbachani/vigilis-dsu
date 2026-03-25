import { cn } from "@/lib/utils";

type Status = "Flagged" | "Safe" | "Reviewed" | "Idle" | "Running" | "Completed";

export function StatusBadge({ status, className }: { status: string, className?: string }) {
  const getStyles = (s: string) => {
    switch (s.toLowerCase()) {
      case 'flagged':
      case 'busy':
        return "bg-destructive/10 text-destructive border-destructive/20";
      case 'safe':
      case 'completed':
      case 'online':
        return "bg-green-500/10 text-green-600 border-green-500/20 dark:text-green-400";
      case 'reviewed':
      case 'idle':
      case 'away':
        return "bg-amber-500/10 text-amber-600 border-amber-500/20 dark:text-amber-400";
      case 'running':
        return "bg-blue-500/10 text-blue-600 border-blue-500/20 dark:text-blue-400 animate-pulse";
      default:
        return "bg-muted text-muted-foreground border-border";
    }
  };

  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border",
      getStyles(status),
      className
    )}>
      {status}
    </span>
  );
}
