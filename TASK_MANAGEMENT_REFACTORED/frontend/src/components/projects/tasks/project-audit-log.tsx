"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Badge } from "@/platform/v1/components";
import { Skeleton } from "@/platform/v1/components";
import { ChevronDown, ChevronUp, Clock, ArrowRight } from "lucide-react";
import { cn, showErrorToast } from "@/lib/utils";
import { CONTENT_TYPES, type IAuditProjectLogs } from "@/types/project.type";
import { AUDIT_LOG_API } from "@/lib/utils.chats";
import { useInView } from "react-intersection-observer";

interface ProjectAuditTrailProps {
  projectId: number;
  className?: string;
}

export function ProjectAuditTrail({
  projectId,
  className,
}: ProjectAuditTrailProps) {
  const [logs, setProjectLogs] = useState<IAuditProjectLogs[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [expandedLogs, setExpandedLogs] = useState<Set<number>>(new Set());
  const { ref, inView } = useInView({ threshold: 0 });
  const logsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const fetchAuditProjectLogs = useCallback(async () => {
    if (!projectId) return;

    setLoading(true);
    try {
      const res = await AUDIT_LOG_API.getPaginatedProjectAuditLogs({
        project_id: projectId,
        page: 1,
        object_id: projectId,
        content_type: CONTENT_TYPES.PROJECT,
      });

      setProjectLogs(res.results.reverse());
      setNextUrl(res.next);
      setHasMore(!!res.next);

      setTimeout(scrollToBottom, 100);
    } catch (error) {
      showErrorToast({ error, defaultMessage: "Failed to fetch project logs" });
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [projectId, scrollToBottom]);

  const fetchNextPage = useCallback(async () => {
    if (!nextUrl || loading) return;

    setLoading(true);
    try {
      const res = await AUDIT_LOG_API.getAuditProjectLogsFromUrl({
        url: nextUrl,
      });

      setProjectLogs((prev) => [...res.results.reverse(), ...prev]);
      setNextUrl(res.next);
      setHasMore(!!res.next);
    } catch (error) {
      showErrorToast({
        error,
        defaultMessage: "Failed to load more project logs",
      });
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [nextUrl, loading]);

  useEffect(() => {
    fetchAuditProjectLogs();
  }, [fetchAuditProjectLogs]);

  useEffect(() => {
    if (inView && hasMore && !loading) {
      fetchNextPage();
    }
  }, [inView, hasMore, loading, fetchNextPage]);

  const toggleExpand = (logId: number) => {
    setExpandedLogs((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(logId)) {
        newSet.delete(logId);
      } else {
        newSet.add(logId);
      }
      return newSet;
    });
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
  };

  const getActionColor = (action: string) => {
    switch (action.toUpperCase()) {
      case "CREATE":
        return "bg-cyan-500/10 text-cyan-600 hover:bg-cyan-500/20";
      case "UPDATE":
        return "bg-cyan-500/10 text-cyan-600 hover:bg-cyan-500/20";
      case "DELETE":
        return "bg-rose-500/10 text-rose-600 hover:bg-rose-500/20";
      default:
        return "bg-gray-500/10 text-gray-600 hover:bg-gray-500/20";
    }
  };

  const getDotColor = (action: string) => {
    return "bg-gray-400";
  };

  const parseChanges = (changes: any) => {
    if (!changes) return null;
    if (typeof changes === "string") {
      try {
        return JSON.parse(changes);
      } catch {
        return null;
      }
    }
    return changes;
  };

  if (loading && logs.length === 0) {
    return (
      <div
        className={cn(
          "space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto",
          className
        )}
      >
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3">
            <Skeleton className="h-3 w-3 rounded-full flex-shrink-0 mt-1" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("p-8 text-center", className)}>
        <p className="text-sm font-medium text-gray-900">
          Failed to load audit logs
        </p>
        <p className="text-xs text-gray-500 mt-1">{error}</p>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className={cn("p-8 text-center", className)}>
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gray-50 mb-3">
          <Clock className="h-5 w-5 text-gray-400" />
        </div>
        <p className="text-sm font-medium text-gray-900">No activity yet</p>
        <p className="text-xs text-gray-500 mt-1">
          Changes to this project will appear here
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "max-h-[calc(100vh-200px)] overflow-y-auto space-y-6 pr-4 bg-white rounded-xl border border-gray-200",
        className
      )}
    >
      {logs.map((log, index) => {
        const isExpanded = expandedLogs.has(log.id);
        const changes = parseChanges(log.changes);
        const hasChanges = changes && Object.keys(changes).length > 0;
        const isLastItem = index === logs.length - 1;

        return (
          <div
            key={log.id}
            className="relative space-y-3 ml-4 sm:ml-8 mt-6 sm:mt-10"
          >
            {!isLastItem && (
              <div className="absolute left-[5px] top-6 bottom-0 w-px bg-gray-300" />
            )}

            {/* Header Section */}
            <div className="flex items-start gap-3 relative">
              <div className="flex-shrink-0 mt-1 relative z-10">
                <div
                  className={cn(
                    "h-3 w-3 rounded-full",
                    getDotColor(log.action)
                  )}
                />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    className={cn(
                      "text-[10px] sm:text-xs font-medium px-2 py-0.5 rounded",
                      getActionColor(log.action)
                    )}
                  >
                    {log.action.charAt(0).toUpperCase() +
                      log.action.slice(1).toLowerCase()}
                  </Badge>
                  <span className="text-xs sm:text-sm text-gray-600 break-words">
                    By {log.user.name}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-1 mt-1 text-[10px] sm:text-xs text-gray-500">
                  <span>{formatTimestamp(log.timestamp)}</span>
                  <span>•</span>
                  <span>{formatTime(log.timestamp)}</span>
                </div>
              </div>
            </div>

            {/* Expandable Section */}
            {hasChanges && (
              <div className="ml-4 sm:ml-6 bg-[#F4F4F9] p-2 sm:p-3 rounded-2xl">
                <button
                  onClick={() => toggleExpand(log.id)}
                  className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 mb-2 pt-2 sm:pt-3 pl-1 pb-2 sm:pb-3"
                >
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                  <span>Details</span>
                </button>

                {isExpanded && (
                  <div className="p-2 sm:p-3 space-y-4 -mt-2 sm:-mt-3">
                    {/* Description */}
                    <div className="space-y-2">
                      <div className="text-xs sm:text-sm font-medium text-gray-500">
                        Description
                      </div>
                      <div className="text-sm text-gray-900 rounded-md break-words">
                        {log.description || (
                          <span className="text-gray-400 italic">
                            No description
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Changes Section */}
                    {Object.entries(changes).map(
                      ([field, change]: [string, any]) => (
                        <div key={field} className="space-y-2">
                          <div className="text-xs sm:text-sm font-medium text-gray-700">
                            {field.replace(/_/g, " ").charAt(0).toUpperCase() +
                              field.replace(/_/g, " ").slice(1)}
                            :
                          </div>

                          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
                            {/* Old Value */}
                            <div className="w-full sm:w-1/2">
                              <div className="text-xs text-gray-500 mb-1">
                                Previous:
                              </div>
                              <div className="text-sm text-gray-900 p-2 rounded-md break-words">
                                {change.old !== null &&
                                change.old !== undefined ? (
                                  String(change.old)
                                ) : (
                                  <span className="text-gray-400 italic">
                                    Empty
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Arrow */}
                            <div className="flex items-center justify-center sm:justify-start w-full sm:w-auto">
                              <div className="h-px w-8 sm:w-16 bg-[#848496] rounded-full" />
                              <ArrowRight className="h-4 w-4 text-[#848496] -ml-1" />
                            </div>

                            {/* New Value */}
                            <div className="w-full sm:w-1/2">
                              <div className="text-xs text-gray-500 mb-1">
                                Current:
                              </div>
                              <div className="text-sm font-medium text-gray-900 p-2 rounded-md break-words">
                                {change.new !== null &&
                                change.new !== undefined ? (
                                  String(change.new)
                                ) : (
                                  <span className="text-gray-400 italic">
                                    Empty
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {hasMore && (
        <div ref={ref} className="flex justify-center pt-4">
          {loading && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900" />
              Loading more entries...
            </div>
          )}
        </div>
      )}
      <div ref={logsEndRef} />
    </div>
  );
}
