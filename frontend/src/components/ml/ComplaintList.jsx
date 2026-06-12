export default function ComplaintList({
    complaints = [],
    categoryName = '',
    examples = [],
    loading = false,
    error = null
}) {
    if (loading) {
        return (
            <div className="rounded-xl border border-gray-200 bg-white p-6">
                <div className="mb-4 h-6 w-1/2 animate-pulse rounded bg-gray-200" />
                <div className="space-y-3">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="flex items-center gap-3">
                            <div className="h-6 w-6 animate-pulse rounded-full bg-gray-200" />
                            <div className="h-4 flex-1 animate-pulse rounded bg-gray-200" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-xl border border-red-200 bg-red-50 p-6">
                <h3 className="mb-2 font-semibold text-red-800">Unable to Load Complaints</h3>
                <p className="text-sm text-red-600">{error}</p>
            </div>
        );
    }

    if (!complaints || complaints.length === 0) {
        return (
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-6 text-center">
                <p className="text-sm text-gray-500">No negative or neutral review themes found for this category.</p>
            </div>
        );
    }

    const getSeverityStyle = (index, total) => {
        const severity = 1 - (index / Math.max(total, 1));
        if (severity > 0.7) return { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-200' };
        if (severity > 0.4) return { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-200' };
        return { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-200' };
    };

    return (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
            <div className="border-b border-gray-100 bg-gradient-to-r from-red-50 to-orange-50 px-6 py-4">
                <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 text-sm font-bold text-red-700">!</span>
                    <div>
                        <h3 className="font-semibold text-gray-900">Top Complaint Themes</h3>
                        {categoryName && <p className="text-sm text-gray-500">In {categoryName}</p>}
                    </div>
                </div>
            </div>

            <div className="divide-y divide-gray-100">
                {complaints.map((complaint, index) => {
                    const style = getSeverityStyle(index, complaints.length);
                    const label = complaint.text || complaint.complaint || complaint.issue || complaint.keyword || complaint.phrase;
                    const score = Number(complaint.tfidf_score ?? complaint.score ?? 0);

                    return (
                        <div key={complaint.id || `${label}-${index}`} className="px-6 py-4 transition-colors hover:bg-gray-50">
                            <div className="flex items-start gap-4">
                                <div className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border text-sm font-bold ${style.bg} ${style.text} ${style.border}`}>
                                    {index + 1}
                                </div>

                                <div className="min-w-0 flex-1">
                                    <p className="font-medium text-gray-900">{label}</p>
                                    <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500">
                                        {complaint.count && <span>{complaint.count} mentions</span>}
                                        {score > 0 && <span>Signal score: {(score * 100).toFixed(1)}</span>}
                                        {complaint.sentiment && <span>{complaint.sentiment}</span>}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {examples.length > 0 && (
                <div className="border-t bg-gray-50 px-6 py-4">
                    <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Sample negative reviews</p>
                    <div className="space-y-2">
                        {examples.slice(0, 3).map((example, index) => (
                            <p key={index} className="rounded-lg bg-white p-3 text-sm text-gray-600">
                                {example.review_text || example.text || example.clean_text}
                            </p>
                        ))}
                    </div>
                </div>
            )}

            <div className="bg-gray-50 px-6 py-3 text-xs text-gray-500">
                Analysis is extracted from negative and neutral review text using TF-IDF.
            </div>
        </div>
    );
}
