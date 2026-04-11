import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  Eye,
  Save,
  Wand2,
} from "lucide-react";
import axios from "axios";
import { useToast } from "@/hooks/use-toast";

interface WebsiteScraperConfigModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sourceId: number;
  sourceName: string;
  sourceUrl: string;
  onConfigSaved?: () => void;
}

interface SelectorConfig {
  post_selector: string;
  content_selector: string;
  title_selector: string;
  author_selector: string;
  date_selector: string;
  link_selector: string;
  image_selector: string;
}

interface PreviewData {
  success: boolean;
  posts: Array<{
    title: string;
    content: string;
    author: string;
    date: string;
    link: string;
  }>;
  message?: string;
}

export function WebsiteScraperConfigModal({
  open,
  onOpenChange,
  sourceId,
  sourceName,
  sourceUrl,
  onConfigSaved,
}: WebsiteScraperConfigModalProps) {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState("auto-detect");
  const [isLoading, setIsLoading] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const [selectors, setSelectors] = useState<SelectorConfig>({
    post_selector: "",
    content_selector: "",
    title_selector: "",
    author_selector: "",
    date_selector: "",
    link_selector: "",
    image_selector: "",
  });

  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);

  // Auto-detect selectors
  const handleAutoDetect = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(
        `http://localhost:8000/api/sources/${sourceId}/selectors/auto-detect`
      );

      if (response.data.success) {
        setSelectors({
          post_selector: response.data.selectors?.post_selector || "",
          content_selector: response.data.selectors?.content_selector || "",
          title_selector: response.data.selectors?.title_selector || "",
          author_selector: response.data.selectors?.author_selector || "",
          date_selector: response.data.selectors?.date_selector || "",
          link_selector: response.data.selectors?.link_selector || "",
          image_selector: response.data.selectors?.image_selector || "",
        });

        toast({
          title: "✅ Auto-Detection Complete",
          description: "CSS selectors have been detected. Review and validate them below.",
        });

        setActiveTab("preview");
      } else {
        toast({
          title: "⚠️ Auto-Detection Failed",
          description: response.data.message || "Could not auto-detect selectors.",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      toast({
        title: "❌ Error",
        description: error.response?.data?.message || "Failed to auto-detect selectors.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Validate selectors with preview
  const handleValidateSelectors = async () => {
    setIsValidating(true);
    try {
      const response = await axios.post(
        `http://localhost:8000/api/sources/${sourceId}/selectors/validate`,
        selectors
      );

      if (response.data.success) {
        setPreviewData(response.data);
        setShowPreviewDialog(true);
        toast({
          title: "✅ Validation Successful",
          description: `Found ${response.data.posts?.length || 0} samples to preview.`,
        });
      } else {
        toast({
          title: "⚠️ Validation Failed",
          description: response.data.message || "Selectors did not extract any data.",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      toast({
        title: "❌ Error",
        description: error.response?.data?.message || "Failed to validate selectors.",
        variant: "destructive",
      });
    } finally {
      setIsValidating(false);
    }
  };

  // Save selectors to database
  const handleSaveSelectors = async () => {
    if (!selectors.post_selector || !selectors.content_selector) {
      toast({
        title: "⚠️ Missing Required Selectors",
        description: "Post Selector and Content Selector are required.",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    try {
      const response = await axios.post(
        `http://localhost:8000/api/sources/${sourceId}/selectors`,
        selectors
      );

      if (response.data.success || response.status === 200) {
        toast({
          title: "✅ Selectors Saved",
          description: "CSS selectors have been saved. You can now run the scraper.",
        });
        onConfigSaved?.();
        onOpenChange(false);
      }
    } catch (error: any) {
      toast({
        title: "❌ Error",
        description: error.response?.data?.message || "Failed to save selectors.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSelectorChange = (key: keyof SelectorConfig, value: string) => {
    setSelectors((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-2xl max-h-96 overflow-y-auto">
          <DialogHeader>
            <DialogTitle>🔧 Configure Website Scraper</DialogTitle>
            <DialogDescription>
              {sourceName} • {sourceUrl}
            </DialogDescription>
          </DialogHeader>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="auto-detect" className="flex items-center gap-2">
                <Wand2 className="h-4 w-4" />
                Auto-Detect
              </TabsTrigger>
              <TabsTrigger value="manual" className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Manual
              </TabsTrigger>
              <TabsTrigger value="preview" className="flex items-center gap-2">
                <Eye className="h-4 w-4" />
                Preview
              </TabsTrigger>
            </TabsList>

            {/* Auto-Detect Tab */}
            <TabsContent value="auto-detect" className="space-y-4 mt-4">
              <Card className="border-border/50 bg-background/50">
                <CardHeader>
                  <CardTitle className="text-base">Auto-Detect CSS Selectors</CardTitle>
                  <CardDescription>
                    The system will visit your website and automatically detect common CSS selector patterns
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-sm text-blue-900 dark:text-blue-100">
                      💡 <strong>How it works:</strong> This feature analyzes your website's HTML to find patterns for posts, titles, content, and other elements.
                    </p>
                  </div>

                  <Button
                    onClick={handleAutoDetect}
                    disabled={isLoading}
                    className="w-full"
                    size="lg"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing Website...
                      </>
                    ) : (
                      <>
                        <Wand2 className="mr-2 h-4 w-4" />
                        Start Auto-Detection
                      </>
                    )}
                  </Button>

                  {selectors.post_selector && (
                    <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-green-900 dark:text-green-100">
                            ✅ Selectors detected!
                          </p>
                          <p className="text-xs text-green-800 dark:text-green-200 mt-1">
                            Click the "Preview" tab to validate and review extracted data.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Manual Tab */}
            <TabsContent value="manual" className="space-y-4 mt-4">
              <Card className="border-border/50 bg-background/50">
                <CardHeader>
                  <CardTitle className="text-base">Manual CSS Selectors</CardTitle>
                  <CardDescription>
                    Enter CSS selectors to extract data from your website
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    {/* Post Selector */}
                    <div>
                      <label className="text-sm font-medium">
                        📦 Post Container Selector
                        <Badge variant="destructive" className="ml-2">Required</Badge>
                      </label>
                      <p className="text-xs text-muted-foreground mt-1 mb-2">
                        CSS selector for the container of each post (e.g., article, .post, .item)
                      </p>
                      <Input
                        placeholder="e.g., article.post, .news-item, div.article"
                        value={selectors.post_selector}
                        onChange={(e) =>
                          handleSelectorChange("post_selector", e.target.value)
                        }
                        className="font-mono text-xs"
                      />
                    </div>

                    {/* Content Selector */}
                    <div>
                      <label className="text-sm font-medium">
                        📝 Content Selector
                        <Badge variant="destructive" className="ml-2">Required</Badge>
                      </label>
                      <p className="text-xs text-muted-foreground mt-1 mb-2">
                        CSS selector for the main post content/text
                      </p>
                      <Input
                        placeholder="e.g., .content, p, div.text, .body"
                        value={selectors.content_selector}
                        onChange={(e) =>
                          handleSelectorChange("content_selector", e.target.value)
                        }
                        className="font-mono text-xs"
                      />
                    </div>

                    {/* Title Selector */}
                    <div>
                      <label className="text-sm font-medium">
                        📄 Title Selector
                        <Badge variant="outline" className="ml-2">Optional</Badge>
                      </label>
                      <p className="text-xs text-muted-foreground mt-1 mb-2">
                        CSS selector for post title/headline
                      </p>
                      <Input
                        placeholder="e.g., h2, .title, h1.headline"
                        value={selectors.title_selector}
                        onChange={(e) =>
                          handleSelectorChange("title_selector", e.target.value)
                        }
                        className="font-mono text-xs"
                      />
                    </div>

                    {/* Author Selector */}
                    <div>
                      <label className="text-sm font-medium">
                        👤 Author Selector
                        <Badge variant="outline" className="ml-2">Optional</Badge>
                      </label>
                      <Input
                        placeholder="e.g., .author, span.by, [data-author]"
                        value={selectors.author_selector}
                        onChange={(e) =>
                          handleSelectorChange("author_selector", e.target.value)
                        }
                        className="font-mono text-xs"
                      />
                    </div>

                    {/* Date Selector */}
                    <div>
                      <label className="text-sm font-medium">
                        📅 Date Selector
                        <Badge variant="outline" className="ml-2">Optional</Badge>
                      </label>
                      <Input
                        placeholder="e.g., time, .date, [data-date]"
                        value={selectors.date_selector}
                        onChange={(e) =>
                          handleSelectorChange("date_selector", e.target.value)
                        }
                        className="font-mono text-xs"
                      />
                    </div>

                    {/* Link Selector */}
                    <div>
                      <label className="text-sm font-medium">
                        🔗 Link Selector
                        <Badge variant="outline" className="ml-2">Optional</Badge>
                      </label>
                      <Input
                        placeholder="e.g., a, a.post-link, [href]"
                        value={selectors.link_selector}
                        onChange={(e) =>
                          handleSelectorChange("link_selector", e.target.value)
                        }
                        className="font-mono text-xs"
                      />
                    </div>

                    {/* Image Selector */}
                    <div>
                      <label className="text-sm font-medium">
                        🖼️ Image Selector
                        <Badge variant="outline" className="ml-2">Optional</Badge>
                      </label>
                      <Input
                        placeholder="e.g., img, .image, .thumbnail"
                        value={selectors.image_selector}
                        onChange={(e) =>
                          handleSelectorChange("image_selector", e.target.value)
                        }
                        className="font-mono text-xs"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Preview Tab */}
            <TabsContent value="preview" className="space-y-4 mt-4">
              <Button
                onClick={handleValidateSelectors}
                disabled={isValidating || (!selectors.post_selector && !selectors.content_selector)}
                className="w-full"
                size="lg"
              >
                {isValidating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Validating...
                  </>
                ) : (
                  <>
                    <Eye className="mr-2 h-4 w-4" />
                    Validate & Preview
                  </>
                )}
              </Button>

              {previewData && (
                <Card className="border-border/50 bg-background/50">
                  <CardHeader>
                    <CardTitle className="text-base">Preview Results</CardTitle>
                    <CardDescription>
                      {previewData.posts?.length || 0} sample post(s) extracted
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 max-h-64 overflow-y-auto">
                    {previewData.posts && previewData.posts.length > 0 ? (
                      previewData.posts.map((post, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-muted rounded-lg border border-border/30 space-y-2"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              {post.title && (
                                <p className="font-semibold text-sm truncate">
                                  {post.title}
                                </p>
                              )}
                              <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                {post.content?.substring(0, 100)}...
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>{post.author || "Unknown"}</span>
                            <span>{post.date || "No date"}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-4 text-muted-foreground">
                        <AlertCircle className="h-4 w-4 mx-auto mb-2 opacity-50" />
                        <p className="text-xs">No data extracted. Check your selectors.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveSelectors}
              disabled={isSaving || !selectors.post_selector || !selectors.content_selector}
              className="flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Selectors
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <AlertDialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Preview Data Extraction</AlertDialogTitle>
            <AlertDialogDescription>
              Review the extracted data below. If it looks correct, click "Looks Good" to proceed with saving.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="space-y-3 max-h-64 overflow-y-auto">
            {previewData?.posts && previewData.posts.length > 0 ? (
              previewData.posts.map((post, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-muted rounded-lg border border-border/30 space-y-2"
                >
                  {post.title && (
                    <p className="font-semibold text-sm">{post.title}</p>
                  )}
                  <p className="text-xs text-muted-foreground">{post.content}</p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{post.author || "Unknown"}</span>
                    <span>{post.date || "No date"}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                <p className="text-sm">No data to preview</p>
              </div>
            )}
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel>Need to adjust</AlertDialogCancel>
            <AlertDialogAction onClick={() => {
              setShowPreviewDialog(false);
              handleSaveSelectors();
            }}>
              Looks Good
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
