"use client";

import { useState } from "react"; 
import { useContent } from "@/hooks/use-content";
import { 
  Card, 
  CardContent, 
  CardFooter, 
  CardHeader 
} from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Play, Calendar, AlertTriangle, Eye, CheckCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { FlagPostModal } from "@/components/FlagPostModal";
import { FlaggedContent } from "@/types/FlaggedContent";

export default function FlaggedVideos() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedVideo, setSelectedVideo] = useState<FlaggedContent | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
const { data, isLoading } = useContent({ type: 'video' });
const videos = data as FlaggedContent[] | undefined;

  const handleViewVideo = (video: FlaggedContent) => {
    setSelectedVideo(video);
    setIsModalOpen(true);
  };

  // Client-side filtering
  const filteredVideos = videos?.filter((v: FlaggedContent) => 
    v.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col gap-4">
        <div className="w-full">
          <h1 className="text-3xl font-display font-bold tracking-tight text-foreground">Flagged Videos</h1>
          <p className="text-sm text-muted-foreground mt-2 font-medium">Analysis of multimedia content for violations.</p>
        </div>
        <div className="w-full md:w-72">
          <Input 
            placeholder="Search by title..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-background border-border/30 focus-visible:ring-primary/30 text-sm py-2"
          />
        </div>
      </div>

      <div className="grid gap-5 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 8 }).map((_, i) => (
            <Card key={i} className="overflow-hidden">
              <Skeleton className="h-36 w-full" />
              <div className="p-3 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
                <div className="flex gap-2 pt-2">
                  <Skeleton className="h-8 w-full" />
                </div>
              </div>
            </Card>
          ))
        ) : filteredVideos?.length === 0 ? (
          <div className="col-span-full text-center py-12 text-sm text-muted-foreground">
            No videos found matching your search.
          </div>
        ) : (
          filteredVideos?.map((video: FlaggedContent) => (
            <Card 
              key={video.id} 
              className="overflow-hidden group border-border/50 hover:border-primary/50 transition-all duration-300 hover:shadow-lg cursor-pointer flex flex-col"
              onClick={() => handleViewVideo(video)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleViewVideo(video);
                }
              }}
              title="Click to view details"
              data-testid="card-flagged-video"
            >
              <div className="relative aspect-video bg-black/5 dark:bg-black/40 group-hover:opacity-90 transition-opacity">
                <img 
                  src={video.thumbnailUrl || "https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=500&h=300&fit=crop"} 
                  alt={video.content}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-[2px]">
                  <Button 
                    size="icon" 
                    className="rounded-full h-12 w-12 bg-white/20 hover:bg-white/40 backdrop-blur-md border-0 text-white shadow-xl"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleViewVideo(video);
                    }}
                  >
                    <Play className="h-6 w-6 ml-0.5 fill-current" />
                  </Button>
                </div>
                <div className="absolute top-3 right-3">
                  <span className="px-3 py-1.5 rounded bg-black/70 text-white text-xs font-semibold backdrop-blur-sm">
                    {video.platform}
                  </span>
                </div>
              </div>
              
              <CardContent className="p-3 flex-1 flex flex-col">
                <h3 className="font-semibold truncate mb-2 text-xs" title={video.content}>{video.content}</h3>
                <div className="flex flex-wrap items-center text-xs text-muted-foreground mb-3 gap-2">
                  <Calendar className="h-3.5 w-3.5" />
                  <span className="truncate">{new Date(video.timestamp!).toLocaleDateString()}</span>
                  <span className="mx-1">•</span>
                  <span className="text-destructive font-semibold flex items-center">
                    <AlertTriangle className="h-3.5 w-3.5 mr-1" />
                    {video.confidenceScore}%
                  </span>
                </div>
                
                <div className="flex flex-wrap gap-2 mb-4">
                  <StatusBadge status={video.status} />
                  <span className="inline-flex items-center px-2.5 py-1 rounded text-xs font-semibold bg-primary/25 text-primary border border-border">
                    {video.category}
                  </span>
                </div>
              </CardContent>
              
              <CardFooter className="p-3 pt-0 flex gap-2">
                <Button 
                  variant="secondary" 
                  size="sm" 
                  className="w-full text-sm font-medium flex items-center justify-center"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewVideo(video);
                  }}
                  data-testid="button-review-video"
                >
                  <Eye className="h-4 w-4 mr-1.5" /> Review
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full text-sm font-medium hover:bg-green-500/10 hover:text-green-600 hover:border-green-500/20 flex items-center justify-center"
                  onClick={(e) => e.stopPropagation()}
                >
                  <CheckCircle className="h-3 w-3 mr-1" /> Clear
                </Button>
              </CardFooter>
            </Card>
          ))
        )}
      </div>

      <FlagPostModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        content={selectedVideo}
      />
    </div>
  );
}
