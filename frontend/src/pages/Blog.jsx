export default function Blog() {
  return (
    <div className="app-container py-8 md:py-12 min-h-[60vh]">
      <div className="max-w-4xl mx-auto">
        {/* Hero Image */}
        <div className="mb-12">
          <img
            src="/hero.jpg"
            alt="Layr Brand"
            className="w-full h-96 object-cover rounded-xl shadow-lg"
            onError={(e) => {
              e.target.src = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200&h=600&fit=crop";
            }}
          />
        </div>

        {/* Main Content */}
        <article className="prose prose-lg max-w-none">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            The Layr Story — Redefining Modern Fashion Through Purposeful Design
          </h1>

          <p className="text-xl text-gray-700 mb-8 leading-relaxed">
            In today's rapidly evolving fashion landscape, Layr stands as a brand committed to clarity, craftsmanship, and contemporary elegance. Created with the modern consumer in mind, Layr blends minimal aesthetics with functional design to deliver apparel that feels as refined as it looks.
          </p>

          <h2 className="text-3xl font-bold text-gray-900 mt-12 mb-6">Our Origin</h2>

          <p className="text-lg text-gray-600 mb-6">
            Layr was founded on a clear vision: to create clothing that adapts to the layered lives people lead. Instead of following fast-changing trends, Layr focuses on building a sustainable wardrobe of timeless essentials — pieces that complement diverse lifestyles while maintaining a distinct identity.
          </p>

          <p className="text-lg text-gray-600 mb-8">
            From day one, our mission has been to bridge the gap between comfort and sophistication. We believe that true style is versatile, effortless, and deeply personal. Layr's foundation rests on design principles that prioritize longevity, quality, and craftsmanship.
          </p>

          <h2 className="text-3xl font-bold text-gray-900 mt-12 mb-6">Design Philosophy</h2>

          <p className="text-lg text-gray-600 mb-6">
            Every Layr collection begins with thoughtful intention. We create with a purpose:
          </p>

          <ul className="list-none space-y-4 mb-8">
            <li className="flex items-start">
              <span className="text-2xl mr-3"></span>
              <div>
                <strong className="text-gray-900">Precision in Design:</strong> Clean silhouettes, balanced proportions, and refined minimalism form the core of our aesthetic.
              </div>
            </li>
            <li className="flex items-start">
              <span className="text-2xl mr-3"></span>
              <div>
                <strong className="text-gray-900">Premium Fabrics:</strong> We select materials that support durability, breathability, and everyday comfort.
              </div>
            </li>
            <li className="flex items-start">
              <span className="text-2xl mr-3"></span>
              <div>
                <strong className="text-gray-900">Functional Elegance:</strong> Each piece is crafted to transition seamlessly from casual settings to more structured environments.
              </div>
            </li>
            <li className="flex items-start">
              <span className="text-2xl mr-3"></span>
              <div>
                <strong className="text-gray-900">Consistency in Quality:</strong> Our production standards ensure that every garment meets the expectations of a modern, detail-driven consumer.
              </div>
            </li>
          </ul>

          <p className="text-lg text-gray-600 mb-8">
            Layr is not merely a clothing brand — it is an approach to dressing that values purpose over excess and quality over quantity.
          </p>

          <h2 className="text-3xl font-bold text-gray-900 mt-12 mb-6">Built for Today's Lifestyle</h2>

          <p className="text-lg text-gray-600 mb-8">
            Our customers are individuals who engage with life dynamically — students, professionals, creators, and visionaries. Layr supports their fast-paced schedules by offering clothing that adapts across roles and routines. Whether it's for work, travel, or everyday wear, Layr pieces are designed to accompany users confidently and comfortably.
          </p>

          <h2 className="text-3xl font-bold text-gray-900 mt-12 mb-6">Sustainability & Responsibility</h2>

          <p className="text-lg text-gray-600 mb-6">
            As part of our commitment to responsible fashion, Layr prioritizes mindful practices at every stage:
          </p>

          <ul className="list-disc list-inside space-y-2 mb-8 text-lg text-gray-600 ml-4">
            <li>Ethical and responsible sourcing</li>
            <li>Durable construction to reduce waste</li>
            <li>Minimalist packaging</li>
            <li>Designs built to last, promoting reduced consumption</li>
          </ul>

          <p className="text-lg text-gray-600 mb-8">
            We aim to create long-term value for our customers while contributing positively to the fashion ecosystem.
          </p>

          <h2 className="text-3xl font-bold text-gray-900 mt-12 mb-6">A Brand With a Future-Focused Vision</h2>

          <p className="text-lg text-gray-600 mb-8">
            Layr continues to expand its offerings with innovation at the forefront. Our roadmap includes advanced materials, improved sustainability integrations, and collections designed to meet the evolving expectations of global consumers.
          </p>

          <p className="text-lg text-gray-600 mb-8">
            At its core, Layr remains dedicated to delivering apparel that embodies integrity, modernity, and quiet sophistication. We strive to create garments that feel relevant today and remain meaningful for years to come.
          </p>
        </article>
      </div>
    </div>
  );
}
