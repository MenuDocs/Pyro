import asyncio
import difflib
import logging
import random

from utils.exceptions import IdNotFound
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
        self.logger = logging.getLogger(__name__)

    async def start(self, ctx):
        # sort the questions by ID, in this context, ID is the order
        # of the questions.
        correct_answers = dict()
        code_ques = sorted(await ctx.bot.code.get_all(), key=lambda d: d["_id"])

        for ques in code_ques:
            ques_id = ques["_id"]

            await ctx.send(ques["question"])
            async with aiohttp.ClientSession() as session:
                async with session.get(ques["bin"]) as resp:
                    code = await resp.text()
                    code = code.replace("\t", "    ").replace("\r\n", "\n")

            try:
                msg = await ctx.bot.wait_for(
                    "message",
                    check=lambda m: m.channel.id == ctx.channel.id
                    and m.author.id == ctx.author.id,
                    timeout=self.timeout,
                )

                content = clean_code(msg.content)
                # Replace tabs with spaces.
                content = content.replace("\t", "    ").replace("\r\n", "\n")
                # This line is supposed to clear empty lines in the
                # User's code, this is to give as much lee-way as
                # Possible with code formatting.
                # Of course, because of that, the code in the
                # database must not have any blank lines.
                content = "\n".join([text for text in content.split("\n") if text])

                if not content == code:
                    self.logger.info(
                        "\n".join(
                            [li for li in difflib.ndiff(content, code) if li[0] != " "]
                        )
                    )
                    await ctx.send(
                        "Sorry, but that isn't what we're looking for! Remember that Python and the way we're "
                        "detecting code needs you to be accurate with your capitalization as well! "
                        "Make sure you're using correct python conventions and grammar. "
                        "Let's see the next one!"
                    )
                    correct_answers[ques_id] = False
                    continue
                else:
                    await ctx.send("Great! That looks good! Let's see the next one...")
                    correct_answers[ques_id] = True
                    continue
            except asyncio.TimeoutError:
                await ctx.send("Whoops! You ran out of time.")
                correct_answers[ques_id] = False
                return
        await ctx.send("Whoa! You're all done!")
        return correct_answers


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

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def quiz(self, ctx):
        """Quiz yourself on relevant Python knowledge!"""
        guild = ctx.guild
        try:
            quiz_role = await self.bot.config.find(ctx.guild.id)
            quiz_role = quiz_role.get("quiz_role")
        except IdNotFound:
            quiz_role = None

        await ctx.send("Quiz started in your DMs!")
        msg = await ctx.author.send("Do you still want to take the quiz? [yes/no]")

        try:
            msg = await self.bot.wait_for(
                "message",
                check=lambda m: m.channel.id == msg.channel.id
                and m.author.id == ctx.author.id,
                timeout=60,
            )

            if msg.content.lower() != "yes":
                return
            ctx = await self.bot.get_context(msg)

        except asyncio.TimeoutError:
            await ctx.author.send(
                "Well... A bit too slow there, pal. Better luck next time!"
            )
            return

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
            return

        await ctx.send(
            "Please note, all code should be in accordance with PEP8.\n"
            "You can find it here <https://www.python.org/dev/peps/pep-0008/>\n"
            "For simpler adhering, use this tool: <https://pypi.org/project/black/>"
        )

        code_quiz = CodeQuiz(210)  # 3 minutes and a half
        correct_answers = await code_quiz.start(ctx)
        await ctx.send("Alright! This whole quiz is over! Thanks for trying it!")
        correct_choices = total_correct == len(questions)

        if all(correct_answers.values()) and correct_choices:
            try:
                member = await guild.fetch_member(ctx.author.id)
            except discord.HTTPException:
                self.logger.error(
                    f"Failed to fetch {ctx.author.display_name}({ctx.author.id}) from guild {guild.name}{guild.id}"
                )
            else:
                if quiz_role:
                    if quiz_role in member.roles:
                        await ctx.send("You already have the quiz role!")
                        return

                    quiz_role = guild.get_role(quiz_role)
                    await member.add_roles(
                        quiz_role, reason="Correctly finished the quiz."
                    )
                else:
                    await ctx.send(
                        f"Unfortunately, your server doesn't provide a quiz role! "
                        f"Please ask them to do it using `{ctx.prefix}quiz role`."
                    )

                await ctx.send("Congratulations on getting everything correct!")

    @quiz.command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def role(self, ctx, role: discord.Role):
        if (
            role.is_default()
            or role.managed
            or role.position >= ctx.guild.me.top_role.position
        ):
            await ctx.send(
                "Please choose a role that isn't the `everyone` role, "
                "and isn't managed by an integration such as a bot, that I have permission to give."
            )
            return

        await self.bot.config.upsert({"_id": ctx.guild.id, "quiz_role": role.id})
        await ctx.send("Role added as a quiz role.")


def setup(bot):
    bot.add_cog(Quiz(bot))
