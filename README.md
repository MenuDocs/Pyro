# Pyro
Pyro is supposed to be a short sharp coded bot to help the MenuDocs community with python and discord.py related issues. Therefore, it is going to have features that aid the menudocs python developers to understand python better, such as quizzes that ask for common knowledge in both python and discord.py


## Installation

Bundled with Mongo (Not yet)
```shell
- docker-compose build
- docker-compose up
```

Without:
```shell
- docker build . -t pyro:latest
- docker run pyro:latest
```

## Environment Variables

`TOKEN` - Your bot token
`MONGO` - Your mongodb connection url (Not required for docker-compose)

## Development

This will run both Pyro and the required MongoDB config.
You can view `pyro/checks/basic.py` if you require things during development.

```shell
- docker-compose build
- docker-compose up
```