import { useState } from "react";
import { useScrapedPosts } from "@/hooks/use-content";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { StatusBadge } from "@/components/StatusBadge";
import { Input } from "@/components/ui/input";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Search, Filter, RefreshCw, MoreVertical, Trash2, CheckCircle2, Globe, Download, FileText } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { FlagPostModal } from "@/components/FlagPostModal";
import { FlaggedContent } from "@/types/FlaggedContent";
import axios from "axios";
import { useToast } from "@/hooks/use-toast";

export default function FlaggedPosts() {
  const [platform, setPlatform] = useState("All");
  const [category, setCategory] = useState("All");
  const [selectedPost, setSelectedPost] = useState<FlaggedContent | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<"selected" | "all" | "single" | null>(null);
  const [postToDelete, setPostToDelete] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { toast } = useToast();

 const { data, isLoading, refetch } = useScrapedPosts();

const posts: FlaggedContent[] | undefined = data;

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refetch();
      toast({
        title: "Refreshed",
        description: "Flagged posts data has been refreshed.",
      });
    } catch (error) {
      console.error("Failed to refresh:", error);
      toast({
        title: "Error",
        description: "Failed to refresh data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const filteredPosts = posts?.filter((post) => {
    const matchesPlatform = 
      platform === "All" || 
      (platform === "Twitter" && post.platform.includes("Twitter")) ||
      post.platform === platform;

    const matchesCategory = 
      category === "All" || 
      post.category === category;
    
    const matchesSearch = 
      searchQuery === "" ||
      post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.content?.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesPlatform && matchesCategory && matchesSearch;
  });

  const handleViewPost = (post: FlaggedContent) => {
    setSelectedPost(post);
    setIsModalOpen(true);
  };

  const toggleSelectPost = (postId: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(postId)) {
      newSelected.delete(postId);
    } else {
      newSelected.add(postId);
    }
    setSelectedIds(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredPosts?.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredPosts?.map((p: FlaggedContent) => p.id) || []));
    }
  };

  const handleMarkAsReviewedSelected = async () => {
    try {
      const idsArray = Array.from(selectedIds);
      
      if (idsArray.length === 0) return;

      // Mark each post as reviewed
      await Promise.all(
        idsArray.map(id =>
          axios.patch(`http://localhost:8000/api/post/${id}/mark-reviewed`)
        )
      );

      toast({
        title: "Marked as Reviewed",
        description: `Successfully marked ${idsArray.length} post(s) as reviewed.`,
      });

      // Refresh data and clear selection
      await refetch();
      setSelectedIds(new Set());
    } catch (error) {
      console.error("Failed to mark as reviewed:", error);
      toast({
        title: "Error",
        description: "Failed to mark posts as reviewed. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleExport = async (format: 'csv' | 'pdf') => {
    try {
      const response = await axios.get(
        'http://localhost:8000/api/post/export',
        { 
          params: { 
            format
          },
          responseType: 'blob'
        }
      );
      
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `flagged_posts_export.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: "Export Successful",
        description: `Flagged posts exported as ${format.toUpperCase()}.`,
      });
    } catch (error) {
      console.error("Export failed:", error);
      toast({
        title: "Export Failed",
        description: `Failed to export as ${format.toUpperCase()}. Please try again.`,
        variant: "destructive",
      });
    }
  };

  const handleDeleteSelected = () => {
    setDeleteTarget("selected");
    setShowDeleteConfirm(true);
  };

  const handleDeleteAll = () => {
    setDeleteTarget("all");
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    try {
      let idsToDelete: number[] = [];

      if (deleteTarget === "single" && postToDelete) {
        idsToDelete = [postToDelete];
      } else if (deleteTarget === "selected") {
        idsToDelete = Array.from(selectedIds);
      } else if (deleteTarget === "all") {
        idsToDelete = filteredPosts?.map(p => p.id) || [];
      }

      if (idsToDelete.length === 0) return;

      // Delete each post
      await Promise.all(
        idsToDelete.map(id => axios.delete(`http://localhost:8000/api/post/${id}`))
      );

      toast({
        title: "Deleted",
        description: `Successfully deleted ${idsToDelete.length} post(s).`,
      });

      // Refresh data
      refetch();
      
      // Cleanup
      if (deleteTarget === "selected" || deleteTarget === "all") {
        setSelectedIds(new Set());
      }
      setPostToDelete(null);
    } catch (error) {
      console.error("Failed to delete posts:", error);
      toast({
        title: "Error",
        description: "Failed to delete posts. Please try again.",
        variant: "destructive",
      });
    } finally {
      setShowDeleteConfirm(false);
      setDeleteTarget(null);
    }
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'twitter':
      case 'twitter/x':
        return <span className="inline-flex items-center justify-center h-4 w-4 bg-black dark:bg-white text-white dark:text-black rounded-sm text-xs font-bold mr-1.5">𝕏</span>;
      case 'facebook':
        return <span className="inline-flex items-center justify-center h-4 w-4 bg-blue-600 text-white rounded-sm text-xs font-bold mr-1.5">f</span>;
      case 'tiktok':
        return <span className="inline-flex items-center justify-center h-4 w-4 bg-black text-white rounded-sm text-xs font-bold mr-1.5">t</span>;
      case 'Dawn News':
      case 'Bellingcat':
      case 'Jihad Intel':
      case 'The Khorasan Diary':
      case 'Website / Blog':
        return <span className="inline-flex items-center justify-center h-4 w-4 bg-emerald-600 text-white rounded-sm text-xs font-bold mr-1.5"><Globe className="h-3 w-3" /></span>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold tracking-tight text-foreground">Text Content</h1>
          <p className="text-sm text-muted-foreground mt-2 font-medium">Review and moderate text-based content from social platforms.</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap md:flex-nowrap">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh} 
            disabled={isRefreshing || isLoading}
            className="text-xs font-medium border-border/30">
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} /> 
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm" className="text-xs font-semibold bg-primary hover:bg-primary/90 shadow-md">
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleExport('csv')}>
                <FileText className="h-4 w-4 mr-2" />
                Export as CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('pdf')}>
                <FileText className="h-4 w-4 mr-2" />
                Export as PDF
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 bg-card/40 backdrop-blur-sm p-4 rounded-md border border-border/30 shadow-sm bg-gradient-to-br from-card to-card/95">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search by title or content..." 
            className="pl-10 bg-background border-border/30 focus-visible:ring-primary/30 text-sm py-2" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex flex-col sm:flex-row gap-3 w-full">
          <Select value={platform} onValueChange={setPlatform}>
            <SelectTrigger className="w-full sm:flex-1 bg-background border-border/30 focus-visible:ring-primary/30 text-sm py-2">
              <Filter className="h-4 w-4 mr-2 text-muted-foreground" />
              <SelectValue placeholder="Platform" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All">All Platforms</SelectItem>
              <SelectItem value="Twitter/X">Twitter (X)</SelectItem>
              <SelectItem value="Facebook">Facebook</SelectItem>
              <SelectItem value="Dawn News">Dawn</SelectItem>
              <SelectItem value="Bellingcat">Bellingcat</SelectItem>
              <SelectItem value="Jihad Intel">Jihad Intel</SelectItem>
              <SelectItem value="The Khorasan Diary">Khorasan Diary</SelectItem>
              <SelectItem value="TikTok">TikTok</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger className="w-full sm:flex-1 bg-background border-border/30 focus-visible:ring-primary/30 text-sm py-2">
              <Filter className="h-4 w-4 mr-2 text-muted-foreground" />
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="All">All Categories</SelectItem>
              <SelectItem value="Hate Speech">Hate Speech</SelectItem>
              <SelectItem value="Violence">Violence</SelectItem>
              <SelectItem value="Misinformation">Misinformation</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Selected Actions */}
      {selectedIds.size > 0 && (
        <div className="flex flex-col gap-3 bg-primary/5 backdrop-blur-sm p-4 rounded-md border border-primary/20 shadow-sm bg-gradient-to-br from-primary/5 to-primary/10">
          <span className="text-sm font-medium text-foreground">
            {selectedIds.size} {selectedIds.size === 1 ? 'post' : 'posts'} selected
          </span>
          <div className="flex flex-col gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleMarkAsReviewedSelected}
              className="w-full md:w-auto text-xs justify-center md:justify-start border-primary/30 hover:bg-primary/10 font-medium"
              data-testid="button-mark-selected-reviewed"
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Mark Selected as Reviewed
            </Button>
            <div className="flex flex-col sm:flex-row gap-2">
              <Button 
                variant="outline" 
                size="sm"
                className="text-red-500 hover:text-red-600 hover:bg-red-500/10 text-sm flex-1 sm:flex-none border-red-500/30"
                onClick={handleDeleteSelected}
                data-testid="button-delete-selected"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Selected
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                className="text-red-500 hover:text-red-600 hover:bg-red-500/10 text-sm flex-1 sm:flex-none border-red-500/30"
                onClick={handleDeleteAll}
                data-testid="button-delete-all"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete All
              </Button>
              <Button 
                variant="ghost" 
                size="sm"
                className="text-sm flex-1 sm:flex-none"
                onClick={() => setSelectedIds(new Set())}
                data-testid="button-clear-selection"
              >
                Clear
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="rounded-lg border border-border/50 bg-gradient-to-br from-card to-card/95 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <Table className="text-sm">
            <TableHeader>
              <TableRow className="bg-muted/40 border-b border-border/50">
                <TableHead className="w-[40px] md:w-[50px] font-semibold text-foreground">
                  <Checkbox
                    checked={selectedIds.size > 0 && selectedIds.size === filteredPosts?.length}
                    onCheckedChange={toggleSelectAll}
                    data-testid="checkbox-select-all"
                  />
                </TableHead>
                <TableHead className="w-[50px] md:w-[80px] font-semibold text-foreground">ID</TableHead>
                <TableHead className="min-w-[150px] md:min-w-[200px] font-semibold text-foreground">Title</TableHead>
                <TableHead className="min-w-[90px] md:w-[100px] font-semibold text-foreground">Platform</TableHead>
                <TableHead className="min-w-[85px] md:w-[100px] font-semibold text-foreground">Category</TableHead>
                <TableHead className="min-w-[70px] md:w-[80px] font-semibold text-foreground">Confidence</TableHead>
                <TableHead className="min-w-[75px] md:w-[90px] font-semibold text-foreground">Date</TableHead>
                <TableHead className="min-w-[65px] md:w-[80px] font-semibold text-foreground">Status</TableHead>
                <TableHead className="w-[40px] md:w-[50px] font-semibold text-foreground">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i} className="border-border/50">
                    <TableCell><Skeleton className="h-4 w-4" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-14 rounded-full" /></TableCell>
                    <TableCell><Skeleton className="h-8 w-8 rounded-md" /></TableCell>
                  </TableRow>
                ))
              ) : filteredPosts?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="h-24 text-center text-muted-foreground">
                    <p className="font-medium">No flagged posts found</p>
                    <p className="text-xs mt-1">Try adjusting your filters</p>
                  </TableCell>
                </TableRow>
              ) : (
                filteredPosts?.map((post: FlaggedContent) => (
                  <TableRow 
                    key={post.id} 
                    className={`group hover:bg-muted/50 transition-colors border-border/50 py-3 ${selectedIds.has(post.id) ? 'bg-muted/60' : ''}`}
                    data-testid="row-flagged-post"
                  >
                    <TableCell className="py-3" onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedIds.has(post.id)}
                        onCheckedChange={() => toggleSelectPost(post.id)}
                        data-testid={`checkbox-post-${post.id}`}
                      />
                    </TableCell>
                    <TableCell 
                      onClick={() => handleViewPost(post)}
                      className="font-mono text-xs text-muted-foreground cursor-pointer py-3"
                    >
                      #{post.id}
                    </TableCell>
                    <TableCell 
                      onClick={() => handleViewPost(post)}
                      className="cursor-pointer py-3"
                    >
                      <p className="truncate font-semibold text-sm">{post.title}</p>
                    </TableCell>
                    <TableCell className="py-3">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-sm text-xs font-medium bg-primary/20 text-primary whitespace-nowrap">
                        {getPlatformIcon(post.platform)}
                        <span className="hidden sm:inline">{post.platform}</span>
                      </span>
                    </TableCell>
                    <TableCell className="text-sm py-3">{post.category}</TableCell>
                    <TableCell className="py-3">
                      <span className={post.confidenceScore > 90 ? "text-red-600 dark:text-red-400 font-bold text-sm" : "text-foreground text-sm font-semibold"}>
                        {post.confidenceScore}%
                      </span>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm whitespace-nowrap py-3.5">
                      {new Date(post.timestamp!).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="py-3">
                      <StatusBadge status={post.status} />
                    </TableCell>
                    <TableCell className="py-3">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button 
                            variant="ghost" 
                            className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-muted" 
                            data-testid="button-more-options"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem 
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewPost(post);
                            }} 
                            data-testid="menu-view-details"
                          >
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={(e) => e.stopPropagation()}>Mark as Reviewed</DropdownMenuItem>
                          <DropdownMenuItem 
                            className="text-red-500" 
                            onClick={(e) => {
                              e.stopPropagation();
                              setPostToDelete(post.id);
                              setDeleteTarget("single");
                              setShowDeleteConfirm(true);
                            }}
                          >
                            Delete Entry
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent className="w-[90vw] md:w-full max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm Deletion</AlertDialogTitle>
            <AlertDialogDescription className="text-sm">
              {deleteTarget === "single"
                ? "Are you sure you want to permanently delete this post? This action cannot be undone."
                : deleteTarget === "selected" 
                  ? `Are you sure you want to permanently delete ${selectedIds.size} selected post${selectedIds.size === 1 ? '' : 's'}? This action cannot be undone.`
                  : `Are you sure you want to permanently delete all posts? This action cannot be undone.`
              }
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={confirmDelete}
              className="bg-red-600 hover:bg-red-700 text-white"
              data-testid="button-confirm-delete"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <FlagPostModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        content={selectedPost}
      />
    </div>
  );
}
