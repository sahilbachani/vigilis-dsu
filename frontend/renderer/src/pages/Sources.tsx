import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Database, RefreshCw, Trash2, ChevronDown, ChevronUp, Globe, Zap, AlertCircle, Twitter, Music, Settings, Play } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/StatusBadge";
import { useSources, useScrapedPosts } from "@/hooks/use-content";
import { Skeleton } from "@/components/ui/skeleton";
import { AddSourceModal } from "@/components/AddSourceModal";
import { WebsiteScraperConfigModal } from "@/components/WebsiteScraperConfigModal";
import { ScraperProgressModal } from "@/components/ScraperProgressModal";
import { EasyAddWebsiteModal } from "@/components/EasyAddWebsiteModal";
import { EasySelectorConfigModal } from "@/components/EasySelectorConfigModal";
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
import { useState } from "react";
import axios from "axios";
import { useToast } from "@/hooks/use-toast";

const BUILTIN_SCRAPERS = [
  { id: "twitter", name: "Twitter (X) Scraper", type: "Social Media", status: "Running", icon: Twitter },
  { id: "facebook", name: "Facebook Scraper", type: "Social Media", status: "Running" },
  { id: "tiktok", name: "TikTok Scraper", type: "Social Media", status: "Running", icon: Music },
];

const BUILTIN_WEBSITES = [
  { id: "dawn", name: "Dawn News", url: "https://www.dawn.com", status: "Active", itemsScanned: 127, lastSync: "2:45 PM" },
  { id: "jihad", name: "Intel Jihad", url: "https://www.inteljihad.com", status: "Active", itemsScanned: 89, lastSync: "3:10 PM" },
  { id: "khorasan", name: "Khorasan Watch", url: "https://www.khorasanwatch.com", status: "Active", itemsScanned: 56, lastSync: "2:30 PM" },
  { id: "bellingcat", name: "Bellingcat", url: "https://www.bellingcat.com", status: "Active", itemsScanned: 203, lastSync: "1:15 PM" },
];

