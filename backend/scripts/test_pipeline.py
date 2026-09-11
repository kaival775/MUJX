
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from feature4_drl.pipeline import CropRecommender

def test_pipeline():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, "feature4_drl", "crop_recommendation_models")
        dataset_path = os.path.join(current_dir, "feature4_drl", "enhanced_agriculture_dataset.csv")
        
        logger.info(f"Initializing CropRecommender with:\nModel Dir: {model_dir}\nDataset: {dataset_path}")
        
        recommender = CropRecommender(model_dir, dataset_path)
        
        # Test Data (sample input)
        test_input = {
            'soil_n': 90,
            'soil_p': 42,
            'soil_k': 43,
            'ph': 6.5,
            'soil_moisture': 30,
            'avg_temperature': 28,
            'seasonal_rainfall': 850,
            'humidity': 50,
            'crop_duration_days': 120,
            'soil_type': 'Alluvial',
            'state': 'Maharashtra',
            'district': 'Pune',
            'climate_season': 'Kharif',
            'previous_crop': 'Rice'
        }
        
        logger.info(f"Testing with input: {test_input}")
        
        recommendations = recommender.get_top_recommendations(test_input, top_n=3)
        
        print("\n--- RECOMMENDATIONS ---")
        for rec in recommendations:
            print(f"Crop: {rec['crop_name']}")
            print(f"  Yield: {rec['predicted_yield']} t/ha")
            print(f"  Expected Revenue: ₹{rec['expected_revenue']}")
            print(f"  Potential Loss: ₹{rec['potential_loss']}")
            print("-" * 30)
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
