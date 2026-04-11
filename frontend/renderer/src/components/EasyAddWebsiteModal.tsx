import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  Globe,
  Zap,
  BookOpen,
} from "lucide-react";
import axios from "axios";
import { useToast } from "@/hooks/use-toast";

interface EasyAddWebsiteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onWebsiteAdded?: (sourceId: number, sourceName: string) => void;
}

export function EasyAddWebsiteModal({
  open,
  onOpenChange,
  onWebsiteAdded,
}: EasyAddWebsiteModalProps) {
  const { toast } = useToast();
  const [step, setStep] = useState<"input" | "verifying" | "success">("input");
  
  const [websiteName, setWebsiteName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [createdSourceId, setCreatedSourceId] = useState<number | null>(null);

  const handleAddWebsite = async () => {
    if (!websiteName.trim() || !websiteUrl.trim()) {
      toast({
        title: "Missing Information",
        description: "Please enter both website name and URL",
        variant: "destructive",
      });
      return;
    }

    // Validate URL format
    try {
      new URL(websiteUrl);
    } catch {
      toast({
        title: "Invalid URL",
        description: "Please enter a valid URL (e.g., https://example.com)",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    setStep("verifying");

    try {
      const response = await axios.post("http://localhost:8000/api/sources", {
        source_name: websiteName,
        platform: "website",
        url: websiteUrl,
      });

      if (response.status === 200 || response.status === 201) {
        const sourceId = response.data.source_id;
        setCreatedSourceId(sourceId);
        setStep("success");

        toast({
          title: "✅ Website Added",
          description: `"${websiteName}" added successfully. Click "Configure Now" to set up scrapers.`,
        });
      }
    } catch (error: any) {
      setStep("input");
      toast({
        title: "❌ Error",
        description:
          error.response?.data?.detail ||
          "Failed to add website. Check the URL and try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setStep("input");
    setWebsiteName("");
    setWebsiteUrl("");
    setCreatedSourceId(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>🌐 Add Website Source</DialogTitle>
          <DialogDescription>
            {step === "input" && "Add any website to start scraping"}
            {step === "verifying" && "Verifying website..."}
            {step === "success" && "Website added successfully!"}
          </DialogDescription>
        </DialogHeader>

        {/* Input Step */}
        {step === "input" && (
          <div className="space-y-4">
            <Alert className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
              <Globe className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <AlertDescription className="text-blue-900 dark:text-blue-100">
                Just enter the website name and URL. We'll handle all the technical setup!
              </AlertDescription>
            </Alert>

            <div className="space-y-2">
              <label className="text-sm font-medium">Website Name</label>
              <Input
                placeholder="e.g., BBC News"
                value={websiteName}
                onChange={(e) => setWebsiteName(e.target.value)}
                disabled={isLoading}
                className="text-base"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Website URL</label>
              <Input
                placeholder="e.g., https://www.bbc.com/news"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                disabled={isLoading}
                className="text-base"
              />
              <p className="text-xs text-muted-foreground">
                Must start with http:// or https://
              </p>
            </div>

            <Button
              onClick={handleAddWebsite}
              disabled={isLoading || !websiteName.trim() || !websiteUrl.trim()}
              className="w-full"
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Zap className="mr-2 h-4 w-4" />
                  Add Website
                </>
              )}
            </Button>
          </div>
        )}

        {/* Verifying Step */}
        {step === "verifying" && (
          <div className="space-y-4 py-8 text-center">
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
            <div>
              <p className="text-sm font-medium">Verifying website...</p>
              <p className="text-xs text-muted-foreground mt-1">
                Setting up {websiteName}
              </p>
            </div>
          </div>
        )}

        {/* Success Step */}
        {step === "success" && (
          <div className="space-y-4">
            <div className="flex justify-center">
              <CheckCircle2 className="h-12 w-12 text-green-600 dark:text-green-400" />
            </div>

            <Card className="border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950">
              <CardContent className="pt-4">
                <p className="text-sm font-medium text-green-900 dark:text-green-100">
                  ✅ {websiteName} is ready!
                </p>
                <p className="text-xs text-green-800 dark:text-green-200 mt-2">
                  Source ID: <Badge variant="secondary">{createdSourceId}</Badge>
                </p>
              </CardContent>
            </Card>

            <Alert className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
              <BookOpen className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <AlertDescription className="text-blue-900 dark:text-blue-100">
                Now click "Configure Now" to auto-detect CSS selectors, then "Run" to start scraping!
              </AlertDescription>
            </Alert>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleClose}
                className="flex-1"
              >
                Close
              </Button>
              <Button
                onClick={() => {
                  if (createdSourceId) {
                    onWebsiteAdded?.(createdSourceId, websiteName);
                    handleClose();
                  }
                }}
                className="flex-1"
              >
                Configure Now →
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
