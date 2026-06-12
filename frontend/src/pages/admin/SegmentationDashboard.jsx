import { useEffect, useMemo, useState } from 'react';
import { useSegmentation } from '../../hooks/useSegmentation';
import { SegmentPieChart, SegmentBarChart } from '../../components/charts';
import { SkeletonLoader } from '../../components/ml';
import { segmentationAPI } from '../../api/segmentationAPI';
import { formatPrice } from '../../utils/price';

const segmentAction = (segment) => {
    const name = String(segment.name || segment.segment_label || segment.segment_name || '').toLowerCase();
    const recency = Number(segment.avg_recency || segment.recency_days || 0);
    const monetary = Number(segment.avg_monetary || segment.monetary || 0);
    const frequency = Number(segment.avg_frequency || segment.frequency || 0);

    if (name.includes('high') || name.includes('loyal') || monetary > 25000 || frequency > 8) {
        return {
            priority: 'Protect',
            action: 'Offer early access, premium bundles, and loyalty multipliers.',
            tone: 'bg-green-50 text-green-700 border-green-200'
        };
    }
    if (name.includes('dormant') || name.includes('inactive') || recency > 60) {
        return {
            priority: 'Recover',
            action: 'Send win-back discounts and show personalized best sellers.',
            tone: 'bg-red-50 text-red-700 border-red-200'
        };
    }
    if (name.includes('steady') || frequency >= 3) {
        return {
            priority: 'Grow',
            action: 'Cross-sell adjacent categories and recommend repeat-purchase staples.',
            tone: 'bg-blue-50 text-blue-700 border-blue-200'
        };
    }
    return {
        priority: 'Nurture',
        action: 'Use onboarding recommendations and category preference prompts.',
        tone: 'bg-amber-50 text-amber-700 border-amber-200'
    };
};

