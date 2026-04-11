import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Zap, Globe, MessageSquare, Facebook } from "lucide-react";

interface ScrapeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ScraperOption {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  status: "ready" | "running" | "coming-soon";
  command: string;
}

const scrapers: ScraperOption[] = [
  {
    id: "x",
    name: "X/Twitter",
    description: "Scrape posts from X/Twitter timeline",
    icon: MessageSquare,
    status: "ready",
    command: "python run_scraper.py x",
  },
  {
    id: "tiktok",
    name: "TikTok",
    description: "Scrape videos from TikTok explore page",
    icon: Zap,
    status: "ready",
    command: "python run_scraper.py tiktok",
  },
  {
    id: "facebook",
    name: "Facebook",
    description: "Scrape posts from Facebook feed",
    icon: Facebook,
    status: "ready",
    command: "python run_scraper.py facebook",
  },
  {
    id: "web",
    name: "Websites/Blogs",
    description: "Scrape news from Pakistani news sites",
    icon: Globe,
    status: "ready",
    command: "python run_scraper.py web",
  },
];

function getStatusColor(status: string): string {
  switch (status) {
    case "ready":
      return "bg-green-100 dark:bg-green-950 text-green-800 dark:text-green-200";
    case "running":
      return "bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-200";
    case "coming-soon":
      return "bg-gray-100 dark:bg-gray-950 text-gray-800 dark:text-gray-200";
    default:
      return "bg-gray-100 dark:bg-gray-950";
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case "ready":
      return <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />;
    case "coming-soon":
      return <AlertCircle className="h-4 w-4 text-gray-600 dark:text-gray-400" />;
    default:
      return null;
  }
}

export function ScrapeModal({ open, onOpenChange }: ScrapeModalProps) {
  const [selectedScraper, setSelectedScraper] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunScraper = async (scraperId: string) => {
    setSelectedScraper(scraperId);
    setIsRunning(true);
    
    try {
      // Call the backend API to start scraping
      const response = await fetch("/api/scraper/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ scraper: scraperId }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Scraper started:", data);
        
        // Close modal after a short delay
        setTimeout(() => {
          setIsRunning(false);
          onOpenChange(false);
          setSelectedScraper(null);
        }, 1500);
      } else {
        console.error("Failed to start scraper");
        setIsRunning(false);
      }
    } catch (error) {
      console.error("Error starting scraper:", error);
      setIsRunning(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Start Web Scraping</DialogTitle>
          <DialogDescription>
            Select a platform to scrape content from. Scraped data will be automatically analyzed and stored in the database.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 max-h-96 overflow-y-auto pr-4">
          {scrapers.map((scraper) => {
            const Icon = scraper.icon;
            const isDisabled = scraper.status !== "ready" || isRunning;
            const isSelected = selectedScraper === scraper.id && isRunning;

            return (
              <Card
                key={scraper.id}
                className={`cursor-pointer transition-all ${
                  isDisabled ? "opacity-60 cursor-not-allowed" : "hover:border-primary/50 hover:shadow-md"
                } ${isSelected ? "border-primary bg-primary/5" : ""}`}
                onClick={() => !isDisabled && handleRunScraper(scraper.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="p-2.5 bg-secondary rounded-lg mt-0.5">
                        <Icon className="h-5 w-5 text-secondary-foreground" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-foreground flex items-center gap-2">
                          {scraper.name}
                          <Badge variant="outline" className={getStatusColor(scraper.status)}>
                            <span className="flex items-center gap-1.5">
                              {getStatusIcon(scraper.status)}
                              {scraper.status === "ready" && "Ready"}
                              {scraper.status === "running" && "Running"}
                              {scraper.status === "coming-soon" && "Coming Soon"}
                            </span>
                          </Badge>
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">{scraper.description}</p>
                        <p className="text-xs text-muted-foreground mt-2 font-mono bg-muted/50 px-2 py-1 rounded w-fit">
                          {scraper.command}
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRunScraper(scraper.id);
                      }}
                      disabled={isDisabled}
                      variant={isSelected ? "default" : "outline"}
                      size="sm"
                      className="flex-shrink-0"
                    >
                      {isSelected ? "Starting..." : "Run"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <div className="flex gap-2">
            <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-blue-800 dark:text-blue-200">
              <strong>Tip:</strong> Scrapers run in the background. You can close this dialog and monitor progress in the Activity section.
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button
            variant="outline"
            onClick={() => {
              onOpenChange(false);
              setSelectedScraper(null);
              setIsRunning(false);
            }}
            disabled={isRunning}
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
