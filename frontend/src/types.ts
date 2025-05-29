export interface ListingItem {
  id: string;
  title: string;
  description: string;
  images: string[];
  price: number;
  meltValue: number;
  profit: number;
  scamRisk: number;
  scamRiskExplanation: string;
  ebayUrl: string;
  sellerUsername: string;
  sellerFeedbackScore: number;
  feedbackPercent: number;
  topRatedBuyingExperience: boolean;
  returnsAccepted: boolean;
  weight: number;
  purity: number;
}

export interface Filters {
  profit: number;
  scamRisk: number;
  returnsAccepted: boolean;
  sortBy: string;
}