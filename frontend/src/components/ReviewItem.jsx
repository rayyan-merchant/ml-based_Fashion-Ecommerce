export default function ReviewItem({ review }) {
  const reviewerName =
    review.reviewer_name ||
    review.customer_name ||
    [review.first_name, review.last_name].filter(Boolean).join(" ").trim() ||
    "Verified Customer";
  const reviewerInitial = reviewerName.charAt(0).toUpperCase();

  // Simple sentiment analysis based on rating
  const getSentiment = (rating) => {
    if (rating >= 4) return { label: "Positive", color: "bg-green-100 text-green-800" };
    if (rating >= 3) return { label: "Neutral", color: "bg-yellow-100 text-yellow-800" };
    return { label: "Negative", color: "bg-red-100 text-red-800" };
  };

  const sentiment = getSentiment(review.rating);

  return (
    <div className="border p-4 rounded mb-4">
      <div className="flex justify-between items-start">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#F5EDD8] text-sm font-semibold text-[#A07840]">
            {reviewerInitial}
          </div>
          <div>
            <p className="font-bold">{reviewerName}</p>
            <div className="flex items-center mt-1">
              <span className="mr-2">Rating: {review.rating} / 5</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${sentiment.color}`}>
                {sentiment.label}
              </span>
            </div>
          </div>
        </div>
        <p className="text-gray-500 text-sm">{new Date(review.created_at).toLocaleDateString()}</p>
      </div>
      <p className="mt-2">{review.review_text}</p>
    </div>
  );
}
