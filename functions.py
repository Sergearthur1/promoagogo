import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import os
from openai import OpenAI
import openai
import numpy as np
from git import Repo
import os

def get_description(url):
    r = requests.get(url)
    return r.text.split("""shortDescription":""")[1].split("""","isCrawlable""")[0]
    
def get_channel_name(url): 
    return url.split("&ab_channel=")[1]
    
def get_trends_url():
    url = "https://www.youtube.com/feed/trending"
    r = requests.get(url)
    #soup = BeautifulSoup(r.text, "lxml")
    #text_tamp = soup.find("body").text
    text_tamp = r.text
    last_index = 0
    last_index += text_tamp[last_index:].find('"videoId"')
    breaked = False
    urls = []
    while(not(breaked)):
        videoId = text_tamp[last_index:].split('":"')[1].split('","')[0]
        last_index += text_tamp[last_index:].find('"canonicalBaseUrl"')
        channel = text_tamp[last_index:].split('":"')[1].split('"')[0]
        last_index += text_tamp[last_index:].find('"videoId"')
        while(videoId == text_tamp[last_index:].split('":"')[1].split('","')[0]):
            old_index = last_index
            last_index += text_tamp[last_index + 1:].find('"videoId"')
            last_index += 1
            if(old_index >= last_index):
                breaked = True
                break
        if("/channel/" in channel):
            urls.append(
                f"https://www.youtube.com/watch?v={videoId}&ab_channel={channel}"
            )
        else:
            urls.append(
                f"https://www.youtube.com/watch?v={videoId}&ab_channel={channel[2:]}"
            )
    return urls

def get_trends_url_2(api_key):
    url = "https://www.googleapis.com/youtube/v3/videos"

    # Paramètres de la requête
    params = {
        'part': "id,snippet",
        'chart': "mostPopular",
        'regionCode': "FR",
        'maxResults': 50,
        'key': api_key,
    }

    # Faire la requête GET
    response = requests.get(url, params=params)
    
    # Vérifier si la requête a réussi
    if response.status_code == 200:
        data = response.json()
        
        # Extraire les URLs des vidéos
        video_urls = []
        for item in data["items"]:
            video_id = item['id']
            ab_channel = item["snippet"]['channelTitle']
            video_url = f"https://www.youtube.com/watch?v={video_id}&ab_channel={ab_channel}"
            if "Topic" not in ab_channel:
                video_urls.append(video_url)
        return video_urls
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return []

def get_pourcent(phrase):
    index = phrase.find("%")
    if index == -1:
        return np.nan
    else:
        while phrase[index - 1] == " ":
            index = index - 1
        while((phrase[index-1] >= "0") and (phrase[index-1] <= "9")):
              index = index - 1
        last_index = phrase.find("%")
    return int(phrase[index:last_index])

def get_euros(phrase):
    list_synonyme_euros = ["€", "euro"]
    for euro_symbol in list_synonyme_euros:
        index = phrase.find(euro_symbol)
        if(index  != -1):
            break
    if index == -1:
        return np.nan
    else:
        while phrase[index - 1] == " ":
            index = index - 1
        while((phrase[index-1] >= "0") and (phrase[index-1] <= "9")):
              index = index - 1
        last_index = phrase.find(euro_symbol)
    return int(phrase[index:last_index])

def get_period_intensity(phrase):
    phrase = str(phrase).lower()
    if " an" in phrase:
        return 1.
    elif "mois" in phrase:
        return 0.75
    elif "semaine" in phrase:
        return 0.5
    elif "jours" in phrase:
        return 0.25
    else:
        return np.nan

def clean_historical_urls(min_date):
    df_historical_urls = pd.read_csv(f"{os.getcwd()}/historical_urls.csv")
    df_historical_urls["datetime"] = df_historical_urls["date"].apply(lambda x: pd.to_datetime(x, format ="%Y-%m-%d"))
    df_historical_urls = df_historical_urls[df_historical_urls["datetime"] > min_date]
    del df_historical_urls["datetime"]
    df_historical_urls.to_csv(f"{os.getcwd()}/historical_urls.csv", index=False)
    
def clean_promos(min_date):
    df_promos = pd.read_csv("promos.csv")
    df_promos["datetime"] = df_promos["date de création"].apply(lambda x: pd.to_datetime(x, format ="%Y-%m-%d"))
    df_promos = df_promos[df_promos["datetime"] > min_date]
    del df_promos["datetime"]
    df_promos.to_csv("promos.csv", index=False)
    
def filter_code_createur(df):
    def find_code_createur(phrase):
        bannish_words = [
            "souteni",
            "soutien",
            "ode créateur", 
            "odecréateur", 
            "odecreateur", 
            "ode createur", 
            "odes createur", 
            "odes créateur",
        ]
        find_bannish_word = False
        for bannish_word in bannish_words:
            if bannish_word in phrase:
                find_bannish_word = True
                break
        return not(find_bannish_word)
    return df[df["description de l'offre en 1 phrase"].apply(find_code_createur)]

def read_string_dict_list(reponse_str):
    reponse = pd.DataFrame(
        data = {
            "code": [],
            "dates": [],
            "lien": [],
            "description de loffre en 1 phrase": [],
            "marque": [],
        },
        index=[],
    )
    for line in reponse_str.splt("}"):
        sub_reponse = {}
        for champs in line.split(","):
            key = champs.split(": ")[0].replace("\'", "").replace("[","").replace("{","").replace("}", "").replace("]","")
            value = champs.split(": ")[1].replace("\'", "").replace("[","").replace("{","").replace("}", "").replace("]","")
            sub_reponse[key] = value
        reponse.append(pd.Dataframe.from_dict(sub_reponse))
    return reponse
    

