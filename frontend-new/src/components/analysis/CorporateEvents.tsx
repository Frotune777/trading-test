import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Calendar, TrendingUp, Gift, Scissors, DollarSign, FileText } from "lucide-react"
import { cn } from "@/lib/utils"

interface CorporateEvent {
    symbol: string
    eventType: 'Dividend' | 'Bonus' | 'Split' | 'Buyback' | 'Rights Issue' | 'Other'
    subject: string
    exDate: string
    recDate: string
    comp: string
}

const eventConfig = {
    'Dividend': { icon: DollarSign, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
    'Bonus': { icon: Gift, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
    'Split': { icon: Scissors, color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
    'Buyback': { icon: TrendingUp, color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
    'Rights Issue': { icon: FileText, color: 'text-cyan-600 dark:text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
    'Other': { icon: Calendar, color: 'text-muted-foreground', bg: 'bg-muted', border: 'border-border' }
}

export function CorporateEvents({ symbol }: { symbol: string }) {
    const { data, isLoading, isError } = useQuery({
        queryKey: ['corporate-events', symbol],
        queryFn: async () => {
            const res = await api.get(`/stocks/${symbol}/corporate-events`)
            return res.data as { data: CorporateEvent[], count: number, symbol: string }
        },
        retry: 2,
        staleTime: 10 * 60 * 1000, // 10 minutes
    })

    if (isLoading) {
        return (
            <div className="space-y-4">
                {[1, 2, 3].map(i => (
                    <Card key={i} className="bg-muted animate-pulse h-24 border-border" />
                ))}
            </div>
        )
    }

    if (isError) {
        return (
            <Card className="bg-rose-500/5 border-rose-500/20">
                <CardContent className="py-8 text-center text-rose-600 dark:text-rose-400">
                    Error loading corporate events
                </CardContent>
            </Card>
        )
    }

    if (!data?.data || data.data.length === 0) {
        return (
            <Card className="bg-card border-border">
                <CardContent className="py-12 text-center">
                    <Calendar className="h-12 w-12 mx-auto text-muted-foreground/60 mb-4" />
                    <p className="text-muted-foreground">No corporate events found in the last 6 months</p>
                </CardContent>
            </Card>
        )
    }

    // Group events by type
    const groupedEvents = data.data.reduce((acc, event) => {
        if (!acc[event.eventType]) {
            acc[event.eventType] = []
        }
        acc[event.eventType].push(event)
        return acc
    }, {} as Record<string, CorporateEvent[]>)

    return (
        <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
                {Object.entries(groupedEvents).map(([type, events]) => {
                    const config = eventConfig[type as keyof typeof eventConfig]
                    const Icon = config.icon
                    return (
                        <Card key={type} className={cn("bg-card border-border")}>
                            <CardContent className="p-4">
                                <div className="flex items-center gap-2">
                                    <Icon className={cn("h-4 w-4", config.color)} />
                                    <span className="text-xs font-medium text-muted-foreground">{type}</span>
                                </div>
                                <div className="text-2xl font-bold text-foreground mt-2">{events.length}</div>
                            </CardContent>
                        </Card>
                    )
                })}
            </div>

            {/* Timeline View */}
            <Card className="bg-card border-border">
                <CardHeader>
                    <CardTitle className="text-foreground">Recent Corporate Events</CardTitle>
                    <p className="text-sm text-muted-foreground">Last 6 months of corporate actions</p>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {data.data.map((event, i) => {
                            const config = eventConfig[event.eventType]
                            const Icon = config.icon
                            return (
                                <div key={i} className="flex gap-4 items-start pb-4 border-b border-border last:border-0 last:pb-0">
                                    <div className={cn("p-2 rounded-lg", config.bg, config.border, "border")}>
                                        <Icon className={cn("h-5 w-5", config.color)} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <Badge variant="outline" className={cn(config.bg, config.color, config.border, "text-xs")}>
                                                {event.eventType}
                                            </Badge>
                                            <span className="text-xs text-muted-foreground">Ex-Date: {event.exDate}</span>
                                        </div>
                                        <p className="text-sm font-medium text-foreground mb-1">{event.subject}</p>
                                        <p className="text-xs text-muted-foreground">Record Date: {event.recDate}</p>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
