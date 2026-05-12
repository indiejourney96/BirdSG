export interface PredictionItem {
  label: string;
  confidence: number;
  singapore_match: boolean;
}

export interface PredictResponse {
  filename: string;
  mode: string;
  predictions: PredictionItem[];
  singapore_filtered: boolean;
  sighting_id?: string;
}