from config.path_config import *
from utils.helper import *


def hybrid_recommendation(user_id,user_weight=0.5,content_weight = 0.5):
    #### User recommendation
    simialar_user = find_similar_users(user_id,
                        USER_WEIGHTS_PATH,
                        USER2USER_ENCODED,
                        USER2USER_DECODED
                        )
    
    user_pref= get_user_preferences(user_id,RATING_DF,DF)
    user_recommended_anime = get_user_recommendation(simialar_user,user_pref,RATING_DF,DF,SYNOPSIS_DF)

    user_recommended_anime_list = user_recommended_anime["anime_name"].to_list()
    # print(user_recommended_anime_list)
    ##### Content Recomendation
    content_recommended_anime = []

    for anime in user_recommended_anime_list:
        similar_animes = find_similar_animes(anime,
                        ANIME_WEIGHTS_PATH,
                        ANIME2ANIME_ENCODED,
                        ANIME2ANIME_DECODED,
                        DF,SYNOPSIS_DF)
        if similar_animes is not None and not similar_animes.empty:
            # print(similar_animes)
            content_recommended_anime.extend(similar_animes["name"].tolist())

        else:
            print(f"No Similar Animes found {anime}")


    
    combined_scores = {}

    for anime in user_recommended_anime_list:
        combined_scores[anime] = combined_scores.get(anime,0) + user_weight
    
    for anime in content_recommended_anime:
        combined_scores[anime] = combined_scores.get(anime,0) + content_weight

    sorted_animes = sorted(combined_scores.items() , key=lambda x:x[1] , reverse=True)
    return [anime for anime, score in sorted_animes[:10]]