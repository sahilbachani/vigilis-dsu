import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Globe, Loader2 } from "lucide-react";
import axios from "axios";
import { useToast } from "@/hooks/use-toast";

interface ScrapeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const PLATFORMS = [
  {
    id: "twitter",
    name: "Twitter (X)",
    description: "Scrape posts from X/Twitter feed",
    icon: (
      <span className="inline-flex items-center justify-center h-10 w-10 bg-black dark:bg-white text-white dark:text-black rounded-xl text-xl font-bold">
        𝕏
      </span>
    ),
    color: "border-neutral-300 dark:border-neutral-600",
    activeColor: "border-black dark:border-white bg-neutral-50 dark:bg-neutral-900",
  },
  {
    id: "facebook",
    name: "Facebook",
    description: "Scrape posts from Facebook feed",
    icon: (
      <span className="inline-flex items-center justify-center h-10 w-10 bg-blue-600 text-white rounded-xl text-xl font-bold">
        f
      </span>
    ),
    color: "border-blue-200 dark:border-blue-800",
    activeColor: "border-blue-500 dark:border-blue-400 bg-blue-50 dark:bg-blue-950",
  },
  {
    id: "tiktok",
    name: "TikTok",
    description: "Scrape videos from TikTok explore feed",
    icon: (
      <span className="inline-flex items-center justify-center h-10 w-10 bg-black dark:bg-white text-white dark:text-black rounded-xl text-xl font-bold">
        ♪
      </span>
    ),
    color: "border-fuchsia-200 dark:border-fuchsia-800",
    activeColor: "border-fuchsia-500 dark:border-fuchsia-400 bg-fuchsia-50 dark:bg-fuchsia-950",
  },
  {
    id: "website-dawn",
    name: "Dawn News",
    description: "Scrape articles from Dawn News",
    icon: (
      <span className="inline-flex items-center justify-center h-10 w-10 bg-emerald-600 text-white rounded-xl text-lg">
        <Globe className="h-5 w-5" />
      </span>
    ),
    color: "border-emerald-200 dark:border-emerald-800",
    activeColor: "border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950",
  },
  {
    id: "website-toi",
    name: "Times of India",
    description: "Scrape articles from Times of India",
    icon: (
      <span className="inline-flex items-center justify-center h-10 w-10 bg-emerald-600 text-white rounded-xl text-lg">
        <Globe className="h-5 w-5" />
      </span>
    ),
    color: "border-emerald-200 dark:border-emerald-800",
    activeColor: "border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950",
  },
  {
    id: "website-jihadintel",
    name: "Jihad Intel",
    description: "Scrape articles from Jihad Intel",
    icon: (
      <span className="inline-flex items-center justify-center h-10 w-10 bg-emerald-600 text-white rounded-xl text-lg">
        <Globe className="h-5 w-5" />
      </span>
    ),
    color: "border-emerald-200 dark:border-emerald-800",
    activeColor: "border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950",
  },
  {
    id: "website-khorasandiary",
    name: "The Khorasan Diary",
    description: "Scrape articles from The Khorasan Diary",
    icon: (
      <span className="inline-flex items-center justify-center h-10 w-10 bg-emerald-600 text-white rounded-xl text-lg">
        <Globe className="h-5 w-5" />
      </span>
    ),
    color: "border-emerald-200 dark:border-emerald-800",
    activeColor: "border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950",
  },
];

export function ScrapeModal({ open, onOpenChange }: ScrapeModalProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleScrape = async () => {
    if (!selectedPlatform) return;

    setIsLoading(true);
    try {
      const response = await axios.post("http://localhost:8000/api/scraper/run", {
        platform: selectedPlatform,
      });

      toast({
        title: "Scraping Started",
        description: response.data.message || `${selectedPlatform} scraper has been launched.`,
      });

      // Close modal after success
      onOpenChange(false);
      setSelectedPlatform(null);
    } catch (error: any) {
      const message = error.response?.data?.detail || "Failed to start scraper. Is the backend running?";
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => {
      if (!isLoading) {
        onOpenChange(v);
        if (!v) setSelectedPlatform(null);
      }
    }}>
      <DialogContent className="sm:max-w-[600px] flex flex-col max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="text-xl font-display font-bold">Scrape Data</DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Select a platform to start scraping content from.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 py-4 overflow-y-auto pr-2 flex-1">
          {PLATFORMS.map((platform) => (
            <button
              key={platform.id}
              onClick={() => setSelectedPlatform(platform.id)}
              disabled={isLoading}
              className={cn(
                "flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-200 text-left",
                "hover:shadow-md hover:scale-[1.01] active:scale-[0.99]",
                selectedPlatform === platform.id
                  ? platform.activeColor + " shadow-md ring-1 ring-primary/20"
                  : platform.color + " bg-card hover:bg-accent/30"
              )}
              data-testid={`platform-${platform.id}`}
            >
              {platform.icon}
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm text-foreground">{platform.name}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{platform.description}</p>
              </div>
              <div
                className={cn(
                  "h-5 w-5 rounded-full border-2 flex items-center justify-center transition-colors flex-shrink-0",
                  selectedPlatform === platform.id
                    ? "border-primary bg-primary"
                    : "border-muted-foreground/30"
                )}
              >
                {selectedPlatform === platform.id && (
                  <div className="h-2 w-2 rounded-full bg-white" />
                )}
              </div>
            </button>
          ))}
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Button
            variant="outline"
            onClick={() => {
              onOpenChange(false);
              setSelectedPlatform(null);
            }}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleScrape}
            disabled={!selectedPlatform || isLoading}
            className="min-w-[140px] font-semibold shadow-md"
            data-testid="button-start-scraping"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Starting...
              </>
            ) : (
              "Start Scraping"
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
