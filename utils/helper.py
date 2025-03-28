import pandas as pd
import numpy as np
import joblib 
from config.path_config import *



def getAnimeFrame(anime,df):
    if isinstance(anime,int):
        return df[df.anime_id == anime]
    if isinstance(anime,str):
        return df[df.eng_version == anime]
    
def getSynopsis(anime,df):
    if isinstance(anime, int):
        anime_data = df[df.MAL_ID == anime]
    elif isinstance(anime, str):
        anime_data = df[df.Name == anime]
    else:
        return "" 

    if anime_data.empty:
        return ""

    return anime_data["sypnopsis"].values[0]

############ Content Recommendation ##############################
def find_similar_animes(name,
                        path_anime_weights,
                        path_anime2anime_encoded,
                        path_anime2anime_decoded,
                        path_df, path_synopsis_df, n=10,
                        return_dist=False, neg=False):
    
    anime_weights = joblib.load(path_anime_weights)
    anime2anime_encoded = joblib.load(path_anime2anime_encoded)
    anime2anime_decoded = joblib.load(path_anime2anime_decoded)
    df = pd.read_csv(path_df)
    synopsis_df = pd.read_csv(path_synopsis_df)

    try:
        index = getAnimeFrame(name, df).anime_id.values[0]
        encoded_index = anime2anime_encoded.get(index)

        if encoded_index is None:
            raise ValueError(f"Encoded index not found for anime ID {index}")

        weights = anime_weights
        dists = np.dot(weights, weights[encoded_index])
        sorted_dists = np.argsort(dists)

        n = n + 1

        if neg:
            closest = sorted_dists[:n]
        else:
            closest = sorted_dists[-n:]

        # print(f"Anime closest to {name}: {closest}")

        if return_dist:
            return dists, closest

        SimilarityArr = []
        for close in closest:
            decoded_id = anime2anime_decoded.get(close)
            if decoded_id is None:
                continue  

            synopsis = getSynopsis(decoded_id, synopsis_df)
            anime_frame = getAnimeFrame(decoded_id, df)

            if anime_frame.empty:
                continue 

            anime_name = anime_frame.eng_version.values[0]
            genre = anime_frame.Genres.values[0]
            similarity = dists[close]

            SimilarityArr.append({
                "anime_id": decoded_id,
                "name": anime_name,
                "similarity": similarity,
                "genre": genre,
                "synopsis": synopsis
            })

        if not SimilarityArr:
            raise ValueError("No similar animes found.")

        frame = pd.DataFrame(SimilarityArr)
        

        # print("Final DataFrame Columns:", frame.columns)

        frame = frame.sort_values(by="similarity", ascending=False)
        # return frame 
        return frame[frame.anime_id != index].drop(["anime_id"], axis=1)

    except Exception as e:
        print(f"Error occurred: {e}")
        raise

############## Find Similar Users ##########################
def find_similar_users(item_input,
                        path_user_weights,
                        path_user2user_encoded,
                        path_user2user_decoded,
                        n=10,
                        return_dist=False, neg=False):
    
    user_weights = joblib.load(path_user_weights)
    user2user_encoded = joblib.load(path_user2user_encoded)
    user2user_decoded = joblib.load(path_user2user_decoded)

    try :
        index = item_input

        encoded_index = user2user_encoded.get(index)

        weights = user_weights

        dists = np.dot(weights,weights[encoded_index])
        sorted_dists = np.argsort(dists)

        n = n + 1

        if neg:
            closest = sorted_dists[:n]
        else:
            closest = sorted_dists[-n:]

        if return_dist:
            return dists, closest
        

        SimilarityArr = []
        for close in closest:
            similarity = dists[close]

            if isinstance(item_input, int):
                decoded_id = user2user_decoded.get(close)
                SimilarityArr.append({
                    "similar_users" :decoded_id,
                    "similarity": similarity
                })
        frame = pd.DataFrame(SimilarityArr)
        

        # print("Final DataFrame Columns:", frame.columns)

        frame = frame.sort_values(by="similarity", ascending=False)
        return frame[frame.similar_users != item_input]

    except Exception as e:
        print(f"Error occurred: {e}")
        raise
 
 ############### Get User preferences #####################

def get_user_preferences(user_id,path_rating_df,path_df):
    rating_df = pd.read_csv(path_rating_df)
    df = pd.read_csv(path_df)
    animes_watched_by_user = rating_df[rating_df.user_id == user_id]

    user_rating_percentile = np.percentile(animes_watched_by_user.rating, 75)

    animes_watched_by_user = animes_watched_by_user[animes_watched_by_user.rating >= user_rating_percentile]

    top_animes_user = (
        animes_watched_by_user.sort_values(by = "rating", ascending = False).anime_id.values
    )

    anime_df_rows = df[df["anime_id"].isin(top_animes_user)]
    anime_df_rows = anime_df_rows[["eng_version","Genres"]]

    return anime_df_rows

######### USer recommendation ##################
def get_user_recommendation(simialar_users,user_pref,path_rating_df,path_df,path_synopsis_df,n=10):

    rating_df = pd.read_csv(path_rating_df)
    df = pd.read_csv(path_df)
    synopsis_df = pd.read_csv(path_synopsis_df)

    recommended_animes = []
    anime_list = []

    for userid in simialar_users.similar_users.values:
        pref_list = get_user_preferences(int(userid),path_rating_df,path_df)

        pref_list = pref_list[~pref_list.eng_version.isin(user_pref.eng_version.values)]

        if not pref_list.empty:
            anime_list.append(pref_list.eng_version.values)

    if anime_list :
        anime_list = pd.DataFrame(anime_list)

        sorted_list = pd.DataFrame(pd.Series(anime_list.values.ravel()).value_counts()).head(n)

        for i, anime_name in enumerate(sorted_list.index):
            n_user_pref = sorted_list[sorted_list.index == anime_name].values[0]

            if isinstance(anime_name,str):
                frame = getAnimeFrame(anime_name,df)
                anime_id = frame.anime_id.values[0]
                genre = frame.Genres.values[0]
                synopsis = getSynopsis(int(anime_id),synopsis_df)

                recommended_animes.append({
                    "n": n_user_pref,
                    "anime_name": anime_name,
                    "Genres" : genre,
                    "Synopsis": synopsis
                })

    return pd.DataFrame(recommended_animes).head(n)

