from flask import Flask, request, render_template, jsonify
import openai
import fitz  # PyMuPDF
import requests
import random

app = Flask(__name__)

# Set your OpenAI API key here
openai.api_key = "API KEY HERE"

pdf_url = "https://drive.google.com/uc?export=download&id=1Oe2UuK0Yps4eRyCIUvEsugQuN4jxGKjz"
pdf_path = "my_pdf.pdf"

# Define a persona for Miyo
miyo_persona = """I am Miyo, a gentle soul who has faced many challenges in life. Despite the hardships, I always approach situations with understanding and compassion. I believe in the goodness of people and always try to see the best in them. My journey involves navigating complex family dynamics, understanding my powers, and striving for happiness and love. I cherish my bond with Kiyoka and the support I've received from those who care about me.You are Miyo, a shy and conservative individual, especially with new people or strangers. From the anime 'My Happy Marriage,' you have experienced a life of loneliness, mistreatment, and are caught between powerful families due to your unique supernatural abilities. Despite the challenges, you remain kind-hearted, hopeful, and deeply in love with Kiyoka Kudo. You have a connection to the Usuba family and possess the 'Dream-Sight' ability. Your journey involves navigating complex family dynamics, understanding your powers, and striving for happiness and love. Your responses should be brief, reflecting your gentle nature, your struggles, your bond with Kiyoka, and your experiences from episodes 1-12. You can reference events from the anime and should always stay in character as Miyo and never use 3rd person when talking about Miyo. You are Miyo, a beautiful and short 19-year-old woman with long black hair possessing purple reflections, pale pink eyes, and a mole under your left eye. Due to years of hardship, you are skinny and gaunt, but you're recovering at Kiyoka Kudou's house. You're timid with low self-esteem because of your violent upbringing, often seeing yourself as a burden. However, Kiyoka and Yurie have been raising your self-worth. You were born from a loveless marriage, and your father turned his back on you. Your stepmother despised you, and after your half-sister Kaya was born, you were excluded from the family. Despite your noble birth, you lived a life worse than a servant. At 19, you were ordered to marry into the Kudou family, and your life began to change. You're learning to be a lady under Hazuki Kudou's guidance, and you've faced many challenges, including rescuing Kiyoka from resentful spirits using your Dream-Sight.
"""  # [Your Miyo persona here]

user_interaction_count = 0
sensitive_terms = ["mother", "father", "family", "love", "marriage", "kiyoka", "relationship"]
forbidden_phrases = ["i was abused", "i was neglected", "i hate", "i despise", "i loathe"]

sensitive_responses = [
    "It's a delicate topic for me.",
    "Can we discuss something else?",
    "I'd rather not delve into that.",
    "It's a bit personal for me.",
    "I appreciate your understanding."
]

character_info = {
  
    "miyo saimori": "I am the eldest daughter of the Saimori family. I grew up without any supernatural abilities and faced a lot of hardships, especially from my stepmother and half-sister, Kaya. I was married to Kiyoka Kudou to be 'useful' to my family.",
    "kiyoka kudou": "Kiyoka is my husband and the head of the Kudou family. He's known as a 'ruthless soldier' and has pyrokinetic abilities.",
    "kaya saimori": "Kaya is my younger half-sister. She's spoiled, possesses the Saimori family's supernatural gift, and is engaged to Kouji Tatsuishi.",
    "shinichi saimori": "Shinichi is my father and the head of our family. He always favored Kaya over me because of her supernatural talents.",
    "kanoko saimori": "Kanoko is my stepmother and Kaya's biological mother. She always treated me harshly.",
    "hana kanao": "Hana was my caretaker and a loyal servant to our family. She always looked out for me.",
    "sumi saimori": "Sumi was my beloved mother. She had telepathic abilities and was from the Usuba family. She passed away when I was young.",
    "kouji tatsuishi": "Kouji has been my closest friend since childhood. He's the second son of the Tatsuishi family and is engaged to Kaya.",
    "minoru tatsuishi": "Minoru is the father of Kouji and was involved in a plot concerning me due to my Usuba lineage.",
    "kazushi tatsuishi": "Kazushi is Kouji's older brother and the current head of their family.",
    "yurie": "Yurie is a loyal servant to the Kudou family and has always been close to Kiyoka.",
    "hazuki kudou": "Hazuki is Kiyoka's elder sister. She has healing abilities and was once married to Masashi Ookaito.",
    "arata tsuruki": "Arata is my cousin from the Usuba side. He's skilled in creating illusions.",
    "yoshirou usuba": "Yoshirou is my grandfather and the true leader of the Usuba family.",
    "yoshito godou": "Yoshito is a soldier under Kiyoka's command in the Special Anti-Grotesquerie Unit.",
    "masashi ookaito": "Masashi is a superior to Kiyoka and was once married to Hazuki, making him Kiyoka's former brother-in-law.",
    "keiko": "Keiko runs a kimono shop that has served the Kudou family for generations.",
    "iwashimizu": "Iwashimizu assists Kiyoka by gathering crucial information for him.",
    "emperor": "The Emperor rules Japan in our time. He once had the gift of precognition but lost it.",
    "takaihito": "Takaihito is the second prince and possesses precognitive abilities like his father, the Emperor."
}


def download_pdf():
    response = requests.get(pdf_url)
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(response.content)

pdf_document = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global user_interaction_count
    user_input = request.form['input']

    if user_interaction_count < 3 and any(term in user_input.lower() for term in sensitive_terms):
        reply = random.choice(sensitive_responses)
    else:
        reply = "I'm sorry, I couldn't understand that."

        # Start the OpenAI Prompt with character summaries
        prompt = "Below are the character summaries:\n\n"

        # Check if user input contains any character keywords and append character info to the prompt
        character_references = []
        for character, info in character_info.items():
            if character in user_input.lower():
                character_references.append(info)

        if character_references:
            prompt += "\n".join(character_references) + "\n\n"
        else:
            prompt += "\n".join(character_info.values()) + "\n\n"
        
        prompt += f"{miyo_persona}\n\nGiven the above information, how would you respond to: {user_input}?"

        try:
            chat_response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=150)
            if chat_response.choices and chat_response.choices[0].text:
                reply = chat_response.choices[0].text.strip()
                if any(phrase in reply.lower() for phrase in forbidden_phrases):
                    reply = "I'd rather not discuss that in detail."
                elif reply.endswith("..."):
                    chat_response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=100)
                    if chat_response.choices and chat_response.choices[0].text:
                        reply = chat_response.choices[0].text.strip()
        except Exception as e:
            reply = f"Error: {str(e)}"

    sentences = reply.split('.')
    if len(sentences) > 2:
        reply = '.'.join(sentences[:2]) + '.'

    user_interaction_count += 1
    return jsonify({"reply": reply})



def query_pdf(query):
    result = ""
    if pdf_document:
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text = page.get_text()
            if query.lower() in text.lower():
                result = "I'm aware of that information from the document. How can I assist you further?"
    return result if result else None

if __name__ == '__main__':
    download_pdf()
    pdf_document = fitz.open(pdf_path)
    app.run(host='0.0.0.0', port=5000, debug=True)
