import webbrowser
import speech_recognition as sr
import pyttsx3
import platform
import subprocess
import datetime
import os
import openai
from config import apikey
import random

# Initialize global variables and settings
chatStr = ""
tts_engine = pyttsx3.init()
recognizer = sr.Recognizer()
mic = sr.Microphone()
openai.api_key = apikey

# Define the applications and their respective commands
applications = {
    'notepad': 'notepad.exe',
    'calculator': 'calc.exe',
    'command prompt': 'cmd.exe',
    'explorer': 'explorer.exe',
    'paint': 'mspaint.exe',
    'chrome': 'chrome.exe',
    'firefox': 'firefox.exe',
    'edge': 'msedge.exe',
    'opera': 'opera.exe',
    'safari': 'safari.exe',
    'word': 'winword.exe',
    'excel': 'excel.exe',
    'powerpoint': 'powerpnt.exe',
    'outlook': 'outlook.exe',
    'skype': 'skype.exe',
    'slack': 'slack.exe',
    'zoom': 'zoom.exe',
    'teams': 'teams.exe',
    'discord': 'discord.exe',
    'spotify': 'spotify.exe',
    'itunes': 'itunes.exe',
    'vlc': 'vlc.exe',
    'windows media player': 'wmplayer.exe',
    'photos': 'msphotos.exe',
    'camera': 'microsoft.windows.camera',
    'mail': 'microsoft.windows.mail',
    'calendar': 'microsoft.windows.calendar',
    'settings': 'ms-settings:',
    'control panel': 'control.exe',
    'task manager': 'taskmgr.exe',
    'notepad++': 'notepad++.exe',
    'visual studio code': 'code.exe',
    'pycharm': 'pycharm.exe',
    'atom': 'atom.exe',
    'sublime text': 'sublime_text.exe',
    'eclipse': 'eclipse.exe',
    'intellij idea': 'idea.exe',
    'android studio': 'studio64.exe',
    'filezilla': 'filezilla.exe',
    'winscp': 'winscp.exe',
    'putty': 'putty.exe',
    'teamviewer': 'teamviewer.exe',
    'anydesk': 'anydesk.exe',
    'photoshop': 'photoshop.exe',
    'illustrator': 'illustrator.exe',
    'premiere pro': 'premiere.exe',
    'after effects': 'afterfx.exe',
    'audacity': 'audacity.exe',
    'obs studio': 'obs64.exe',
    'zoom': 'zoom.exe',
    'discord': 'discord.exe',
    'steam': 'steam.exe',
    'epic games launcher': 'EpicGamesLauncher.exe',
    'minecraft': 'minecraft.exe',
    'fortnite': 'FortniteClient-Win64-Shipping.exe',
    'overwatch': 'Overwatch.exe',
    'league of legends': 'LeagueClient.exe',
    'world of warcraft': 'Wow.exe',
    'dota 2': 'dota2.exe',
    'counter-strike': 'csgo.exe',
    'rainbow six siege': 'RainbowSix.exe',
    'apex legends': 'r5apex.exe',
    'gta v': 'GTA5.exe',
    'rocket league': 'RocketLeague.exe',
    'valorant': 'VALORANT.exe',
    'call of duty': 'ModernWarfare.exe',
    'battlefield': 'bfv.exe',
    'fall guys': 'FallGuys_client.exe',
    'among us': 'AmongUs.exe',
    'phasmophobia': 'Phasmophobia.exe',
    'terraria': 'Terraria.exe',
    'civilization': 'Civ6.exe',
    'sims': 'TS4_x64.exe',
    'minecraft': 'minecraft.exe',
    'roblox': 'RobloxPlayerLauncher.exe',
    'discord': 'discord.exe',
    'zoom': 'zoom.exe',
    'teams': 'teams.exe',
    'skype': 'skype.exe',
    'slack': 'slack.exe',
    'whatsapp': 'whatsapp.exe',
    'viber': 'viber.exe',
    'telegram': 'telegram.exe',
    'signal': 'signal.exe',
    'zoom': 'zoom.exe',
    'webex': 'webex.exe',
    'gotomeeting': 'g2mstart.exe',
    'anydesk': 'anydesk.exe',
    'teamviewer': 'teamviewer.exe',
    'chrome': 'chrome.exe',
    'firefox': 'firefox.exe',
    'edge': 'msedge.exe',
    'opera': 'opera.exe',
    'safari': 'safari.exe',
    'brave': 'brave.exe',
    'vivaldi': 'vivaldi.exe',
    'tor': 'tor.exe',
    'filezilla': 'filezilla.exe',
    'winscp': 'winscp.exe',
    'putty': 'putty.exe',
    'sftp': 'sftp.exe',
    'xampp': 'xampp-control.exe',
    'mamp': 'mamp.exe',
    'wamp': 'wampmanager.exe',
    'xampp': 'xampp-control.exe',
    'xampp': 'xampp-control.exe',
    'virtualbox': 'VirtualBox.exe',
    'vmware': 'vmware.exe',
    'docker': 'docker.exe',
    'android studio': 'studio64.exe',
    'xcode': 'xcode.exe',
    'eclipse': 'eclipse.exe',
    'intellij idea': 'idea.exe',
    'visual studio': 'devenv.exe',
    'pycharm': 'pycharm.exe',
    'anaconda': 'anaconda-navigator.exe',
    'git': 'git-bash.exe',
    'github desktop': 'GitHubDesktop.exe',
    'sourcetree': 'sourcetree.exe',
    'sublime text': 'sublime_text.exe',
    'notepad++': 'notepad++.exe',
    'atom': 'atom.exe',
    'visual studio code': 'code.exe',
    'brackets': 'brackets.exe',
    'netbeans': 'netbeans64.exe',
    'eclipse': 'eclipse.exe',
    'spyder': 'spyder.exe',
    'jupyter notebook': 'jupyter-notebook.exe',
    'pycharm': 'pycharm64.exe',
    'anaconda': 'anaconda-navigator.exe',
    'r studio': 'rstudio.exe',
    'matlab': 'matlab.exe',
    'octave': 'octave-cli.exe',
    'cisco packet tracer': 'PacketTracer.exe',
    'wireshark': 'wireshark.exe',
    'putty': 'putty.exe',
    'virtualbox': 'VirtualBox.exe',
    'vmware': 'vmware.exe',
    'gns3': 'gns3.exe',
    'packet tracer': 'PacketTracer.exe',
    'wireshark': 'wireshark.exe',
    'gns3': 'gns3.exe',
    'minitab': 'minitab.exe',
    'spss': 'stats.exe',
    'r studio': 'rstudio.exe',
    'matlab': 'matlab.exe',
    'octave': 'octave-cli.exe',
    'microsoft access': 'MSACCESS.exe',
    'oracle sql developer': 'sqldeveloper.exe',
    'whatsapp': 'whatsapp.exe'
}
# Define the websites and their respective URLs
websites = {
    'youtube': 'https://www.youtube.com',
    'wikipedia': 'https://www.wikipedia.org',
    'google': 'https://www.google.com',
    'facebook': 'https://www.facebook.com',
    'twitter': 'https://www.twitter.com',
    'github': 'https://www.github.com',
    'reddit': 'https://www.reddit.com',
    'linkedin': 'https://www.linkedin.com',
    'instagram': 'https://www.instagram.com',
    'amazon': 'https://www.amazon.com',
    'netflix': 'https://www.netflix.com',
    'stackoverflow': 'https://stackoverflow.com',
    'quora': 'https://www.quora.com',
    'bing': 'https://www.bing.com',
    'yahoo': 'https://www.yahoo.com',
    'apple': 'https://www.apple.com',
    'microsoft': 'https://www.microsoft.com',
    'spotify': 'https://www.spotify.com',
    'adobe': 'https://www.adobe.com',
    'medium': 'https://www.medium.com',
    'nytimes': 'https://www.nytimes.com',
    'bbc': 'https://www.bbc.com',
    'cnn': 'https://www.cnn.com',
    'dropbox': 'https://www.dropbox.com',
    'drive': 'https://drive.google.com',
    'weather': 'https://www.weather.com',
    'hulu': 'https://www.hulu.com',
    'pinterest': 'https://www.pinterest.com',
    'tumblr': 'https://www.tumblr.com',
    'whatsapp': 'https://www.whatsapp.com',
    'slack': 'https://www.slack.com',
    'zoom': 'https://www.zoom.us',
    'skype': 'https://www.skype.com',
    'trello': 'https://www.trello.com',
    'airbnb': 'https://www.airbnb.com',
    'booking': 'https://www.booking.com',
    'expedia': 'https://www.expedia.com',
    'uber': 'https://www.uber.com',
    'lyft': 'https://www.lyft.com',
    'doordash': 'https://www.doordash.com',
    'grubhub': 'https://www.grubhub.com',
    'yelp': 'https://www.yelp.com',
    'zillow': 'https://www.zillow.com',
    'indeed': 'https://www.indeed.com',
    'glassdoor': 'https://www.glassdoor.com',
    'monster': 'https://www.monster.com',
    'craigslist': 'https://www.craigslist.org',
    'etsy': 'https://www.etsy.com',
    'shopify': 'https://www.shopify.com',
    'bestbuy': 'https://www.bestbuy.com',
    'homedepot': 'https://www.homedepot.com',
    'walmart': 'https://www.walmart.com',
    'target': 'https://www.target.com',
    'costco': 'https://www.costco.com',
    'ikea': 'https://www.ikea.com',
    'nasa': 'https://www.nasa.gov',
    'spacex': 'https://www.spacex.com',
    'ted': 'https://www.ted.com',
    'coursera': 'https://www.coursera.org',
    'edx': 'https://www.edx.org',
    'khanacademy': 'https://www.khanacademy.org',
    'udemy': 'https://www.udemy.com',
    'codecademy': 'https://www.codecademy.com',
    'pluralsight': 'https://www.pluralsight.com',
    'udacity': 'https://www.udacity.com',
    'lynda': 'https://www.lynda.com',
    'hootsuite': 'https://www.hootsuite.com',
    'buffer': 'https://www.buffer.com',
    'canva': 'https://www.canva.com',
    'dribbble': 'https://www.dribbble.com',
    'behance': 'https://www.behance.net',
    'flickr': 'https://www.flickr.com',
    'vimeo': 'https://www.vimeo.com',
    'dailymotion': 'https://www.dailymotion.com',
    'soundcloud': 'https://www.soundcloud.com',
    'bandcamp': 'https://www.bandcamp.com',
    'lastfm': 'https://www.last.fm',
    'pandora': 'https://www.pandora.com',
    'twitch': 'https://www.twitch.tv',
    'hbr': 'https://hbr.org',
    'bloomberg': 'https://www.bloomberg.com',
    'forbes': 'https://www.forbes.com',
    'wired': 'https://www.wired.com',
    'techcrunch': 'https://www.techcrunch.com',
    'engadget': 'https://www.engadget.com',
    'thenextweb': 'https://www.thenextweb.com',
    'mashable': 'https://www.mashable.com',
    'gizmodo': 'https://www.gizmodo.com',
    'lifehacker': 'https://www.lifehacker.com',
    'theverge': 'https://www.theverge.com',
    'cnet': 'https://www.cnet.com',
    'arstechnica': 'https://www.arstechnica.com',
    '9to5mac': 'https://www.9to5mac.com',
    'macrumors': 'https://www.macrumors.com',
    'anandtech': 'https://www.anandtech.com',
    'pcmag': 'https://www.pcmag.com',
    'tomshardware': 'https://www.tomshardware.com',
    'ign': 'https://www.ign.com',
    'gamespot': 'https://www.gamespot.com',
    'kotaku': 'https://www.kotaku.com',
    'polygon': 'https://www.polygon.com',
    'gamefaqs': 'https://www.gamefaqs.com',
    'gog': 'https://www.gog.com',
    'humblebundle': 'https://www.humblebundle.com',
    'steam': 'https://store.steampowered.com',
    'epicgames': 'https://www.epicgames.com',
    'bbcgoodfood': 'https://www.bbcgoodfood.com',
    'allrecipes': 'https://www.allrecipes.com',
    'foodnetwork': 'https://www.foodnetwork.com',
    'healthline': 'https://www.healthline.com',
    'webmd': 'https://www.webmd.com',
    'mayoclinic': 'https://www.mayoclinic.org',
    'nih': 'https://www.nih.gov',
    'cdc': 'https://www.cdc.gov',
    'who': 'https://www.who.int',
    'psychologytoday': 'https://www.psychologytoday.com',
    'medlineplus': 'https://medlineplus.gov',
    'goodreads': 'https://www.goodreads.com',
    'bookdepository': 'https://www.bookdepository.com',
    'projectgutenberg': 'https://www.gutenberg.org',
    'archive': 'https://archive.org',
    'jstor': 'https://www.jstor.org',
    'scihub': 'https://sci-hub.se',
    'researchgate': 'https://www.researchgate.net',
    'nature': 'https://www.nature.com',
    'sciencedirect': 'https://www.sciencedirect.com',
    'arxiv': 'https://arxiv.org',
    'springer': 'https://link.springer.com',
    'pnas': 'https://www.pnas.org',
    'bbcnews': 'https://www.bbc.com/news',
    'aljazeera': 'https://www.aljazeera.com',
    'reuters': 'https://www.reuters.com',
    'apnews': 'https://apnews.com',
    'theguardian': 'https://www.theguardian.com',
    'washingtonpost': 'https://www.washingtonpost.com',
    'latimes': 'https://www.latimes.com',
    'npr': 'https://www.npr.org',
    'axios': 'https://www.axios.com',
    'buzzfeed': 'https://www.buzzfeed.com',
    'usatoday': 'https://www.usatoday.com',
    'time': 'https://time.com',
    'newyorker': 'https://www.newyorker.com',
    'vanityfair': 'https://www.vanityfair.com',
    'nationalgeographic': 'https://www.nationalgeographic.com',
    'people': 'https://people.com',
    'tmz': 'https://www.tmz.com',
    'perezhilton': 'https://perezhilton.com',
    'eonline': 'https://www.eonline.com',
    'rottentomatoes': 'https://www.rottentomatoes.com',
    'imdb': 'https://www.imdb.com',
    'metacritic': 'https://www.metacritic.com',
    'letterboxd': 'https://letterboxd.com',
    'fandango': 'https://www.fandango.com',
    'moviefone': 'https://www.moviefone.com',
    'amctheatres': 'https://www.amctheatres.com',
    'cinemark': 'https://www.cinemark.com',
    'regmovies': 'https://www.regmovies.com'
}