export default function SegmentationDashboard() {
    const { overview, profiles, definitions, loading, error, fetchAll } = useSegmentation();
    const [selectedSegment, setSelectedSegment] = useState(null);
    const [customers, setCustomers] = useState([]);
    const [customersLoading, setCustomersLoading] = useState(false);

    useEffect(() => {
        fetchAll();
    }, [fetchAll]);

    const segments = useMemo(() => {
        const overviewSegments = overview?.segments || [];
        const profileMap = new Map((profiles || []).map(profile => [String(profile.segment_id ?? profile.segment), profile]));
        const definitionMap = new Map((definitions || []).map(def => [String(def.segment_id), def]));
        const total = overviewSegments.reduce((sum, segment) => sum + Number(segment.count || segment.customer_count || 0), 0);

        return overviewSegments.map(segment => {
            const id = String(segment.segment_id ?? segment.id ?? segment.segment);
            const profile = profileMap.get(id) || {};
            const definition = definitionMap.get(id) || {};
            const count = Number(segment.count || segment.customer_count || 0);
            const merged = {
                ...definition,
                ...profile,
                ...segment,
                segment_id: Number(id),
                name: definition.name || profile.segment_name || segment.segment_label || `Segment ${id}`,
                count,
                pct: total ? (count / total) * 100 : 0,
                avg_recency: Number(profile.avg_recency ?? profile.recency_days ?? 0),
                avg_frequency: Number(profile.avg_frequency ?? profile.frequency ?? 0),
                avg_monetary: Number(profile.avg_monetary ?? profile.monetary ?? 0),
                conversion: Number(profile.conversion ?? 0)
            };
            return { ...merged, playbook: segmentAction(merged) };
        }).sort((a, b) => b.count - a.count);
    }, [overview, profiles, definitions]);

    const summary = useMemo(() => {
        const totalCustomers = segments.reduce((sum, segment) => sum + segment.count, 0);
        const largest = segments[0];
        const recovery = segments.find(segment => segment.playbook.priority === 'Recover');
        const highValue = segments.find(segment => segment.playbook.priority === 'Protect');
        return { totalCustomers, largest, recovery, highValue };
    }, [segments]);

    useEffect(() => {
        if (!selectedSegment) return;

        const fetchCustomers = async () => {
            setCustomersLoading(true);
            try {
                const response = await segmentationAPI.getCustomersBySegment(selectedSegment.segment_id, 50);
                setCustomers(response.data?.customers || response.data || []);
            } catch (err) {
                console.error('Error fetching customers:', err);
                setCustomers([]);
            } finally {
                setCustomersLoading(false);
            }
        };

        fetchCustomers();
    }, [selectedSegment]);

    return (
        <div className="space-y-6">
            <div className="rounded-2xl border bg-white p-6 shadow-sm">
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--clr-primary-dark)]">Customer Intelligence</p>
                <h1 className="mt-2 text-2xl font-semibold text-gray-950">Customer Segmentation</h1>
                <p className="mt-2 max-w-3xl text-sm text-gray-500">
                    Convert RFM and behavior clusters into retention, growth, and recovery actions.
                </p>
            </div>

            {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
                    {error}
                    <button onClick={fetchAll} className="ml-4 underline">Retry</button>
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-4">
                <Metric label="Customers segmented" value={summary.totalCustomers.toLocaleString()} />
                <Metric label="Active segments" value={segments.length} />
                <Metric label="Largest segment" value={summary.largest?.name || "-"} compact />
                <Metric label="Recovery pool" value={summary.recovery ? `${summary.recovery.count.toLocaleString()} customers` : "-"} compact />
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <SegmentPieChart segments={segments} title="Segment Distribution" loading={loading} />
                <SegmentBarChart segments={segments} title="Segment Sizes" loading={loading} horizontal />
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h2 className="text-lg font-semibold text-gray-900">Action Playbook</h2>
                        <p className="text-sm text-gray-500">Click a segment to inspect customers and campaign targets.</p>
                    </div>
                    {summary.highValue && (
                        <span className="rounded-full bg-green-50 px-3 py-1 text-sm font-medium text-green-700">
                            Highest value: {summary.highValue.name}
                        </span>
                    )}
                </div>

                {loading ? (
                    <SkeletonLoader variant="table" />
                ) : segments.length ? (
                    <div className="grid gap-4 xl:grid-cols-2">
                        {segments.map(segment => (
                            <button
                                key={segment.segment_id}
                                onClick={() => setSelectedSegment(segment)}
                                className="rounded-xl border bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <p className="text-lg font-semibold text-gray-950">{segment.name}</p>
                                        <p className="mt-1 text-sm text-gray-500">{segment.description || segment.segment_description}</p>
                                    </div>
                                    <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${segment.playbook.tone}`}>
                                        {segment.playbook.priority}
                                    </span>
                                </div>
                                <div className="mt-4 grid grid-cols-4 gap-3 text-sm">
                                    <SmallStat label="Customers" value={segment.count.toLocaleString()} />
                                    <SmallStat label="Share" value={`${segment.pct.toFixed(1)}%`} />
                                    <SmallStat label="Frequency" value={segment.avg_frequency.toFixed(1)} />
                                    <SmallStat label="Monetary" value={formatPrice(segment.avg_monetary)} />
                                </div>
                                <p className="mt-4 rounded-lg bg-gray-50 p-3 text-sm text-gray-600">{segment.playbook.action}</p>
                            </button>
                        ))}
                    </div>
                ) : (
                    <p className="py-8 text-center text-gray-500">No segmentation data available.</p>
                )}
            </div>

            {selectedSegment && (
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="mb-4 flex items-center justify-between">
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900">Customers in {selectedSegment.name}</h2>
                            <p className="text-sm text-gray-500">{selectedSegment.playbook.action}</p>
                        </div>
                        <button
                            onClick={() => setSelectedSegment(null)}
                            className="rounded-lg border px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
                        >
                            Close
                        </button>
                    </div>

                    {customersLoading ? (
                        <SkeletonLoader variant="table" />
                    ) : customers.length > 0 ? (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-200">
                                        <th className="px-3 py-2 text-left text-sm font-semibold text-gray-700">Customer ID</th>
                                        <th className="px-3 py-2 text-left text-sm font-semibold text-gray-700">Name</th>
                                        <th className="px-3 py-2 text-left text-sm font-semibold text-gray-700">Email</th>
                                        <th className="px-3 py-2 text-right text-sm font-semibold text-gray-700">Orders</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {customers.map((customer, index) => (
                                        <tr key={customer.customer_id || index} className="border-b border-gray-100 hover:bg-gray-50">
                                            <td className="px-3 py-2 text-sm">{customer.customer_id}</td>
                                            <td className="px-3 py-2 text-sm">{customer.name || '-'}</td>
                                            <td className="px-3 py-2 text-sm text-gray-600">{customer.email || '-'}</td>
                                            <td className="px-3 py-2 text-right text-sm">{customer.total_orders || 0}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <p className="py-8 text-center text-gray-500">No customers found in this segment.</p>
                    )}
                </div>
            )}
        </div>
    );
}

function Metric({ label, value, compact = false }) {
    return (
        <div className="rounded-xl border bg-white p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
            <p className={`mt-2 font-semibold text-gray-950 ${compact ? "truncate text-lg" : "text-3xl"}`}>{value}</p>
        </div>
    );
}

function SmallStat({ label, value }) {
    return (
        <div>
            <p className="text-xs uppercase tracking-wide text-gray-400">{label}</p>
            <p className="mt-1 font-semibold text-gray-900">{value}</p>
        </div>
    );
}
