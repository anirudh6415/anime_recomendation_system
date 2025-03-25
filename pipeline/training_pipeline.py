from config.path_config import *
from utils.common_functions import read_yaml
from src.data_processing import DataProcessor
from src.model_training import ModelTraining


if __name__ == "__main__":
    # data_ingestion = DataIngestion(read_yaml(CONFIG_PATH))
    # data_ingestion.run()

    processer = DataProcessor(ANIMELIST_CSV,PROCESSED_DIR)
    processer.run()
    
    model_trainer = ModelTraining(PROCESSED_DIR)
    model_trainer.train_model()