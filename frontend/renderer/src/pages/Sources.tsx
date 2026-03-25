import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Database, RefreshCw, Trash2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/StatusBadge";
import { useSources } from "@/hooks/use-content";
import { Skeleton } from "@/components/ui/skeleton";

export default function Sources() {
  const { data: sources, isLoading, refetch } = useSources();

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
        <Button className="text-xs font-semibold bg-primary hover:bg-primary/90 shadow-md py-2 h-auto">
          <Plus className="mr-2 h-4 w-4" /> Add Source
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
                  <TableHead className="min-w-[200px] md:min-w-auto font-medium text-xs">Source Name</TableHead>
                  <TableHead className="min-w-[90px] md:min-w-auto font-medium text-xs">Type</TableHead>
                  <TableHead className="min-w-[80px] md:min-w-auto font-medium text-xs">Status</TableHead>
                  <TableHead className="text-right min-w-[100px] md:min-w-auto font-medium text-xs">Items Scanned</TableHead>
                  <TableHead className="text-right min-w-[90px] md:min-w-auto font-medium text-xs">Last Sync</TableHead>
                  <TableHead className="w-[60px] md:w-[100px] font-medium text-xs">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources && sources.length > 0 ? (
                  sources.map((source) => (
                    <TableRow key={source.id} className="hover:bg-muted/60 transition-colors py-3.5">
                      <TableCell className="font-medium py-3">
                        <div className="flex items-center gap-2">
                          <div className="p-1.5 bg-primary/20 rounded-md">
                            <Database className="h-4 w-4 text-primary flex-shrink-0" />
                          </div>
                          <span className="truncate font-semibold text-sm">{source.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="py-3">
                        <span className="px-2.5 py-1 text-xs font-medium bg-primary/20 text-primary rounded-sm">{source.type}</span>
                      </TableCell>
                      <TableCell className="py-3">
                        <StatusBadge status={source.status === "Error" ? "Busy" : source.status} />
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm font-medium py-3">{source.itemsScanned.toLocaleString()}</TableCell>
                      <TableCell className="text-right text-muted-foreground text-sm py-3">{source.lastSync}</TableCell>
                      <TableCell className="py-3">
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-all rounded" onClick={() => refetch()}>
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-all rounded">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground py-12">
                      <p className="font-medium">No data sources available</p>
                      <p className="text-xs mt-1">Add a source to get started monitoring content</p>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
