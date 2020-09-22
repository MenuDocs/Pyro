import random
import asyncio
import logging

from utils.util import clean_code

import aiohttp
import discord
from discord.ext import commands


class Choices:
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

            if str(ans[0]) not in answers_dict:
                self.result = False
            else:
                self.result = answers_dict[str(ans[0])]
        except asyncio.TimeoutError:
            self.result = False

        await msg.delete()
        return self.result


class CodeQuiz:
    def __init__(self, timeout):
        self.timeout = timeout

    async def start(self, ctx):
        code_ques = sorted(
            await ctx.bot.code.get_all(),
            key=lambda d: d["_id"]
        )

        for ques in code_ques:
            await ctx.send(ques["question"])
            async with aiohttp.ClientSession() as session:
                async with session.get(ques["bin"]) as resp:
                    code = await resp.text()

            try:
                msg = await ctx.bot.wait_for(
                    'message',
                    check=lambda m: m.channel.id == ctx.channel.id
                    and m.author.id == ctx.author.id,
                    timeout=self.timeout
                )

                content = clean_code(msg.content)
                content = content.replace("\t", "    ")
                content = "\n".join([text for text in content.split("\n") if text])

                if not content == code:
                    await ctx.send("Sorry, but that isn't what we're looking for! Let's see the next one!")
                    return
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
                f"{value[0]['correctAnswer']}",
                inline=False,
            )
        await ctx.send(embed=embed)

        await ctx.send("Please send `confirm` to move on to the jext stage.")

        try:
            msg = await self.bot.wait_for(
                'message',
                check=lambda m: m.channel.id == ctx.channel.id
                and m.author.id == ctx.author.id,
                timeout=60
            )

            if msg.content.lower() == 'confirm':
                await msg.add_reaction("👌")
            else:
                return
        except asyncio.TimeoutError:
            await ctx.send("Sounds like you're busy! You didn't answer fast enough.")

        code_quiz = CodeQuiz(210)  # 3 minutes and a half
        await code_quiz.start(ctx)
        await ctx.send("Alright! This whole quiz is over! Thanks for trying it!")


def setup(bot):
    bot.add_cog(Quiz(bot))
