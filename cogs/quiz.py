import random
import asyncio
import logging

from utils.util import clean_code

import aiohttp
import discord
from discord.ext import commands


class Choices:
    """
    This class is supposed to represent part 1 of the quiz,
    which concerns asking questions to the user and giving them
    choices to pick from, the bot will check against some already
    stored answer.
    """

    def __init__(self, question, answers, timeout=30):
        self.question = question
        self.answers = answers
        self.timeout = timeout

        self.result = None

    async def start(self, ctx):
        embed = discord.Embed(
            title=self.question,
            description="\n".join(f"{i+1}: {q}" for i, q in enumerate(self.answers)),
        )

        msg = await ctx.send(embed=embed)

        answers_dict = {}

        # This for loop is to automate the addition of the reactions
        # Using the box emote.
        for i, _ in enumerate(self.answers):
            answers_dict[f"{i+1}️⃣"] = i
            await msg.add_reaction(f"{i+1}️⃣")
        await msg.add_reaction("\N{CROSS MARK}")

        try:
            ans = await ctx.bot.wait_for(
                "reaction_add",
                check=lambda react, user: react.message.id == msg.id
                and user.id == ctx.author.id,
                timeout=self.timeout,
            )

            # This tries to check if the number in the emoji that
            # was reacted by the user is in the dictionary that has
            # the answers, this works because the "syntax" of the
            # emote is "num⃣", num being the number of the choice.
            # Of course, any other emoji will probably fail.
            # Probably.
            if str(ans[0]) not in answers_dict:
                self.result = False
            else:
                self.result = answers_dict[str(ans[0])]
        except asyncio.TimeoutError:
            self.result = False

        await msg.delete()
        return self.result


class CodeQuiz:
    """
    This class is supposed to start the stage 2 of the Quiz,
    which concerns asking for code from the user and checking if it
    matches some given code from the database.
    """

    def __init__(self, timeout):
        self.timeout = timeout

    async def start(self, ctx):
        # sort the questions by ID, in this context, ID is the order
        # of the questions.
        code_ques = sorted(await ctx.bot.code.get_all(), key=lambda d: d["_id"])

        for ques in code_ques:
            await ctx.send(ques["question"])
            async with aiohttp.ClientSession() as session:
                async with session.get(ques["bin"]) as resp:
                    code = await resp.text()

            try:
                msg = await ctx.bot.wait_for(
                    "message",
                    check=lambda m: m.channel.id == ctx.channel.id
                    and m.author.id == ctx.author.id,
                    timeout=self.timeout,
                )

                content = clean_code(msg.content)
                # Replace tabs with spaces.
                content = content.replace("\t", "    ")
                # This line is supposed to clear empty lines in the
                # User's code, this is to give as much lee-way as
                # Possible with code formatting.
                # Of course, because of that, the code in the
                # database must nkt have any blank lines.
                content = "\n".join([text for text in content.split("\n") if text])

                if not content == code:
                    await ctx.send(
                        "Sorry, but that isn't what we're looking for! Let's see the next one!"
                    )
                    continue
                else:
                    await ctx.send("Great! That looks good! Let's see the next one...")
                    continue
            except asyncio.TimeoutError:
                await ctx.send("Whoops! You ran out of time.")
                return
        await ctx.send("Whoa! You're all done!")


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
        """Quiz yourself on relevant Python knowledge!"""
        questions = await self.bot.quiz.get_all()
        questions.sort(key=lambda d: int(d["_id"]))
        user_answers = {}

        for item in questions:
            answers = item["otherAnswers"]
            answers.append(item["correctAnswer"])
            random.shuffle(answers)

            index = await Choices(item["question"], answers).start(ctx)
            if index is False:
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
            description=f"Starting stage 2.\nYou answered {total_correct} questions out "
            + f"of {len(questions)} correctly.\n"
            + ("Here are your incorrect answers:" if wrong_questions != {} else ""),
        )

        for key, value in wrong_questions.items():
            embed.add_field(
                name=value[0]["question"],
                value=f"Your answer: `{value[1]}`.\n Correct answer: "
                f"`{value[0]['correctAnswer']}`",
                inline=False,
            )
        await ctx.send(embed=embed)

        await ctx.send("Please send `confirm` to move on to the next stage.")

        try:
            msg = await self.bot.wait_for(
                "message",
                check=lambda m: m.channel.id == ctx.channel.id
                and m.author.id == ctx.author.id,
                timeout=60,
            )

            if msg.content.lower() == "confirm":
                await msg.add_reaction("👌")
            else:
                return
        except asyncio.TimeoutError:
            await ctx.send("Sounds like you're busy! You didn't answer fast enough.")

        await ctx.send(
            "Please note, all code should be in accordance with PEP8.\n"
            "You can find it here <https://www.python.org/dev/peps/pep-0008/>\n"
            "For simpler adhering, use this tool: <https://pypi.org/project/black/>"
        )

        code_quiz = CodeQuiz(210)  # 3 minutes and a half
        await code_quiz.start(ctx)
        await ctx.send("Alright! This whole quiz is over! Thanks for trying it!")


def setup(bot):
    bot.add_cog(Quiz(bot))
