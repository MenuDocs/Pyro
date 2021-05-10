# Pyro
Pyro is supposed to be a short sharp coded bot to help the MenuDocs community with python and discord.py related issues. Therefore, it is going to have features that aid the menudocs python developers to understand python better, such as quizzes that ask for common knowledge in both python and discord.py

# Installation
**Python 3.8 is required**

```shell
> git clone https://github.com/MenuDocs/Pyro

> docker-compose build

> docker-compose up
```


# Setup
The bot expects there to be a configuration file named `docker-compose.override.yml` to grab multiple values from, formatted this way:
```docker
services:
  pyro:
    environment:
      - TOKEN="Your token here"
      - MONGO="Your connection string here"
```