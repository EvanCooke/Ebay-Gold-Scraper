import React from 'react';
import '../../styles/components/BuyingGuide/BuyingGuide.css';

const BuyingGuidePage = () => {
  return (
    <div className="buying-guide-container">
      <div className="buying-guide-content">
        <h1>Buying Guide</h1>
        
        <section className="disclaimer-section">
          <h2>Important Disclaimer</h2>
          <p>
            Meltwise is in its early stages of development and still undergoing major improvements. 
            While the platform provides helpful estimates and insights, its current accuracy is limited. 
            Be aware that some listings may include non-gold components (like gemstones or gold-plated items) 
            that incorrectly inflate the gold weight and melt value. The AI may also miss edge cases or 
            fail to detect subtle or elaborate scams. Always double-check listing photos, descriptions, 
            and seller credibility before making a purchase. This tool is meant to assist, not replace, 
            your own judgment. A more reliable and polished version is on the way soon.
          </p>
        </section>

        <section className="details-section">
          <h2>Listing Details</h2>
          
          <div className="guide-detail-item">
            <h3>Melt Value</h3>
            <p>
              This is the raw value of the gold based on purity and current gold price. 
              Gold prices used for calculating melt_value are <span className="highlight">updated once a day at 8:00 am CT</span>.
            </p>
          </div>

          <div className="guide-detail-item">
            <h3>Purity</h3>
            <p>
              How much actual gold is in a piece of jewelry or scrap item, measured in karats. 
              Pure gold is <span className="highlight">24 karats (24k)</span>, meaning it's 99.9% gold. 
              Common purities like <span className="highlight">14k (58.5% gold)</span> or <span className="highlight">10k (41.7% gold)</span> 
              are mixed with other metals for strength and durability. The higher the karat, the more gold content, 
              and the higher the melt value of the item.
            </p>
          </div>

          <div className="guide-detail-item">
            <h3>Weight</h3>
            <p>Measured in grams</p>
          </div>

          <div className="guide-detail-item">
            <h3>Seller Feedback</h3>
            <p>
              How many transactions a seller has completed and how satisfied buyers have been. 
              A high number (e.g., 2,797) means the seller is experienced, while the percentage (e.g., 100%) 
              reflects how many of those buyers left positive reviews. Look for sellers with 
              <span className="highlight">at least a 98% rating and over 100 feedback</span>. 
              This suggests they're reliable and consistent.
            </p>
          </div>

          <div className="guide-detail-item">
            <h3>Top Rated</h3>
            <p>
              A Top Rated badge on eBay means the seller has met strict performance standards over time, 
              including fast shipping, accurate descriptions, and excellent customer service. 
              While not every trustworthy seller has this status, a Top Rated seller generally offers 
              a smoother and safer buying experience.
            </p>
          </div>

          <div className="guide-detail-item">
            <h3>Returns</h3>
            <p>
              We <span className="warning-highlight">highly recommend</span> you purchase only from listings with returns accepted.
            </p>
          </div>

          <div className="guide-detail-item">
            <h3>Scam Risk</h3>
            <p>
              Score from 1 to 10 that assess how risky a gold listing might be. It's calculated using an AI model 
              that analyzes key factors such as seller history and feedback patterns, return policy listing language 
              (e.g., vague descriptions, all caps, buzzwords), price vs. melt value (deals too good to be true).
            </p>
            
            <div className="risk-scale">
              <span className="risk-low">1-3: Likely Safe</span>
              <span className="risk-medium">4-6: Requires Inspection</span>
              <span className="risk-high">7-10: Avoid</span>
            </div>
            
            <p>
              Our AI continually improves by learning from known scam patterns and verified good purchases.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default BuyingGuidePage;