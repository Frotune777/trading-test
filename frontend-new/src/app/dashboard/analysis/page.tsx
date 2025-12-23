import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function AnalysisPage() {
    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">Market Analysis</h2>
                <p className="text-slate-400 mt-2">In-depth technical and fundamental analysis.</p>
            </div>
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Coming Soon</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-slate-400">The Market Analysis module is currently under development.</p>
                </CardContent>
            </Card>
        </div>
    )
}
