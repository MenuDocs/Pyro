import asyncio
import logging
import random
from string import Template

import discord
from discord.ext import commands

from utils.enums import Winner
from utils.tictactoe import TicTacToe, InvalidMove


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    async def display_board(self, messageable, game, *, content=None):
        board = game.board
        desc = f"""
        ```yaml
          1|2|3
        1|{board[0][0].to_piece()}|{board[0][1].to_piece()}|{board[0][2].to_piece()}
        2|{board[1][0].to_piece()}|{board[1][1].to_piece()}|{board[1][2].to_piece()}
        3|{board[2][0].to_piece()}|{board[2][1].to_piece()}|{board[2][2].to_piece()}
        ```
        """

        embed = discord.Embed(
            title=f"TicTacToe ({game.player_one.display_name} VS {game.player_two.display_name})",
            description=desc,
        )
        await messageable.edit(content=content, embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.command(aliases=["ttt"])
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.guild_only()
    async def tictactoe(self, ctx, player_two: discord.Member = None):
        def check(m):
            return m.channel == ctx.channel and m.author == current_player

        def react_check(payload):
            return (
                payload.message_id == difficulty_message.id
                and payload.user_id == ctx.author.id
                and str(payload.emoji) in ["1️⃣", "2⃣"]
            )

        is_bot = False
        difficulty = 1
        if not player_two or player_two == ctx.guild.me:
            player_two = ctx.guild.me
            is_bot = True

            embed = discord.Embed(
                title="Please pick a difficulty",
                description=":one: - Easy\n:two: - Hard",
            )

            difficulty_message = await ctx.send(embed=embed)
            await difficulty_message.add_reaction("1️⃣")
            await difficulty_message.add_reaction("2⃣")

            try:
                payload = await self.bot.wait_for(
                    "raw_reaction_add", check=react_check, timeout=25
                )
            except asyncio.TimeoutError:
                await ctx.send("I picked hard on your behalf :)")
            else:
                if str(payload.emoji) == "1️⃣":
                    difficulty = 2.5
                    await ctx.send("Set difficulty to easy", delete_after=10)
                else:
                    await ctx.send("Set difficulty to hard", delete_after=10)
            finally:
                await difficulty_message.delete()

        m = await ctx.send("Starting game!")

        game = TicTacToe(
            player_one=ctx.author,
            player_two=player_two,
            is_agaisnt_computer=is_bot,
            difficulty=difficulty,
        )

        player_one_start = random.choice([True, False])
        if not player_one_start:
            await game.flip_player()

        await self.display_board(m, game)

        while (winner := await game.is_over()) == Winner.NO_WINNER:
            current_player = ctx.author if game.is_player_one_move else player_two

            if not game.is_player_one_move and is_bot:
                await self.display_board(
                    m,
                    game,
                    content=f"{current_player.mention}, please pick where you wish to play in the format `row column`",
                )
                await game.ai_turn()
                await asyncio.sleep(random.randrange(0, 5))
                continue

            try:
                await self.display_board(
                    m,
                    game,
                    content=f"{current_player.mention}, please pick where you wish to play in the format `row column`",
                )
                msg = await self.bot.wait_for("message", check=check, timeout=25)
            except asyncio.TimeoutError:
                await game.flip_player()
                await ctx.send(f"{current_player.mention}, you missed your turn!")
            else:
                content = msg.content

                await msg.delete()

                if not len(content) == 3:
                    await ctx.send(
                        f"{current_player.mention}, Invalid move sequence, please see the format and try again",
                        delete_after=10,
                    )
                    continue

                row, column = content.split()
                try:
                    await game.make_move(row, column)
                except InvalidMove:
                    await ctx.send(
                        f"{current_player.mention}, illegal move sequence, please try again",
                        delete_after=10,
                    )
                    continue

        content = Template(str(winner)).safe_substitute(
            {"MENTIONONE": ctx.author.mention, "MENTIONTWO": player_two.mention}
        )
        await self.display_board(m, game, content=content)


def setup(bot):
    bot.add_cog(Games(bot))
