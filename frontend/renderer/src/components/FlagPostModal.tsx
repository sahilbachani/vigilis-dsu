import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, X, AlertTriangle, CheckCircle, AlertCircle, Share2 } from "lucide-react";
import { FlaggedContent } from "@/types/FlaggedContent";


interface FlagPostModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  content: FlaggedContent | null;
}

const getPlatformIcon = (platform: string) => {
  switch (platform.toLowerCase()) {
    case 'twitter':
    case 'twitter/x':
      return <span className="inline-flex items-center justify-center h-5 w-5 bg-black dark:bg-white text-white dark:text-black rounded-sm text-xs font-bold">𝕏</span>;
    case 'facebook':
      return <span className="inline-flex items-center justify-center h-5 w-5 bg-blue-600 text-white rounded-sm text-xs font-bold">f</span>;
    case 'tiktok':
      return <span className="inline-flex items-center justify-center h-5 w-5 bg-black text-white rounded-sm text-xs font-bold">t</span>;
    default:
      return <Share2 className="h-5 w-5" />;
  }
};

const getConfidenceColor = (score: number): string => {
  if (score >= 90) return "bg-red-100 dark:bg-red-950 text-red-800 dark:text-red-200 border-red-300 dark:border-red-700";
  if (score >= 75) return "bg-orange-100 dark:bg-orange-950 text-orange-800 dark:text-orange-200 border-orange-300 dark:border-orange-700";
  return "bg-green-100 dark:bg-green-950 text-green-800 dark:text-green-200 border-green-300 dark:border-green-700";
};

const getConfidenceIcon = (score: number) => {
  if (score >= 90) return <AlertTriangle className="h-4 w-4" />;
  if (score >= 75) return <AlertCircle className="h-4 w-4" />;
  return <CheckCircle className="h-4 w-4" />;
};

export function FlagPostModal({ open, onOpenChange, content }: FlagPostModalProps) {
  if (!content) return null;

  const websiteUrl = content.url || "#";
  const formattedDate = new Date(content.timestamp || '').toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const author = content.title;
  const confidenceColor = getConfidenceColor(content.confidenceScore);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Flagged Post Details</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Platform Section - Prominent Display */}
          <div className="bg-gradient-to-br from-primary/10 to-primary/5 dark:from-primary/20 dark:to-primary/10 rounded-xl p-4 border border-primary/20 flex items-center gap-4">
            <div className="text-primary">
              {getPlatformIcon(content.platform)}
            </div>
            <div className="flex-1">
              <p className="text-sm text-muted-foreground font-medium">Platform</p>
              <p className="text-xl font-bold text-foreground">{content.platform}</p>
            </div>
            <Badge variant="outline" className="text-xs font-medium">
              {content.category}
            </Badge>
          </div>

          {/* Author Section */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Posted By</p>
            <p className="text-base font-semibold text-foreground">@{author}</p>
          </div>

          {/* Attached Media Section */}
          {content.media && content.media.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Attached Media</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {content.media.map((mediaItem: any, idx: number) => {
                  if (mediaItem.media_type === "image" && mediaItem.local_path) {
                    return (
                      <div key={idx} className="relative aspect-square rounded-md overflow-hidden bg-black/5 border border-border/50">
                        <img 
                          src={`http://localhost:8000${mediaItem.local_path}`} 
                          alt="Attached media"
                          className="object-cover w-full h-full cursor-pointer hover:scale-105 transition-transform"
                          onClick={() => window.open(`http://localhost:8000${mediaItem.local_path}`, '_blank')}
                        />
                      </div>
                    );
                  } else if (mediaItem.media_type === "video" && mediaItem.local_path) {
                    return (
                      <div key={idx} className="relative aspect-video rounded-md overflow-hidden bg-black/5 border border-border/50 col-span-2 md:col-span-3">
                        <video 
                          src={`http://localhost:8000${mediaItem.local_path}`} 
                          controls
                          className="w-full h-full object-contain bg-black"
                        />
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            </div>
          )}

          {/* Post Content Section */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Post Content</p>
            <div className="bg-muted/50 dark:bg-muted/30 rounded-lg p-4 border border-border/50">
              <p className="text-base leading-relaxed text-foreground whitespace-pre-wrap break-words">
                {content.content}
              </p>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-4">
            {/* Posted Time */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Posted</p>
              <p className="text-sm text-foreground font-medium">{formattedDate}</p>
            </div>

            {/* Confidence Score - Enhanced Badge */}
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Confidence Score</p>
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg font-bold border ${confidenceColor}`}>
                {getConfidenceIcon(content.confidenceScore)}
                <span>{content.confidenceScore}%</span>
              </div>
            </div>
          </div>

          {/* Status Badge */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Status</p>
            <Badge
              variant={content.status === 'Flagged' ? 'destructive' : content.status === 'Reviewed' ? 'default' : 'secondary'}
              className="w-fit"
            >
              {content.status}
            </Badge>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-border/50">
            <Button
              variant="default"
              className="flex-1"
              disabled={websiteUrl === "#"}
              onClick={() => {
                if (websiteUrl !== "#") window.open(websiteUrl, '_blank')
              }}
              data-testid="button-view-website"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View on {content.platform}
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => onOpenChange(false)}
              data-testid="button-close-modal"
            >
              <X className="h-4 w-4 mr-2" />
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
