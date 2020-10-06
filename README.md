# Pyro
Pyro is supposed to be a short sharp coded bot to help the MenuDocs community with python and discord.py related issues. Therefore, it is going to have features that aid the menudocs python developers to understand python better, such as quizzes that ask for common knowledge in both python and discord.py

# Installation
**Python 3.8 is required**

Run `git clone https://github.com/MenuDocs/Pyro`.
To install the requirements for the bot, run `python3.8 -m pip install -r requirements.txt` inside the bot's directory.

# Setup
The bot expects there to be a configuration file named `config.json` to grab multiple values from, formatted this way:
```json
{
  "token": "YOUR TOKEN",
  "menudocs_projects_id": 12345,
  "story_channel_id": 12345,
  "discord.py_help_channel": 12345,
  "mongo_url": "THE URL TO ACCESS THE MONGODB DATABASE "
}
```

Mind that the fields that have `id` in their name need an actual ID as the value.

with that inside the bot's directory, running `python3.8 main.py` should run the bot without any problem, if the ID's are valid.
