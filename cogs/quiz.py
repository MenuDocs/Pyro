import discord
from discord.ext import commands
from utils.util import clean_code

import logging
import random
import asyncio
import aiohttp


class Choices:
    def __init__(self, question, answers, timeout=15.0):
        self.question = question
        self.answers = answers
        self.timeout = timeout

        self.result = None

    async def start(self, ctx):
        embed = discord.Embed(
            title=self.question,
            description="\n".join(
                f"{i+1}: {q}" for i, q in enumerate(self.answers)
            )
        )

        msg = await ctx.send(embed=embed)

        answers_dict = {}

        for i, _ in enumerate(self.answers):
            answers_dict[f"{i+1}️⃣"] = i
            await msg.add_reaction(f"{i+1}️⃣")
        await msg.add_reaction("\N{CROSS MARK}")

        try:
            ans = await ctx.bot.wait_for(
                "reaction_add",
                check=lambda react, user: react.message.id == msg.id and
                user.id == ctx.author.id,
                timeout=self.timeout
            )

            if str(ans[0]) not in answers_dict:
                return

            self.result = answers_dict[str(ans[0])]
        except asyncio.TimeoutError:
            return

        await msg.delete()
        return self.result


# TODO: Implement class for quiz questions that require code from author.

class Quiz(commands.Cog, name="Quiz"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    async def predicate(self, ctx, code, result, errors):
        if not code:
            await ctx.send("Please send some code!")
            return

        if errors:
            await ctx.send(f"You have some errors!\n`{errors}`")


    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.command()
    @commands.dm_only()
    async def quiz(self, ctx):
        questions = await self.bot.quiz.get_all()
        questions.sort(key=lambda d: int(d["_id"]))
        user_answers = {}

        for item in questions:
            answers = item["otherAnswers"]
            answers.append(item["correctAnswer"])
            random.shuffle(answers)

            index = await Choices(item["question"], answers).start(ctx)
            if not index:
                await ctx.send("Cancelled quiz.")
                return

            user_answers[item["_id"]] = answers[index]

        total_correct = 0
        wrong_questions = {}
        for item in questions:
            ans = user_answers[item["_id"]]
            if ans == item["correctAnswer"]:
                total_correct += 1
            else:
                wrong_questions[item["_id"]] = [item, ans]

        embed = discord.Embed(
            title="Python choices quiz",
            description=f"You answered {total_correct} questions out " +
            f"of {len(questions)} correctly.\n" +
                        (
                            "Here are your incorrect answers:"
                            if not wrong_questions else
                            ""
                        )
        )

        for key, value in wrong_questions.items():
            embed.add_field(
                name=value[0]["question"],
                value=f"Your answer: `{value[1]}`.\n Correct answer: "
                      f"{value[0]['correctAnswer']}",
                inline=False
            )
        await ctx.send(embed=embed)

        # TODO: Add stage 2 using snekbox.


def setup(bot):
    bot.add_cog(Quiz(bot))
