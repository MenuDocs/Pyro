from json import load
from logging import basicConfig, getLogger
from os import listdir
from re import compile as re_compile

from discord import Game, Intents
from discord.ext.commands import Bot, command, is_owner, when_mentioned_or
from motor.motor_asyncio import AsyncIOMotorClient

from utils import exceptions
from utils.mongo import Document
from utils.util import Pag, clean_code

with open('config.json', 'r') as f:
    config = load(f)

basicConfig(level='INFO')
mention = re_compile(r"^<@!?(?P<id>\d+)>$")


class Pyro(Bot):

    def __init__(self):
        intents = Intents.none()
        intents.messages = True
        intents.guilds = True
        intents.members = True
        intents.emojis = True

        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=True,
            description=(
                'A short sharp bot coded in Python to aid the Python '
                'developers in helping the community '
                'with "discord.py" related issues.'
            ),
            help_command=None,
            intents=intents
        )

        self.logger = getLogger(__name__)
        self.DEFAULTPREFIX = 'py.'

        # Required for `self.get_prefix` to remain exactly how it was written.
        # See `self.get_prefix` for alternative.
        self.config = self.mongo('config')

    async def on_ready(self):
        activity = Game(name='py.help')
        await self.change_presence(activity=activity)

        self.logger.info("I'm all up and ready like mom's spaghetti")

        try:
            await self.config.get_all()
        except exceptions.PyMongoError as error:
            log = 'An error occured while fetching the config: %s' % error
            self.logger.error(log)
        else:
            self.logger.info('Database connection established.')

    async def on_message(self, message):
        # Ignore messages sent by bots.
        if message.author.bot:
            return None

        guild_id = message.guild.id

        if message.guild:
            try:
                guild_config = await self.config.find(guild_id)
                if message.channel.id in guild_config['ignored_channels']:
                    return None
            except (exceptions.IdNotFound, KeyError):
                pass
        # Whenever the bot is tagged, respond with its prefix
        if match := mention.match(message.content):
            if int(match.group('id')) == (self.user.id):
                data = await self.config._Document__get_raw(guild_id)
                if (not data) or ('prefix' not in data):
                    prefix = self.DEFAULTPREFIX
                else:
                    prefix = data['prefix']

                content = 'My prefix here is `%s`' % (prefix)
                await message.channel.send(content, delete_after=15)

        await self.process_commands(message)

    def mongo(self, collection):
        """Solution for needing to restart the bot each time a new collection
        needs to be created.

        This way you just call this method and create the instance
        of the collection when you need it in the Cog.

        Usage
        -----
        ```python
        from discord.ext.commands import Cog


        class UsageExample(Cog):
            def __init__(self, bot):
                self.bot = bot
                self.starboard = self.bot.mongo('starboard')

                # Now just replace:
                # `self.bot.starboard` -> `self.starboard`
                # With VSCode it's easy, just highlight and hit `CTRL + F2`.

        ```

        Returns connection to collection as an instance of :class: Document.
        """

        db = AsyncIOMotorClient(config['mongo_url']).pyro
        return Document(db, collection)

    def load_cogs(self, path):

        extensions = [
            ext for ext
            in listdir(path)
            if not ext.startswith('_')
            and ext.endswith('.py')
        ]

        for extension in extensions:

            dot_format = (
                path
                .replace('\\', '/')
                .replace('/', '.')
                .strip('.')
                + '.'
            )

            name = dot_format + extension[:3]

            self.bot.load_extension(name=name)

    @staticmethod
    async def get_prefix(bot, message):
        # If private message:
        if not message.guild:
            return when_mentioned_or(bot.DEFAULTPREFIX)(bot, message)

        try:
            # Could be rewritten to be:
            # data = await bot.mongo('config').find(message.guild.id)
            data = await bot.config.find(message.guild.id)

            # Make sure we have a usable prefix:
            if (not data) or ('prefix' not in data):
                return when_mentioned_or(bot.DEFAULTPREFIX)(bot, message)

            return when_mentioned_or(data['prefix'])(bot, message)

        except exceptions.IdNotFound:
            return when_mentioned_or(bot.DEFAULTPREFIX)(bot, message)

    def run(self):
        return super().run(config['token'])


if __name__ == '__main__':

    bot = Pyro()
    bot.load_cogs('./cogs')
    bot.run()
