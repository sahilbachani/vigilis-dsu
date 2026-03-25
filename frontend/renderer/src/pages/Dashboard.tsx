import { useState } from "react";
import { useDashboardStats, useSystemStatus } from "@/hooks/use-dashboard";
import { useScrapedPosts } from "@/hooks/use-content";
import { useLogout } from "@/hooks/use-auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { ScrapeModal } from "@/components/ScrapeModal";
import {
  Activity,
  AlertTriangle,
  FileText,
  TrendingUp,
  Server,
  ArrowUpRight,
  LogOut,
  Download
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import { FlaggedContent } from "@/types/FlaggedContent";

// Mock chart data
const chartData = [
  { name: "Mon", flagged: 12 },
  { name: "Tue", flagged: 19 },
  { name: "Wed", flagged: 15 },
  { name: "Thu", flagged: 22 },
  { name: "Fri", flagged: 28 },
  { name: "Sat", flagged: 14 },
  { name: "Sun", flagged: 18 },
];

// Typed props for StatCard
interface StatCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  trend?: string;
}

function StatCard({ title, value, icon: Icon, description, trend }: StatCardProps) {
  return (
    <Card className="overflow-hidden border-border/50 shadow-sm hover:shadow-md transition-all duration-300 group h-full">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{title}</p>
          </div>
          <div className="p-2 bg-primary/15 rounded-lg group-hover:bg-primary/25 transition-colors flex-shrink-0">
            <Icon className="h-5 w-5 text-primary" />
          </div>
        </div>
        
        <div className="mb-2">
          <div className="flex items-baseline gap-2">
            <h2 className="text-4xl font-bold tracking-tight text-foreground">{value}</h2>
            {trend && (
              <span className="text-xs font-semibold text-green-600 dark:text-green-400 flex items-center gap-0.5 px-1.5 py-0.5 bg-green-100/30 dark:bg-green-900/30 rounded">
                <ArrowUpRight className="h-3.5 w-3.5" /> {trend}
              </span>
            )}
          </div>
        </div>
        
        <p className="text-xs text-muted-foreground font-medium">{description}</p>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [scrapeModalOpen, setScrapeModalOpen] = useState(false);
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: status, isLoading: statusLoading } = useSystemStatus();
  const { data: scrapedPosts, isLoading: postsLoading } = useScrapedPosts();
  const logout = useLogout();

  const recentItems = scrapedPosts?.slice(0, 5) || [];

  if (statsLoading || statusLoading || postsLoading) {
    return (
      <div className="space-y-4 md:space-y-8">
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 md:h-32 rounded-xl" />
          ))}
        </div>
        <div className="grid gap-4 md:gap-6 grid-cols-1 lg:grid-cols-7">
          <Skeleton className="lg:col-span-4 h-[250px] sm:h-[300px] rounded-xl" />
          <Skeleton className="lg:col-span-3 h-[250px] sm:h-[300px] rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-display font-bold tracking-tight text-foreground">Dashboard Overview</h2>
          <p className="text-sm text-muted-foreground mt-2">Real-time monitoring system status and analytics.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={() => setScrapeModalOpen(true)}
            className="font-semibold shadow-md"
            data-testid="button-scrape-data"
          >
            <Download className="h-4 w-4 mr-2" />
            Scrape Data
          </Button>
          <div className="flex items-center gap-3 bg-card px-4 py-2 rounded-lg border border-border/50 shadow-sm whitespace-nowrap">
            <div className="flex items-center gap-2">
              <Server className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-foreground">System:</span>
            </div>
            <StatusBadge status={status?.status || "Unknown"} />
            <span className="text-xs text-muted-foreground border-l pl-3 border-border/50">
              {(() => {
                const date = status?.lastUpdated ? new Date(status.lastUpdated) : new Date();
                return isNaN(date.getTime()) ? new Date().toLocaleTimeString() : date.toLocaleTimeString();
              })()}
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Total Sources"
          value={stats?.totalSources || 0}
          icon={Activity}
          description="Active monitoring channels"
          trend="+12%"
        />
        <StatCard
          title="Total Flagged"
          value={stats?.totalFlagged || 0}
          icon={AlertTriangle}
          description="Content requiring review"
          trend="+5%"
        />
        <StatCard
          title="Posts Flagged"
          value={stats?.postsFlagged || 0}
          icon={FileText}
          description="Text-based content"
        />
      </div>

      <div className="grid gap-6 md:grid-cols-7">
        <Card className="col-span-4 border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Flagged Content Trend
            </CardTitle>
          </CardHeader>
          <CardContent className="pl-0">
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorFlagged" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false}/>
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} width={35}/>
                  <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: 8, boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} itemStyle={{ color: 'hsl(var(--foreground))' }} />
                  <Area type="monotone" dataKey="flagged" stroke="hsl(var(--primary))" strokeWidth={2.5} fillOpacity={1} fill="url(#colorFlagged)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3 border-border/50 shadow-sm flex flex-col">
          <CardHeader>
            <CardTitle className="text-lg">Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Platform</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead className="text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentItems.map((item: FlaggedContent) => (
                  <TableRow key={item.id} className="hover:bg-muted/50 transition-colors">
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-secondary px-2 py-0.5 rounded text-secondary-foreground">{item.platform}</span>
                        <span className="text-xs text-muted-foreground truncate max-w-[100px]">{item.category}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 bg-secondary rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary rounded-full" 
                            style={{ width: `${item.confidenceScore}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono">{item.confidenceScore}%</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <StatusBadge status={item.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <ScrapeModal
        open={scrapeModalOpen}
        onOpenChange={setScrapeModalOpen}
      />
    </div>
  );
}
