import os 
import pandas as pd
import numpy as np
import joblib 
from sklearn.model_selection import train_test_split
from src.logger import get_logger
from src.custom_exception import CustomException
from config.path_config import *
import sys


logger = get_logger(__name__)


class DataProcessor:
    def __init__(self,input_file, output_dir):
        self.input_file = input_file
        self.output_dir = output_dir

        self.rating_df = None
        self.anime_df = None
        self.X_train_array = None
        self.X_test_array = None
        self.y_train = None
        self.y_test = None

        self.user2user_encoded = {}
        self.user2user_decoded = {}
        self.anime2anime_encoded = {}
        self.anime2anime_decoded = {}

        os.makedirs(self.output_dir,exist_ok=True)

        logger.info("Data Processing Intialized")
    
    
    def load_data(self,usecols):
        try:
            self.rating_df = pd.read_csv(self.input_file,low_memory=True, usecols=usecols)
            logger.info("Data loaded successfully for data processing")
        except Exception as e:
            raise CustomException("Failed to load data",e)
    
    def filter_users(self,min_rating=400):
        try:
            n_ratings = self.rating_df["user_id"].value_counts()
            self.rating_df = self.rating_df[self.rating_df["user_id"].isin(n_ratings[n_ratings>=400].index)].copy()
            logger.info("Filtered Users successfully")
        except Exception as e:
            raise CustomException("Failed to filter data",sys)

    def scale_ratings(self):
        try :
            min_rating = min(self.rating_df["rating"])
            max_rating = max(self.rating_df["rating"])

            self.rating_df["rating"] = self.rating_df["rating"].apply(lambda x: (x-min_rating)/(max_rating-min_rating)).values.astype(np.float64)
            logger.info("Scaling done for processing")
        except Exception as e:
            raise CustomException("Failed to scale data",sys)
        
    def encode_data(self):
        try:
            ## User data 
            userids = self.rating_df["user_id"].unique().tolist()
            self.user2user_encoded = {x:i for i, x in enumerate(userids)}
            self.user2user_decoded = {i:x for i, x in enumerate(userids)}

            self.rating_df["user"]=self.rating_df["user_id"].map(self.user2user_encoded)

            ### Anime Data

            anime_ids = self.rating_df["anime_id"].unique().tolist()
            self.anime2anime_encoded = {x:i for i, x in enumerate(anime_ids)}
            self.anime2anime_decoded = {i:x for i, x in enumerate(anime_ids)}
            self.rating_df["anime"]=self.rating_df["anime_id"].map(self.anime2anime_encoded)
            
            logger.info("Encoded Done for Users and Anime")
        except Exception as e:
            raise CustomException("Failed to encode data",sys)
        
    def split_data(self, test_size = 1000 ,random_state=43):
        try:
            self.rating_df = self.rating_df.sample(frac=1,random_state=43).reset_index(drop=True)
            X = self.rating_df[["user","anime"]].values
            y = self.rating_df[["rating"]]


            train_indices = self.rating_df.shape[0] - test_size
            X_train, X_test, y_train,y_test = (
                                        X[:train_indices],
                                        X[train_indices:],
                                        y[:train_indices],
                                        y[train_indices:],
                                    )
            self.X_train_array = [X_train[:,0],X_train[:,1]]
            self.X_test_array = [X_test[:,0],X_test[:,1]]
            self.y_train =y_train
            self.y_test = y_test
            logger.info("Data Splitting is done")
        except Exception as e:
            raise CustomException("Failed to split data",sys)
        
    def save_artifacts(self):
        try:

            artifacts = {
                "user2user_encoded" : self.user2user_encoded,
                "user2user_decoded" : self.user2user_decoded,
                "anime2anime_encoded": self.anime2anime_encoded,
                "anime2anime_decoded" : self.anime2anime_decoded
            
            }

            for name,data in artifacts.items():
                joblib.dump(data,os.path.join(self.output_dir,f"{name}.pkl"))
                logger.info(f"{name} is saved in processed directory")

            joblib.dump(self.X_train_array,X_TRAIN_ARRAY)
            joblib.dump(self.X_test_array,X_TEST_ARRAY)
            joblib.dump(self.y_train,Y_TRAIN)
            joblib.dump(self.y_test,Y_TEST)

            self.rating_df.to_csv(RATING_DF,index=False)

            logger.info("All the data is saved..........")
        
        except Exception as e:
            raise CustomException("Failed to save data",sys)

    def process_anime_data(self):
        try:
            df = pd.read_csv(ANIME_CSV,low_memory=True)
            cols = ["MAL_ID", "Name", "Genres", "sypnopsis"]
            synopsis_df = pd.read_csv(ANIMESYNOPSIS_CSV,usecols=cols, low_memory = True)
            
            df = df.replace("Unknown", np.nan)
            
            def get_anime_name(animeid):
                try:
                    name = df[df.anime_id == animeid].eng_version.values[0]
                    if name is np.nan:
                        name = df[df.anime_id == animeid].Name.values[0]

                except:
                    print("Error")
                return name
            
            df["anime_id"] = df["MAL_ID"]
            df["eng_version"] = df["English name"]

            df["eng_version"]= df.anime_id.apply(lambda x:get_anime_name(x))
        
            df.sort_values(by = ["Score"],
               inplace= True,
               ascending=False,
               kind='quicksort',
               na_position='last')
            df = df[['anime_id','eng_version','Score', 'Genres', 'Episodes','Type', 'Premiered','Members']]

            df.to_csv(DF,index=False)
            synopsis_df.to_csv(SYNOPSIS_DF,index= False)
            logger.info("the data is saved..........")
        except Exception as e:
            raise CustomException("Failed to save anime and synopsis data",sys)
        
    def run(self):
        try:
            self.load_data(usecols=["user_id","anime_id","rating"])
            self.filter_users()
            self.scale_ratings()
            self.encode_data()
            self.split_data()
            self.save_artifacts()
            self.process_anime_data()
            logger.info("the data processing is successfull..........")
        except Exception as e:
            logger.error(str(e))

if __name__ == "__main__":
    processer = DataProcessor(ANIMELIST_CSV,PROCESSED_DIR)
    processer.run()
    