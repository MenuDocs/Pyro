import contextlib
import io
import textwrap
from traceback import format_exception

import tanjun

from utils.util import clean_code

component = tanjun.Component()


@component.with_message_command
@tanjun.as_message_command("logout")
async def logout(ctx: tanjun.MessageContext):
    await ctx.respond("Cya :wave:")
    await ctx.client.shards.close()  # noqa


@component.with_message_command
@tanjun.with_argument("code")
@tanjun.with_parser
@tanjun.as_message_command("eval")
async def _eval(ctx: tanjun.MessageContext, code: str):
    """
    Evaluates given code.
    """
    code = clean_code(code)

    channel = ctx.get_channel()
    guild = ctx.get_guild()
    local_variables = {
        "bot": ctx.client.shards,
        "ctx": ctx,
        "channel": channel,
        "author": ctx.author,
        "guild": guild,
        "message": ctx.message,
    }

    stdout = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout):
            exec(
                f"async def func():\n{textwrap.indent(code, '    ')}",
                local_variables,
            )

            obj = await local_variables["func"]()
            result = f"{stdout.getvalue()}\n-- {obj}\n"

    except Exception as e:
        result = "".join(format_exception(e, e, e.__traceback__))

    await ctx.respond(result)


@tanjun.as_loader
def load_examples(client: tanjun.abc.Client) -> None:
    client.add_component(component.copy())
