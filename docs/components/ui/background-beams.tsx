"use client";
import React from "react";
import { cn } from "@/lib/utils";

export const BackgroundBeams = ({ className }: { className?: string }) => {
  return (
    <div
      className={cn(
        "absolute h-full w-full inset-0 overflow-hidden",
        className
      )}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-orange-50/50 via-transparent to-amber-50/50 dark:from-orange-950/20 dark:via-transparent dark:to-amber-950/20" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(249,115,22,0.1),transparent_50%)] dark:bg-[radial-gradient(circle_at_50%_120%,rgba(249,115,22,0.05),transparent_50%)]" />
    </div>
  );
};
