import streamlit as st
import whisper
import re
import statistics

# Titre de l'app
st.set_page_config(page_title="🎧 Prédicteur Audio de Match", layout="centered")
st.title("🎧 Prédicteur de Match via Audio")

# Chargement du modèle Whisper (petit modèle pour rapidité)
@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

# Transcription audio
def transcrire_audio(audio_file):
    with open("temp_audio.mp3", "wb") as f:
        f.write(audio_file.read())
    result = model.transcribe("temp_audio.mp3", language="fr")
    return result["text"]

# Extraction des scores à partir du texte
def extraire_matchs_depuis_texte(texte):
    pattern = r"(?P<equipe1>[A-Za-zÀ-ÿ\s\-']+)\s+(contre|vs)\s+(?P<equipe2>[A-Za-zÀ-ÿ\s\-']+)[^\d]*(?P<score1>\d+)[^\d]+(?P<score2>\d+)"
    matchs = re.findall(pattern, texte, flags=re.IGNORECASE)
    resultats = []
    for m in matchs:
        equipe1 = m[0].strip().lower()
        equipe2 = m[2].strip().lower()
        score1 = int(m[3])
        score2 = int(m[4])
        resultats.append((equipe1, equipe2, score1, score2))
    return resultats

# Analyse et prédiction basées sur la moyenne
def predire_prochain_score(historique):
    stats = {}
    for eq1, eq2, s1, s2 in historique:
        for eq, s_for, s_against in [(eq1, s1, s2), (eq2, s2, s1)]:
            if eq not in stats:
                stats[eq] = {'for': [], 'against': []}
            stats[eq]['for'].append(s_for)
            stats[eq]['against'].append(s_against)
    if len(historique) >= 1:
        derniere = historique[-1]
        eq1, eq2 = derniere[0], derniere[1]
        avg1 = statistics.mean(stats[eq1]['for'])
        avg2 = statistics.mean(stats[eq2]['for'])
        score_estime = (round(avg1), round(avg2))
        if avg1 > avg2:
            gagnant = eq1.title()
        elif avg2 > avg1:
            gagnant = eq2.title()
        else:
            gagnant = "Match nul"
        return score_estime, gagnant
    return None, None

# Interface utilisateur
audio = st.file_uploader("🎤 Téléverse un fichier audio (.mp3)", type=["mp3"])

if audio is not None:
    with st.spinner("Transcription en cours..."):
        texte = transcrire_audio(audio)
    st.subheader("📝 Transcription :")
    st.success(texte)

    matchs = extraire_matchs_depuis_texte(texte)

    if matchs:
        st.subheader("📊 Matchs détectés :")
        for m in matchs:
            st.write(f"{m[0].title()} {m[2]} - {m[3]} {m[1].title()}")

        st.subheader("🔮 Prédiction du prochain match :")
        score, gagnant = predire_prochain_score(matchs)
        if score:
            st.info(f"Score estimé : {matchs[-1][0].title()} {score[0]} - {score[1]} {matchs[-1][1].title()}")
            st.success(f"🏆 Victoire probable : {gagnant}")
        else:
            st.warning("Pas assez de données pour faire une prédiction.")
    else:
        st.error("❌ Aucun match détecté dans la transcription.")
