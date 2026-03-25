import { useQuery } from "@tanstack/react-query";
import axios from "axios";

interface Filters {
  type?: "post" | "video";
  platform?: string;
  category?: string;
}

interface Source {
  id: number;
  name: string;
  type: string;
  status: string;
  itemsScanned: number;
  lastSync: string;
}

export function useContent(filters?: Filters) {
  return useQuery({
    queryKey: ["content", filters],
    queryFn: async () => {
      const params: any = {};
      if (filters?.type) params.type = filters.type;
      if (filters?.platform && filters.platform !== "All") params.platform = filters.platform;
      if (filters?.category && filters.category !== "All") params.category = filters.category;

      const response = await axios.get("http://localhost:8000/api/post", { params });
      return response.data;
    },
  });
}

export function useScrapedPosts() {
  return useQuery({
    queryKey: ["posts", "scraped"],
    queryFn: async () => {
      const response = await axios.get("http://localhost:8000/api/post/scraped", {
        params: { limit: 50 }
      });
      return response.data.map((post: any) => {
        let platformName = "Twitter/X";
        if (post.category === "facebook") {
          platformName = "Facebook";
        } else if (post.category === "tiktok") {
          platformName = "TikTok";
        } else if (post.category === "website") {
          if (!post.url) platformName = "Website / Blog";
          else if (post.url.includes("dawn.com")) platformName = "Dawn News";
          else if (post.url.includes("timesofindia")) platformName = "Times of India";
          else if (post.url.includes("jihadintel")) platformName = "Jihad Intel";
          else if (post.url.includes("thekhorasandiary")) platformName = "The Khorasan Diary";
          else platformName = "Website / Blog";
        }

        return {
          id: post.post_id,
          platform: platformName,
          category: post.category || "social-media",
          title: post.author || "Unknown",
          content: post.text_content,
          confidenceScore: post.confidence_score || 0,
          status: post.flagged ? "Flagged" : "Safe",
          timestamp: post.timestamp,
          url: post.url,
          media: post.media || [],
          type: "post"
        };
      });
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useSources() {
  return useQuery({
    queryKey: ["sources"],
    queryFn: async () => {
      try {
        // Twitter Stats
        const twitterCountResponse = await axios.get("http://localhost:8000/api/post", {
          params: { category: "twitter", limit: 100 }
        }).catch(() => ({ data: [] }));
        const twitterCount = twitterCountResponse.data.length;

        // Facebook Stats
        const fbCountResponse = await axios.get("http://localhost:8000/api/post", {
          params: { category: "facebook", limit: 100 }
        }).catch(() => ({ data: [] }));
        const fbCount = fbCountResponse.data.length;

        // Website/Blog Stats
        const webCountResponse = await axios.get("http://localhost:8000/api/post", {
          params: { category: "website", limit: 100 }
        }).catch(() => ({ data: [] }));
        const webCount = webCountResponse.data.length;

        // TikTok Stats
        const tiktokCountResponse = await axios.get("http://localhost:8000/api/post", {
          params: { category: "tiktok", limit: 100 }
        }).catch(() => ({ data: [] }));
        const tiktokCount = tiktokCountResponse.data.length;

        const sources: Source[] = [
          {
            id: 1,
            name: "Twitter (X) Scraper",
            type: "Web Scraper",
            status: twitterCount > 0 ? "Running" : "Idle",
            itemsScanned: twitterCount,
            lastSync: new Date().toLocaleTimeString()
          },
          {
            id: 2,
            name: "Facebook Scraper",
            type: "Web Scraper",
            status: fbCount > 0 ? "Running" : "Idle",
            itemsScanned: fbCount,
            lastSync: new Date().toLocaleTimeString()
          },
          {
            id: 3,
            name: "Website / Blog Scraper",
            type: "Web Scraper",
            status: webCount > 0 ? "Running" : "Idle",
            itemsScanned: webCount,
            lastSync: new Date().toLocaleTimeString()
          },
          {
            id: 4,
            name: "TikTok Scraper",
            type: "Video Scraper",
            status: tiktokCount > 0 ? "Running" : "Idle",
            itemsScanned: tiktokCount,
            lastSync: new Date().toLocaleTimeString()
          }
        ];

        return sources;
      } catch (error) {
        return [
          {
            id: 1,
            name: "Twitter (X) Scraper",
            type: "Web Scraper",
            status: "Offline",
            itemsScanned: 0,
            lastSync: "Never"
          },
          {
            id: 2,
            name: "Facebook Scraper",
            type: "Web Scraper",
            status: "Offline",
            itemsScanned: 0,
            lastSync: "Never"
          },
          {
            id: 3,
            name: "Website / Blog Scraper",
            type: "Web Scraper",
            status: "Offline",
            itemsScanned: 0,
            lastSync: "Never"
          },
          {
            id: 4,
            name: "TikTok Scraper",
            type: "Video Scraper",
            status: "Offline",
            itemsScanned: 0,
            lastSync: "Never"
          }
        ];
      }
    },
    refetchInterval: 60000, // Refresh every 60 seconds
  });
}