export default function Sources() {
  const { data: sources, isLoading, refetch } = useSources();
  const { data: posts, refetch: refetchPosts } = useScrapedPosts();
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [easyAddModalOpen, setEasyAddModalOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [expandedSourceId, setExpandedSourceId] = useState<string | number | null>(null);
  const [sourceToDelete, setSourceToDelete] = useState<{
    id: string | number;
    name: string;
    type?: string;
  } | null>(null);
  const [isScrapingStarting, setIsScrapingStarting] = useState<number | null>(null);
  const [configModalOpen, setConfigModalOpen] = useState(false);
  const [easyConfigModalOpen, setEasyConfigModalOpen] = useState(false);
  const [configSourceId, setConfigSourceId] = useState<number | null>(null);
  const [configSourceName, setConfigSourceName] = useState<string>("");
  const [configSourceUrl, setConfigSourceUrl] = useState<string>("");
  const [scraperModalOpen, setScraperModalOpen] = useState(false);
  const [scraperSourceId, setScraperSourceId] = useState<number | null>(null);
  const [scraperSourceName, setScraperSourceName] = useState<string>("");
  const { toast } = useToast();

  // Get post count and last sync for each source
  const getSourceStats = (sourceId: number) => {
    const sourcePosts = posts?.filter((p: any) => p.source_id === sourceId) || [];
    const lastPost = sourcePosts[0];
    const lastSync = lastPost?.added_date 
      ? new Date(lastPost.added_date).toLocaleTimeString()
      : "Never";
    return {
      count: sourcePosts.length,
      lastSync,
      posts: sourcePosts
    };
  };

  const handleDeleteClick = (source: any) => {
    setSourceToDelete({ 
      id: source.id || source.source_id, 
      name: source.source_name || source.name,
      type: "user"
    });
    setDeleteConfirmOpen(true);
  };

  const handleStartScraping = async (source: any) => {
    const sourceId = source.source_id || source.id;
    setIsScrapingStarting(sourceId);
    
    try {
      const response = await axios.post(
        "http://localhost:8000/api/scraper/run",
        {
          platform: `website-${sourceId}`
        }
      );
      
      toast({
        title: "Scraping Started",
        description: `Started scraping "${source.source_name}" automatically.`,
      });
    } catch (error) {
      console.error("Failed to start scraping:", error);
      toast({
        title: "Error",
        description: "Failed to start scraping. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsScrapingStarting(null);
    }
  };

  const handleScrapingComplete = (results: any) => {
    // Auto-refresh posts after scraping completes
    setTimeout(() => {
      refetchPosts();
    }, 1000);
  };

  const confirmDelete = async () => {
    if (!sourceToDelete) return;

    try {
      // Delete all posts from this source
      await axios.delete(
        `http://localhost:8000/api/post?source_id=${sourceToDelete.id}`
      );

      toast({
        title: "Deleted",
        description: `All posts from "${sourceToDelete.name}" have been removed.`,
      });

      setDeleteConfirmOpen(false);
      setSourceToDelete(null);
      await refetch();
    } catch (error) {
      console.error("Failed to delete posts:", error);
      toast({
        title: "Error",
        description: "Failed to delete source. Please try again.",
        variant: "destructive",
      });
    }
  };

  if (isLoading) {
    return (
      <div className="w-full space-y-4 md:space-y-6">
        <div className="flex flex-col gap-3 md:gap-0 md:items-center md:justify-between">
          <Skeleton className="h-10 w-48" />
        </div>
        <Card>
          <CardHeader className="pb-3">
            <Skeleton className="h-8 w-32" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold tracking-tight text-foreground">Data Sources</h1>
          <p className="text-sm text-muted-foreground mt-2 font-medium">Manage inputs for the monitoring engine.</p>
        </div>
        <Button 
          className="text-xs font-semibold bg-primary hover:bg-primary/90 shadow-md py-2 h-auto" 
          onClick={() => setEasyAddModalOpen(true)}
        >
          <Plus className="mr-2 h-4 w-4" /> Add Website
        </Button>
      </div>

      <Card className="border-border/40 shadow-sm bg-gradient-to-br from-card to-card/95">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">Active Connections</CardTitle>
          <CardDescription className="text-sm">Real-time status of connected platforms and data streams.</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Desktop Table View */}
          <div className="overflow-x-auto -mx-6 px-6">
            <Table className="text-sm">
              <TableHeader>
                <TableRow className="border-border/50">
                  <TableHead className="w-8 font-medium text-xs"></TableHead>
                  <TableHead className="min-w-[180px] md:min-w-auto font-medium text-xs">Source Name</TableHead>
                  <TableHead className="min-w-[90px] md:min-w-auto font-medium text-xs">Type</TableHead>
                  <TableHead className="text-center min-w-[100px] md:min-w-auto font-medium text-xs">Items Scanned</TableHead>
                  <TableHead className="text-right min-w-[120px] md:min-w-auto font-medium text-xs">Last Sync</TableHead>
                  <TableHead className="w-32 font-medium text-xs text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {/* Built-in Scrapers */}
                {BUILTIN_SCRAPERS.map((scraper) => (
                  <TableRow key={scraper.id} className="hover:bg-muted/60 transition-colors">
                    <TableCell className="py-3 px-2"></TableCell>
                    <TableCell className="font-medium py-3">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-primary/20 rounded-md">
                          <Database className="h-4 w-4 text-primary flex-shrink-0" />
                        </div>
                        <span className="truncate font-semibold text-sm">{scraper.name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="py-3">
                      <span className="px-2.5 py-1 text-xs font-medium bg-primary/20 text-primary rounded-sm capitalize">
                        Web Scraper
                      </span>
                    </TableCell>
                    <TableCell className="text-center font-mono text-sm font-medium py-3">0</TableCell>
                    <TableCell className="text-right text-muted-foreground text-sm py-3">Never</TableCell>
                    <TableCell className="py-3">
                      <div className="flex justify-end gap-2">
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-all rounded"
                          onClick={() => refetch()}
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-8 w-8 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-all rounded"
                          onClick={() => {
                            setSourceToDelete({
                              id: scraper.id,
                              name: scraper.name,
                              type: "builtin"
                            });
                            setDeleteConfirmOpen(true);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}

                {/* Website/Blog Scraper Row - Expandable */}
                <TableRow className="hover:bg-muted/60 transition-colors">
                  <TableCell className="py-3 px-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => setExpandedSourceId(expandedSourceId === "websites" ? null : "websites")}
                    >
                      {expandedSourceId === "websites" ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </TableCell>
                  <TableCell className="font-medium py-3">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-primary/20 rounded-md">
                        <Globe className="h-4 w-4 text-primary flex-shrink-0" />
                      </div>
                      <span className="truncate font-semibold text-sm">Website / Blog Scraper</span>
                    </div>
                  </TableCell>
                  <TableCell className="py-3">
                    <span className="px-2.5 py-1 text-xs font-medium bg-primary/20 text-primary rounded-sm capitalize">
                      Web Scraper
                    </span>
                  </TableCell>
                  <TableCell className="text-center font-mono text-sm font-medium py-3">
                    {sources?.filter((s: any) => s.platform?.toLowerCase() === "website").reduce((sum: number, s: any) => sum + getSourceStats(s.id || s.source_id).count, 0) || 0}
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground text-sm py-3">
                    {sources && sources.filter((s: any) => s.platform?.toLowerCase() === "website").some((s: any) => getSourceStats(s.id || s.source_id).count > 0) ? "Now" : "Never"}
                  </TableCell>
                  <TableCell className="py-3">
                    <div className="flex justify-end gap-2">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-all rounded"
                        onClick={() => refetch()}
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>

                {/* Expanded Website/Blog Scrapers */}
                {expandedSourceId === "websites" && (
                  <TableRow className="bg-muted/30">
                    <TableCell colSpan={6} className="py-4">
                      <div className="ml-8 space-y-6">
                        {/* Available Website Scrapers */}
                        <div>
                          <h4 className="font-semibold text-sm mb-3">Available Website Scrapers</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                            {BUILTIN_WEBSITES.map((website) => (
                              <div
                                key={website.id}
                                className="p-3 bg-background/50 border border-border/30 rounded-lg"
                              >
                                <div className="flex items-start justify-between gap-2 mb-2">
                                  <div className="flex-1 min-w-0">
                                    <h5 className="font-medium text-sm truncate">{website.name}</h5>
                                    <p className="text-xs text-muted-foreground truncate">{website.url}</p>
                                  </div>
                                </div>
                                <div className="text-xs text-muted-foreground mb-2">
                                  {website.itemsScanned} posts • Last: {website.lastSync}
                                </div>
                                <div className="flex justify-end">
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                                    onClick={() => {
                                      setSourceToDelete({
                                        id: website.id,
                                        name: website.name,
                                        type: "builtin-website"
                                      });
                                      setDeleteConfirmOpen(true);
                                    }}
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Your Website Sources */}
                        <div>
                          <h4 className="font-semibold text-sm mb-3">Your Website Sources</h4>
                          {sources && sources.filter((s: any) => s.platform?.toLowerCase() === "website").length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                              {sources
                                .filter((s: any) => s.platform?.toLowerCase() === "website")
                                .map((website: any) => {
                                  const websiteId = website.id || website.source_id;
                                  const stats = getSourceStats(websiteId);
                                  return (
                                    <Card key={websiteId} className="border-border/30 bg-background/50 hover:border-primary/50 transition-all">
                                      <CardContent className="p-3 space-y-3">
                                        <div>
                                          <h5 className="font-semibold text-sm">{website.source_name}</h5>
                                          {website.url && (
                                            <p className="text-xs text-muted-foreground truncate">{website.url}</p>
                                          )}
                                        </div>

                                        <div className="text-xs text-muted-foreground">
                                          <span className="inline-block bg-muted px-2 py-1 rounded">
                                            {stats.count} posts
                                          </span>
                                          <span className="inline-block ml-2">Last: {stats.lastSync}</span>
                                        </div>

                                        <div className="flex gap-2">
                                          <Button
                                            size="sm"
                                            className="flex-1 text-xs h-8 bg-primary hover:bg-primary/90"
                                            onClick={() => {
                                              setScraperSourceId(websiteId);
                                              setScraperSourceName(website.source_name);
                                              setScraperModalOpen(true);
                                            }}
                                          >
                                            <Play className="h-3 w-3 mr-1" />
                                            Run
                                          </Button>

                                          <Button
                                            size="sm"
                                            variant="ghost"
                                            className="text-xs h-8 px-2"
                                            title="Advanced: Manually configure CSS selectors"
                                            onClick={() => {
                                              setConfigSourceId(websiteId);
                                              setConfigSourceName(website.source_name);
                                              setConfigSourceUrl(website.url);
                                              setEasyConfigModalOpen(true);
                                            }}
                                          >
                                            <Settings className="h-3 w-3" />
                                          </Button>

                                          <Button
                                            size="sm"
                                            variant="ghost"
                                            className="text-red-500 hover:text-red-600 hover:bg-red-500/10 h-8"
                                            onClick={() => handleDeleteClick(website)}
                                          >
                                            <Trash2 className="h-3 w-3" />
                                          </Button>
                                        </div>
                                      </CardContent>
                                    </Card>
                                  );
                                })}
                            </div>
                          ) : (
                            <div className="text-center py-4 text-muted-foreground">
                              <AlertCircle className="h-4 w-4 mx-auto mb-2 opacity-50" />
                              <p className="text-xs">No websites added yet. Click "Add Source" to add one.</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <AddSourceModal 
        open={addModalOpen}
        onOpenChange={setAddModalOpen}
        onSave={() => {
          refetch();
          setTimeout(() => {
            toast({
              title: "Website Added",
              description: "New website source added successfully.",
            });
          }, 500);
        }}
      />

      <EasyAddWebsiteModal
        open={easyAddModalOpen}
        onOpenChange={setEasyAddModalOpen}
        onWebsiteAdded={(sId, sName) => {
          refetch();
          setTimeout(() => {
            setConfigSourceId(sId);
            setConfigSourceName(sName);
            setEasyConfigModalOpen(true);
          }, 500);
        }}
      />

      <EasySelectorConfigModal
        open={easyConfigModalOpen}
        onOpenChange={setEasyConfigModalOpen}
        sourceId={configSourceId || 0}
        sourceName={configSourceName}
        sourceUrl={configSourceUrl}
        onConfigurationComplete={() => {
          refetch();
          setEasyConfigModalOpen(false);
        }}
        onReadyToScrape={() => {
          setScraperSourceId(configSourceId);
          setScraperSourceName(configSourceName);
          setScraperModalOpen(true);
        }}
      />

      <WebsiteScraperConfigModal
        open={configModalOpen}
        onOpenChange={setConfigModalOpen}
        sourceId={configSourceId || 0}
        sourceName={configSourceName}
        sourceUrl={configSourceUrl}
        onConfigSaved={() => {
          refetch();
          setConfigModalOpen(false);
        }}
      />

      <ScraperProgressModal
        open={scraperModalOpen}
        onOpenChange={setScraperModalOpen}
        sourceId={scraperSourceId || 0}
        sourceName={scraperSourceName}
        onScrapingComplete={(results) => {
          handleScrapingComplete(results);
          refetch();
          setScraperModalOpen(false);
        }}
      />

      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Posts</AlertDialogTitle>
            <AlertDialogDescription>
              Delete all posts from "{sourceToDelete?.name}"? This action cannot be undone, but the source will remain.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete Posts
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
