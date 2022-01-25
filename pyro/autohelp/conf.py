from typing import Dict


class Conf:
    def __init__(
        self,
        on_message_process_commands_link: str,
        context_link: str,
        interaction_link: str,
    ):
        self.context_link: str = context_link
        self.interaction_link: str = interaction_link
        self.on_message_process_commands_link: str = on_message_process_commands_link


default_conf = Conf(
    on_message_process_commands_link="https://nextcord.readthedocs.io/en/latest/faq.html"
    "?highlight=frequently#why-does-on-message-make-my-commands-stop-working",
    context_link="https://nextcord.readthedocs.io/en/latest/ext/commands/api.html#nextcord.ext.commands.Context",
    interaction_link="https://nextcord.readthedocs.io/en/latest/api.html#nextcord.Interaction",
)
disnake_conf = Conf(
    on_message_process_commands_link="https://docs.disnake.dev/en/latest/faq.html"
    "?highlight=frequently#why-does-on-message-make-my-commands-stop-working",
    context_link="https://docs.disnake.dev/en/latest/ext/commands/api.html"
    "?highlight=context#disnake.ext.commands.Context",
    interaction_link="https://docs.disnake.dev/en/latest/api.html?highlight=interaction#disnake.Interaction",
)

AUTO_HELP_CONF: Dict[int, Conf] = {
    -1: default_conf,
    808030843078836254: disnake_conf,
}
