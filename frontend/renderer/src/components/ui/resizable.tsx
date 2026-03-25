"use client";

import { GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

// Panel Group wrapper - simplified
interface ResizablePanelGroupProps {
  children: React.ReactNode;
  direction?: "horizontal" | "vertical";
  className?: string;
}

export const ResizablePanelGroup: React.FC<ResizablePanelGroupProps> = ({
  children,
  direction = "horizontal",
  className,
}) => {
  return (
    <div className={cn("flex h-full w-full", direction === "vertical" ? "flex-col" : "flex-row", className)}>
      {children}
    </div>
  );
};

// Panel wrapper - simplified
interface ResizablePanelProps {
  children: React.ReactNode;
  className?: string;
}

export const ResizablePanel: React.FC<ResizablePanelProps> = ({ children, className }) => (
  <div className={className}>{children}</div>
);

// Handle wrapper - simplified
interface ResizableHandleProps {
  className?: string;
  withGrip?: boolean;
}

export const ResizableHandle: React.FC<ResizableHandleProps> = ({ className, withGrip = false }) => {
  return (
    <div
      className={cn(
        "bg-border flex items-center justify-center hover:bg-primary/20 transition-colors cursor-col-resize",
        withGrip ? "h-4 w-3" : "w-px",
        className
      )}
    >
      {withGrip && <GripVertical className="h-2.5 w-2.5" />}
    </div>
  );
};