def get_new_code_promo(gpt_api_key,youtube_api_key):
    df_new_code_promo = pd.DataFrame(
        data={
            "code": [],
            "dates": [],
            "lien": [],
            "description de l'offre en 1 phrase": [],
            "marque": [],
            "source": [],
            "url source": [],
            "date de création": [],
        },
        index = [],
    )
    client = OpenAI(api_key=gpt_api_key)
    prompt = """trouve moi dans le texte suivant des codes promotionnels en formatant ta réponse au format d'une liste de dictionnaire python comme suit [{"code": "", "dates": "","lien": "", "description de l'offre en 1 phrase": "", "marque": ""}], et si il n'y a pas de code promotionel renvoyer la phrase: pas de code."""
    today_date = dt.date.today()
    urls = get_trends_url_2(youtube_api_key)
    df_historical_urls = pd.read_csv(f"{os.getcwd()}/historical_urls.csv")
    for url in urls:
        if(url not in list(df_historical_urls["url"])):
            channel_name = get_channel_name(url)
            if "/channel/" not in channel_name:
                print(url)
                description = get_description(url)
                channel_name = get_channel_name(url)
                df_historical_urls = df_historical_urls.append(
                    pd.DataFrame(
                        {
                            "url": url,
                            "date": today_date.isoformat()
                        },
                        index =[len(df_historical_urls.index)],
                    ),
                    sort=False
                )
                ##### appel a chatGPT ########
                completion = client.chat.completions.create(
                  model="gpt-3.5-turbo", 
                  messages=[{"role": "user", "content": prompt + "\n" + description[:1000]}]
                )
                try:
                    reponse = eval(completion.choices[0].message.content)
                    for line in reponse:
                        line["source"] = channel_name
                        line["url source"] = url
                        line["date de création"] = today_date.isoformat()
                        df_new_code_promo = df_new_code_promo.append(
                            line,
                            ignore_index=True,
                        )
                except:
                    pass
    df_new_code_promo = filter_code_createur(df_new_code_promo)
    if(df_new_code_promo.empty):
        return df_new_code_promo
    df_new_code_promo["reduction (%)"] = df_new_code_promo["description de l'offre en 1 phrase"].apply(get_pourcent)
    df_new_code_promo["reduction (€)"] = df_new_code_promo["description de l'offre en 1 phrase"].apply(get_euros)
    df_new_code_promo["disclosure criteria"] = 0.33 * df_new_code_promo["code"].apply(lambda x:not(pd.isna(x))) + 0.33 * df_new_code_promo["dates"].apply(lambda x: not(pd.isna(x))) + 0.33 * df_new_code_promo.apply(lambda x: not(pd.isna(x["reduction (€)"]) and pd.isna(x["reduction (%)"])),axis=1)
    df_historical_urls.to_csv(f"{os.getcwd()}/historical_urls.csv", index=False)
    return df_new_code_promo

def inverse_percentile(arr,num):
    arr = sorted(arr)
    i_arr = [i for i, x in enumerate(arr) if x > num]
    return i_arr[0] / len(arr) if len(i_arr) > 0 else 1

def sort_reduction(x, list_reduction):
    if pd.isna(x):
        return 0
    else:
        return inverse_percentile(list_reduction,x)
            
def sort_promo(df):
    today_date = dt.date.today()
    df["euro rank"] = df["reduction (€)"].apply(sort_reduction,list_reduction=list(df["reduction (€)"].dropna()))
    df["% rank"] = df["reduction (%)"].apply(sort_reduction,list_reduction=list(df["reduction (%)"].dropna()))
    df["time rank"] = df["reduction (time)"].fillna(0)
    df["reduction criteria"] = df[["euro rank","% rank","time rank"]].max(axis=1)
    df["marque2"] = df["marque"].apply(lambda x: str(x).replace(" ", "").lower())
    df["rarity criteria"] =  0.5 * df["marque2"].apply(lambda x: 1 / len(df[df["marque2"] == x].index))
    df["anciennete"] = df["date de création"].apply(lambda x:  1 - (today_date - dt.date.fromisoformat(x)).total_seconds() / (3 * 30 * 24 * 60 * 60))
    df["final score"] = df[["reduction criteria","rarity criteria","disclosure criteria", "anciennete"]].mean(axis=1)
    df = df.sort_values(by=["final score"], ascending=False)
    df = df[df["final score"] > 0.5]
    return df[[
        col for col in df 
        if col not in ["euro rank", "% rank", "time rank", "reduction criteria", "rarity criteria", "final score", "marque2", "anciennete"]
    ]]

def git_commit(file_name, username, password):
    #set crendential
    os.environ['GIT_ASKPASS'] = 'echo'
    os.environ['GIT_USERNAME'] = username
    os.environ['GIT_PASSWORD'] = password
    # Initialiser le repo
    date = dt.date.today()
    repo = Repo()
    repo.index.add([file_name])
    repo.index.commit(f"update {file_name}| {date}")
    origin = repo.remote(name='origin')
    origin.push()
