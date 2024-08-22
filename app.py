from flask import Flask, request, render_template, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.json
    video_url = data['video_url']
    start_time = data['start_time']
    end_time = data['end_time']
    video_id = video_url.split('v=')[-1] if 'v=' in video_url else video_url.split('/')[-1]

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = format_transcript(transcript, start_time, end_time)
        chatgpt_response = call_chatgpt(transcript_text)
        return jsonify({'status': 'success', 'original_transcript': transcript_text, 'chatgpt_response': chatgpt_response})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def format_transcript(transcript, start_time, end_time):
    start_seconds = int(start_time.split(":")[0]) * 60 + int(start_time.split(":")[1])
    end_seconds = int(end_time.split(":")[0]) * 60 + int(end_time.split(":")[1])
    formatted_transcript = [entry['text'] for entry in transcript if start_seconds <= entry['start'] <= end_seconds]
    return "\n".join(formatted_transcript)

def call_chatgpt(transcript_text):
    prompt = (
        "Voici une transcription imparfaite d'une vidéo. Je veux que tu traduises et reformule en français correct absolument toute la transcription."
        "Une reformulation avec un niveau de langue modéré pas soutenu (2-3 sur une échelle de 1 à 5)."
        "Il y a deux choses à chaque fois. La voix-off de l'auteur qui explique l'histoire et les dialogues des gens concernés par l'histoire (des extraits vidéos insérées). Différencie clairement la voix-off de l'auteur et les dialogues des extraits vidéos insérées. (sans dire 'voix-off :'"
        "Il est possible qu'il y ai plusieurs extraits et plusieurs moment où l'auteur parle. differencie clairement les moments mais transcrit, traduis et reformule la total."
        "Pour les dialogues des gens, marque 'EXTRAIT :' et traduit et reformule tout, essaye de comprendre le contexte, même si tu ne comprends que approximativement. A la fin de l'extrait marque 'FIN DE L'EXTRAIT'" 
        "Si il n y a pas 'd'EXTRAIT' dans la vidéo, tu n'as pas besoin de le dire et tu ecris seulement le texte de la voix-off de l'auteur"
        "Il peut y avoir plusieurs extraits, retranscris les tous au bon endroit dans chaque texte, même si c'est approximatif et essaye de comprendre le contexte"
        "Arrête toi seulement à mes consignes, ne rajoute pas de texte"
        "Ecrit directement la transcription sans intro de ta part."
        "Tu n'as pas besoin d'ecrire 'voix-off de l'auteur :' ou 'juge :'. seuls les extraits doivent être indiqués. Voici le texte :\n\n" + transcript_text
    )
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4"
    )
    return response.choices[0].message.content

if __name__ == '__main__':
    app.run(debug=True)