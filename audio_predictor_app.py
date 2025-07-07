import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import re
import statistics

st.set_page_config(page_title="🎧 Prédicteur Audio de Match", layout="centered")
st.title("🎧 Prédicteur de Match via Audio (.mp3)")

def transcrire_audio_st(audio_file):
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        sound = AudioSegment.from_file(audio_file, format="mp3")
        sound.export(tmp_wav.name, format="wav")
        with sr.AudioFile(tmp_wav.name) as source:
            audio_data = recognizer.record(source)
            texte = recognizer.recognize_google(audio_data, language="fr-FR")
    return texte

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

audio = st.file_uploader("🎤 Téléverse un fichier audio (.mp3)", type=["mp3"])

if audio is not None:
    with st.spinner("🧠 Transcription en cours..."):
        try:
            texte = transcrire_audio_st(audio)
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
                    st.warning("Pas assez de données pour prédire.")
            else:
                st.error("❌ Aucun match détecté.")
        except Exception as e:
            st.error(f"Erreur de transcription : {str(e)}")
