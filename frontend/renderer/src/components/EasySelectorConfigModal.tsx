import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  Wand2,
  Play,
  SkipForward,
} from "lucide-react";
import axios from "axios";
import { useToast } from "@/hooks/use-toast";

interface EasySelectorConfigModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sourceId: number;
  sourceName: string;
  sourceUrl: string;
  onConfigurationComplete?: () => void;
  onReadyToScrape?: () => void;
}

export function EasySelectorConfigModal({
  open,
  onOpenChange,
  sourceId,
  sourceName,
  sourceUrl,
  onConfigurationComplete,
  onReadyToScrape,
}: EasySelectorConfigModalProps) {
  const { toast } = useToast();
  const [step, setStep] = useState<"start" | "detecting" | "preview" | "saving" | "complete">("start");
  const [previewData, setPreviewData] = useState<any>(null);
  const [detectedSelectors, setDetectedSelectors] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleAutoDetect = async () => {
    setIsProcessing(true);
    setStep("detecting");

    try {
      // Call auto-detect API immediately (no artificial delay)
      // Set timeout to 6 seconds total
      const response = await axios.post(
        `http://localhost:8000/api/sources/${sourceId}/selectors/auto-detect`,
        {},
        { timeout: 6000 }
      );

      if (response.data.success) {
        // Store the detected selectors for later use
        setDetectedSelectors(response.data.selectors);
        
        // Validate selectors
        const validateResponse = await axios.post(
          `http://localhost:8000/api/sources/${sourceId}/selectors/validate`,
          response.data.selectors
        );

        if (validateResponse.data.valid) {
          setPreviewData(validateResponse.data);
          setStep("preview");
        }
      } else {
        toast({
          title: "Auto-Detection Issue",
          description: response.data.message || "Could not auto-detect. Using fallback selectors.",
          variant: "destructive",
        });
        // Still proceed with saving
        const selectors = {
          post_selector: "article, .post, .entry",
          content_selector: ".content, .text, p",
          title_selector: "h2, h3, .title",
          author_selector: ".author, .writer",
          date_selector: "time, .date",
          link_selector: "a",
          image_selector: "img",
        };
        
        setDetectedSelectors(selectors);
        setStep("saving");
        await saveSelectors(selectors);
      }
    } catch (error: any) {
      toast({
        title: "❌ Auto-Detection Failed",
        description: "Please check the website URL and try again.",
        variant: "destructive",
      });
      setStep("start");
    } finally {
      setIsProcessing(false);
    }
  };

  const saveSelectors = async (selectors: any) => {
    try {
      const response = await axios.post(
        `http://localhost:8000/api/sources/${sourceId}/selectors`,
        selectors
      );

      if (response.status === 200) {
        setStep("complete");
        toast({
          title: "✅ Configuration Saved",
          description: "Ready to start scraping!",
        });
        
        setTimeout(() => {
          onConfigurationComplete?.();
          onOpenChange(false);
        }, 1500);
      }
    } catch (error: any) {
      toast({
        title: "❌ Error",
        description: error.response?.data?.detail || "Failed to save configuration.",
        variant: "destructive",
      });
      setStep("start");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmAndSave = async () => {
    setIsProcessing(true);
    setStep("saving");

    // Use the auto-detected selectors (not hardcoded defaults!)
    const selectors = detectedSelectors || {
      post_selector: "article, .post, .entry",
      content_selector: ".content, .text, p",
      title_selector: "h2, h3, .title",
      author_selector: ".author, .writer",
      date_selector: "time, .date",
      link_selector: "a",
      image_selector: "img",
    };

    await saveSelectors(selectors);
  };

  const handleSkipAndUseDefaults = async () => {
    setIsProcessing(true);
    setStep("saving");

    const defaultSelectors = {
      post_selector: "article, .post, .entry, .blog-post",
      content_selector: ".post-content, .entry-content, .content, p, .text",
      title_selector: "h1, h2, h3, .post-title, .title, .headline",
      author_selector: ".author, .writer, .by-author, .contributor",
      date_selector: "time, .date, .published, .entry-date, .post-date",
      link_selector: "a, [href]",
      image_selector: "img, .image, .featured-image",
    };

    await saveSelectors(defaultSelectors);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>⚙️ Quick Setup: {sourceName}</DialogTitle>
          <DialogDescription>
            {step === "start" && "Let's get your scraper ready in 30 seconds"}
            {step === "detecting" && "Analyzing website structure..."}
            {step === "preview" && "Preview of extracted data"}
            {step === "saving" && "Saving configuration..."}
            {step === "complete" && "All set!"}
          </DialogDescription>
        </DialogHeader>

        {/* START */}
        {step === "start" && (
          <div className="space-y-4">
            <Card className="border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950">
              <CardContent className="pt-4">
                <p className="text-sm text-blue-900 dark:text-blue-100">
                  🏃 <strong>Super Simple Process:</strong>
                </p>
                <ul className="text-xs text-blue-800 dark:text-blue-200 mt-2 space-y-1">
                  <li>✓ Click "Auto-Detect" to analyze the website</li>
                  <li>✓ Review the preview (takes ~2 seconds)</li>
                  <li>✓ Click "Ready!" to save and start scraping</li>
                </ul>
              </CardContent>
            </Card>

            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">Website:</p>
              <p className="text-sm font-medium break-all">{sourceUrl}</p>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isProcessing}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={handleAutoDetect}
                disabled={isProcessing}
                className="flex-1 bg-primary hover:bg-primary/90"
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <Wand2 className="mr-2 h-4 w-4" />
                    Auto-Detect
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* DETECTING */}
        {step === "detecting" && (
          <div className="space-y-6 py-8 text-center">
            <div className="flex justify-center">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
            </div>
            <div>
              <p className="font-medium text-sm">🚀 Analyzing website structure...</p>
              <p className="text-xs text-muted-foreground mt-2">
                This usually takes 2-3 seconds
              </p>
            </div>
          </div>
        )}

        {/* PREVIEW */}
        {step === "preview" && (
          <div className="space-y-4">
            <Alert className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
              <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
              <AlertDescription className="text-green-900 dark:text-green-100">
                ✅ Successfully detected {previewData?.posts?.length || 3} sample posts!
              </AlertDescription>
            </Alert>

            <div className="space-y-2 max-h-48 overflow-y-auto">
              <p className="text-xs font-semibold text-muted-foreground">Sample Posts:</p>
              {previewData?.posts?.slice(0, 3).map((post: any, idx: number) => (
                <Card key={idx} className="border-border/30 border p-3">
                  <p className="text-xs font-medium line-clamp-1">
                    {post.title || "No title"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                    {post.content?.substring(0, 80) || "No content"}...
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {post.author} • {post.date || "No date"}
                  </p>
                </Card>
              ))}
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Does the preview look correct? If yes, click "Ready!" to proceed.
              </AlertDescription>
            </Alert>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setStep("start")}
                className="flex-1"
              >
                Back
              </Button>
              <Button
                onClick={handleConfirmAndSave}
                disabled={isProcessing}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Ready!
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* SAVING */}
        {step === "saving" && (
          <div className="space-y-6 py-8 text-center">
            <div className="flex justify-center">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
            </div>
            <div>
              <p className="font-medium text-sm">Saving configuration...</p>
              <p className="text-xs text-muted-foreground mt-2">
                Almost there!
              </p>
            </div>
          </div>
        )}

        {/* COMPLETE */}
        {step === "complete" && (
          <div className="space-y-4 py-4 text-center">
            <CheckCircle2 className="h-12 w-12 text-green-600 dark:text-green-400 mx-auto" />
            <div>
              <p className="font-semibold text-green-900 dark:text-green-100">
                ✅ All Set!
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Your scraper is configured and ready to go!
              </p>
            </div>

            <Card className="bg-primary/10 border-primary/20">
              <CardContent className="pt-4">
                <p className="text-sm font-medium text-primary">
                  Next: Click the "▶️ Run" button to start scraping!
                </p>
              </CardContent>
            </Card>

            <Button
              onClick={() => {
                onReadyToScrape?.();
                onOpenChange(false);
              }}
              className="w-full bg-primary hover:bg-primary/90"
            >
              <Play className="mr-2 h-4 w-4" />
              Close & Start Scraping
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
