import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import axios from "axios";
import { useToast } from "@/hooks/use-toast";

interface AddSourceModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: () => void;
}

export function AddSourceModal({ open, onOpenChange, onSave }: AddSourceModalProps) {
  const [sourceName, setSourceName] = useState("");
  const [url, setUrl] = useState("");
  const [platform, setPlatform] = useState("website");
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleAdd = async () => {
    if (!sourceName.trim()) {
      toast({
        title: "Validation Error",
        description: "Please enter a source name",
        variant: "destructive",
      });
      return;
    }

    if (platform !== "website" && !url.trim()) {
      toast({
        title: "Validation Error",
        description: "Please enter a URL for this source type",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      await axios.post("http://localhost:8000/api/sources", {
        source_name: sourceName.trim(),
        url: url.trim() || null,
        platform,
      });

      toast({
        title: "Source Added",
        description: `Successfully added source "${sourceName}"`,
      });

      // Reset form
      setSourceName("");
      setUrl("");
      setPlatform("website");
      onOpenChange(false);
      onSave();
    } catch (error: any) {
      console.error("Failed to add source:", error);
      const errorMessage = error.response?.data?.detail || "Failed to add source. Please try again.";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      handleAdd();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add New Data Source</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Source Name <span className="text-red-500">*</span>
            </label>
            <Input
              placeholder="e.g., BBC News, Al Jazeera"
              value={sourceName}
              onChange={(e) => setSourceName(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="bg-background border-border/30"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              Platform <span className="text-red-500">*</span>
            </label>
            <Select value={platform} onValueChange={setPlatform} disabled={isLoading}>
              <SelectTrigger className="bg-background border-border/30">
                <SelectValue placeholder="Select platform" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="website">Website</SelectItem>
                <SelectItem value="twitter">Twitter / X</SelectItem>
                <SelectItem value="facebook">Facebook</SelectItem>
                <SelectItem value="tiktok">TikTok</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">
              URL {platform !== "website" && <span className="text-red-500">*</span>}
            </label>
            <Input
              placeholder={`https://example.com${platform === "twitter" ? "/username" : ""}`}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="bg-background border-border/30"
            />
            <p className="text-xs text-muted-foreground">
              {platform === "website"
                ? "Enter the website URL (optional for manual management)"
                : `Enter the ${platform} profile or page URL`}
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button onClick={handleAdd} disabled={isLoading} className="bg-primary hover:bg-primary/90">
            {isLoading ? "Adding..." : "Add Source"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
