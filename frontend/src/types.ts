export interface ListingItem {
  id: string;
  title: string;
  description: string;
  images: string[];
  price: number;
  meltValue: number;
  profit: number;
  scamRisk: number;
  ebayUrl: string;
}

export interface Filters {
  profit: number;
  scamRisk: number;
  returnsAccepted: boolean;
  sortBy: string;
}