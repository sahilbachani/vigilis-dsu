import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";

export default function Settings() {
  const { toast } = useToast();

  const handleSave = () => {
    toast({
      title: "Settings Saved",
      description: "Your system preferences have been updated.",
    });
  };

  return (
    <div className="w-full space-y-6">
      <div>
        <h1 className="text-3xl font-display font-bold tracking-tight text-foreground">
          System Settings
        </h1>
        <p className="text-sm text-muted-foreground mt-2 font-medium">
          Configure monitoring engine behavior and preferences
        </p>
      </div>

      <div className="grid gap-6 w-full">
        <Card className="border-border/40 shadow-sm bg-gradient-to-br from-card to-card/95">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Analysis Thresholds</CardTitle>
            <CardDescription className="text-sm">Configure sensitivity for AI detection models.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
              <div className="space-y-2.5">
                <Label htmlFor="confidence" className="text-sm font-semibold">Minimum Confidence Score (%)</Label>
                <Input id="confidence" type="number" defaultValue={75} min={0} max={100} className="text-sm bg-background border-border/50 focus-visible:ring-primary/50 transition-all py-2.5" />
                <p className="text-xs text-muted-foreground font-medium">Alerts below this score will be auto-archived.</p>
              </div>
              <div className="space-y-2.5">
                <Label htmlFor="batch" className="text-sm font-semibold">Processing Batch Size</Label>
                <Input id="batch" type="number" defaultValue={50} className="text-sm bg-background border-border/50 focus-visible:ring-primary/50 transition-all py-2.5" />
                <p className="text-xs text-muted-foreground font-medium">Items processed per analysis cycle.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/40 shadow-sm bg-gradient-to-br from-card to-card/95">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Notifications & Automation</CardTitle>
            <CardDescription className="text-sm">Control how the system responds to detected threats.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 rounded-md border border-border/30 bg-background/40 hover:bg-background/50 transition-colors">
              <div className="space-y-1">
                <Label className="text-base font-semibold text-foreground">Auto-Flag High Risk Content</Label>
                <p className="text-sm text-muted-foreground">Automatically flag items with &gt;95% confidence score.</p>
              </div>
              <Switch defaultChecked className="flex-shrink-0" />
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 rounded-md border border-border/30 bg-background/40 hover:bg-background/50 transition-colors">
              <div className="space-y-1">
                <Label className="text-base font-semibold text-foreground">System Sound Alerts</Label>
                <p className="text-sm text-muted-foreground">Play a sound when critical threats are detected.</p>
              </div>
              <Switch defaultChecked className="flex-shrink-0" />
            </div>
          </CardContent>
        </Card>

        <div className="flex flex-col sm:flex-row gap-3 justify-end pt-4">
          <Button variant="outline" className="text-sm font-medium order-2 sm:order-1 border-border/50">Reset Defaults</Button>
          <Button onClick={handleSave} className="text-sm font-medium order-1 sm:order-2 bg-gradient-to-r from-primary to-primary/90 hover:from-primary/90 hover:to-primary shadow-lg hover:shadow-xl">Save Changes</Button>
        </div>
      </div>
    </div>
  );
}
