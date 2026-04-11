import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  Play,
  Download,
} from "lucide-react";
import axios from "axios";
import { useToast } from "@/hooks/use-toast";

interface ScraperProgressModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sourceId: number;
  sourceName: string;
  onScrapingComplete?: (results: any) => void;
}

interface ScrapingResult {
  success: boolean;
  posts_found: number;
  posts_saved: number;
  posts_duplicates: number;
  flagged_count: number;
  message: string;
}

interface TaskStatus {
  task_id: string;
  status: string;
  progress: number;
  message: string;
  posts_found: number;
  posts_saved: number;
  error?: string;
}

type ScrapingStatus = "idle" | "scraping" | "processing" | "complete" | "error";

export function ScraperProgressModal({
  open,
  onOpenChange,
  sourceId,
  sourceName,
  onScrapingComplete,
}: ScraperProgressModalProps) {
  const { toast } = useToast();
  const [status, setStatus] = useState<ScrapingStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<ScrapingResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskMessage, setTaskMessage] = useState<string>("Initializing...");
  const [postsFound, setPostsFound] = useState(0);
  const [postsSaved, setPostsSaved] = useState(0);

  // Poll task status
  useEffect(() => {
    if (!taskId || status !== "scraping") return;

    const checkTaskStatus = async () => {
      try {
        const response = await axios.get(
          `http://localhost:8000/api/tasks/${taskId}/status`
        );

        const task: TaskStatus = response.data;
        setProgress(task.progress);
        setTaskMessage(task.message);
        setPostsFound(task.posts_found);
        setPostsSaved(task.posts_saved);

        if (task.status === "completed") {
          setProgress(100);
          setStatus("processing");
          
          await new Promise((resolve) => setTimeout(resolve, 500));
          
          setResult({
            success: true,
            posts_found: task.posts_found,
            posts_saved: task.posts_saved,
            posts_duplicates: 0,
            flagged_count: 0,
            message: task.message
          });
          setStatus("complete");
          onScrapingComplete?.({
            posts_found: task.posts_found,
            posts_saved: task.posts_saved
          });

          toast({
            title: "✅ Scraping Complete",
            description: `Found ${task.posts_found} posts, saved ${task.posts_saved} new posts.`,
          });
        } else if (task.status === "failed") {
          setStatus("error");
          setErrorMessage(task.error || "Scraping failed");
          toast({
            title: "❌ Scraping Failed",
            description: task.error || "An error occurred during scraping.",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error("Failed to check task status:", error);
      }
    };

    const interval = setInterval(checkTaskStatus, 1000);
    return () => clearInterval(interval);
  }, [taskId, status, toast, onScrapingComplete]);

  const handleStartScraping = async () => {
    setStatus("scraping");
    setProgress(0);
    setResult(null);
    setErrorMessage("");
    setPostsFound(0);
    setPostsSaved(0);

    try {
      // Start async scraping
      const response = await axios.post(
        `http://localhost:8000/api/sources/${sourceId}/scrape-async`
      );

      if (response.data.task_id) {
        setTaskId(response.data.task_id);
        setTaskMessage("Analyzing website structure...");
      } else {
        setStatus("error");
        setErrorMessage("Failed to start scraping task");
      }
    } catch (error: any) {
      setStatus("error");
      const errorMsg =
        error.response?.data?.message ||
        "Network error: Make sure the backend is running";
      setErrorMessage(errorMsg);

      toast({
        title: "❌ Scraping Error",
        description: errorMsg,
        variant: "destructive",
      });
    }
  };

  const handleClose = () => {
    if (status !== "scraping" && status !== "processing") {
      setStatus("idle");
      setProgress(0);
      setResult(null);
      setErrorMessage("");
      setTaskId(null);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>🚀 Run Website Scraper</DialogTitle>
          <DialogDescription>{sourceName}</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Status States */}
          {status === "idle" && (
            <Card className="border-border/50 bg-background/50">
              <CardContent className="pt-6 space-y-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
                  <p className="text-sm text-blue-900 dark:text-blue-100">
                    💡 The system will visit {sourceName}, automatically detect content patterns (2-3 sec),
                    extract posts, and analyze for content risks.
                  </p>
                </div>

                <Button
                  onClick={handleStartScraping}
                  className="w-full"
                  size="lg"
                >
                  <Play className="mr-2 h-4 w-4" />
                  Start Scraping Now
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Scraping/Processing States */}
          {(status === "scraping" || status === "processing") && (
            <Card className="border-border/50 bg-background/50">
              <CardContent className="pt-6 space-y-4">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {status === "scraping" ? "Scraping in Progress..." : "Processing..."}
                    </span>
                    <span className="text-xs font-mono text-muted-foreground">
                      {Math.round(progress)}%
                    </span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>

                {/* Real-time Task Message */}
                <div className="flex items-start gap-2 p-3 bg-muted/50 rounded-lg border border-border/50">
                  <Loader2 className="h-4 w-4 text-primary animate-spin flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground font-medium truncate">
                      {taskMessage}
                    </p>
                  </div>
                </div>

                {/* Live Stats */}
                {(postsFound > 0 || postsSaved > 0) && (
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 bg-blue-50 dark:bg-blue-950 rounded border border-blue-200 dark:border-blue-800">
                      <p className="text-xs text-muted-foreground">Posts Found</p>
                      <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{postsFound}</p>
                    </div>
                    <div className="p-2 bg-green-50 dark:bg-green-950 rounded border border-green-200 dark:border-green-800">
                      <p className="text-xs text-muted-foreground">Saved</p>
                      <p className="text-lg font-bold text-green-600 dark:text-green-400">{postsSaved}</p>
                    </div>
                  </div>
                )}

                <div className="text-xs text-muted-foreground text-center">
                  Scraping runs in the background. You can close this dialog and check progress later.
                </div>
              </CardContent>
            </Card>
          )}

          {/* Completed State */}
          {status === "complete" && result && (
            <Card className="border-border/50 bg-background/50">
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
                  <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0" />
                  <span className="text-sm font-medium text-green-900 dark:text-green-100">
                    ✅ Scraping Complete!
                  </span>
                </div>

                {/* Results Summary */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-muted rounded-lg border border-border/30">
                    <p className="text-xs text-muted-foreground">Posts Found</p>
                    <p className="text-2xl font-bold text-primary">
                      {result.posts_found}
                    </p>
                  </div>

                  <div className="p-3 bg-muted rounded-lg border border-border/30">
                    <p className="text-xs text-muted-foreground">Posts Saved</p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {result.posts_saved}
                    </p>
                  </div>
                </div>

                <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
                  <p className="text-xs text-blue-900 dark:text-blue-100">
                    📊 Posts are now in your database. The Sources page will update automatically with counts.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error State */}
          {status === "error" && (
            <Card className="border-border/50 bg-background/50">
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-start gap-3 p-3 bg-red-50 dark:bg-red-950 rounded-lg border border-red-200 dark:border-red-800">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-900 dark:text-red-100">
                      Scraping Failed
                    </p>
                    <p className="text-xs text-red-800 dark:text-red-200 mt-1">
                      {errorMessage}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">
                    Next steps:
                  </p>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    <li>
                      • Check that the website is accessible  
                    </li>
                    <li>• Verify the backend server is running on localhost:8000</li>
                    <li>• Try again with a different website</li>
                  </ul>
                </div>

                <Button
                  onClick={handleStartScraping}
                  className="w-full"
                  variant="outline"
                >
                  Try Again
                </Button>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Footer Button */}
        {status !== "scraping" && status !== "processing" && (
          <div className="pt-2">
            <Button
              onClick={handleClose}
              variant="outline"
              className="w-full"
              disabled={status === "scraping" || status === "processing"}
            >
              {status === "complete" ? "Close" : "Close"}
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
