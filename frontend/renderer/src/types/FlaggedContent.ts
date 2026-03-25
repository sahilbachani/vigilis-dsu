export type ContentStatus = "Flagged" | "Reviewed" | "Safe";

export interface FlaggedContent {
  /** Primary identifier */
  id: number;

  /** Platform name (Twitter, Facebook, TikTok, etc.) */
  platform: string;

  /** Content category (Hate Speech, Violence, etc.) */
  category: string;

  /** Short title used in tables & cards */
  title: string;
  /** Actual URL to the post/video */
  url?: string;

  /** Full text of the post/video shown in modal */
  content: string;

  /** AI confidence score (0–100) */
  confidenceScore: number;

  /** Moderation status */
  status: ContentStatus;

  /** ISO timestamp */
  timestamp?: string;

  /** Optional thumbnail (videos only) */
  thumbnailUrl?: string;

  /** Content type used by useContent hook */
  type?: "post" | "video" | "image";

  /** Attached Media Files */
  media?: any[];
}