# Function to open applications
def open_application(app_name):
    try:
        if platform.system() == 'Windows':
            command = applications.get(app_name.lower())
            if command:
                subprocess.Popen([command])
                return f"Opening {app_name}"
            else:
                return "Application not recognized"
        else:
            return "This functionality is currently only supported on Windows."
    except Exception as e:
        return f"Error opening {app_name}: {str(e)}"

# Function to listen for voice commands
def listen_for_voice_command():
    with mic as source:
        print("Listening for a command...")
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio)
        print(f"Recognized command: {command}")
        return command
    except sr.UnknownValueError:
        print("Sorry, I did not understand that.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return None

# Function to chat with OpenAI
def chat(query):
    global chatStr
    openai.api_key = apikey

    # Predefined responses for greetings
    greetings = {
        "hi": "Hello! How are you doing?",
        "hello": "Hi there! How can I assist you today?",
        "hey": "Hey! What's up?",
        "good morning": "Good morning! How can I help you?",
        "good afternoon": "Good afternoon! What can I do for you?",
        "good evening": "Good evening! How can I assist you?",
        "how are you": "I'm just a program, but I'm here to help you! How can I assist you today?"
    }

    if query.lower() in greetings:
        response = greetings[query.lower()]
        print(response)
        say(response)
        return response
    chatStr += f"User: {query}\nAI: "
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=chatStr,
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    reply = response["choices"][0]["text"].strip()
    chatStr += f"{reply}\n"
    print({reply})
    say(reply)
    return reply

# Function to handle OpenAI API requests
def ai(prompt):
    text = f"OpenAI response for Prompt: {prompt}\n\n"

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    text += response["choices"][0]["text"].strip()
    if not os.path.exists("Openai"):
        os.mkdir("Openai")

    with open(f"Openai/{prompt.replace(' ', '_')}.txt", "w") as f:
        f.write(text)
def schedule_appointment(date_time, details):
    global appointments
    appointment = {"date_time": date_time, "details": details}
    appointments.append(appointment)
    with open("appointments.json", "w") as f:
        json.dump(appointments, f)
    return "Appointment scheduled."

def load_appointments():
    global appointments
    if os.path.exists("appointments.json"):
        with open("appointments.json", "r") as f:
            appointments = json.load(f)

def provide_recommendations():
    # Simple recommendation logic
    recommendations = [
        "Read a book on AI",
        "Watch a movie on Netflix",
        "Try out a new recipe",
        "Go for a walk in the park",
        "Listen to a new podcast"
    ]
    recommendation = random.choice(recommendations)
    print(f"I recommend you to {recommendation}")
    say(f"I recommend you to {recommendation}.")
    return recommendation

# Function to convert text to speech
def say(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

if __name__ == '__main__':
    print('Welcome to Jarvis A.I')
    say("Jarvis AI")

    while True:
        input_type = input("Enter 'voice' to use voice commands or 'text' to type your commands: ").strip().lower()

        while True:
            if input_type == 'voice':
                print("Listening...")
                query = listen_for_voice_command()
            elif input_type == 'text':
                query = input("Please enter your command: ").strip()
            else:
                print("Invalid input type. Please enter 'voice' or 'text'.")
                break  # Exit the inner loop to ask for input type again

            if query is None:
                continue

            # Check if the user wants to change the input method
            if "change input" in query.lower():
                print("Changing input method.")
                say("Changing input method.")
                break  # Exit the inner loop to ask for input type again

            # Handle specific voice commands
            if "open" in query.lower():
                site_found = False
                for site, url in websites.items():
                    if f"open {site}".lower() in query.lower():
                        print(f"Opening {site}")
                        say(f"Opening {site}")
                        webbrowser.open(url)
                        site_found = True
                        break
                if not site_found:
                    app_name = query.lower().replace('open ', '')
                    response = open_application(app_name)
                    print({response})
                    say(response)

            elif "the time" in query.lower():
                now = datetime.datetime.now()
                print(f"The time is {now.strftime('%H:%M')}")
                say(f"Sir, the time is {now.strftime('%H:%M')}")

            elif "the date" in query.lower():
                now = datetime.datetime.now()
                print(f"Today's date is {now.strftime('%Y-%m-%d')}")
                say(f"Sir, today's date is {now.strftime('%Y-%m-%d')}")

            elif "the date and time" in query.lower():
                now = datetime.datetime.now()
                print(f"today's date is {now.strftime('%Y-%m-%d')} and the time is {now.strftime('%H:%M')}")
                say(f"Sir, today's date is {now.strftime('%Y-%m-%d')} and the time is {now.strftime('%H:%M')}")
            elif "using artificial intelligence" in query.lower():
                ai(prompt=query)
            elif "schedule appointment" in query.lower():
                try:
                    print("Please provide the date and time for the appointment.")
                    say("Please provide the date and time for the appointment.")
                    date_time = listen_for_voice_command()
                    print("Please provide the details for the appointment.")
                    say("Please provide the details for the appointment.")
                    details = listen_for_voice_command()
                    response = schedule_appointment(date_time, details)
                    print({response})
                    say(response)
                except Exception as e:
                    print("Sorry, I couldn't schedule the appointment.")
                    say("Sorry, I couldn't schedule the appointment.")
                    print(f"Error: {e}")

            elif "recommend" in query.lower():
                response = provide_recommendations()
            elif "jarvis quit" in query.lower():
                print("Goodbye sir.")
                say("Goodbye, sir.")
                exit()
            else:
                print("Chatting...")
                chat(query)
